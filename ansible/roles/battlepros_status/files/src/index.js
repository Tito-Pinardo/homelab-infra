import "dotenv/config";
import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";
import crypto from "crypto";
import multer from "multer";
import { Client, GatewayIntentBits } from "discord.js";
import {
  listServers,
  listTargets,
  updateTargetMessage,
} from "./db.js";
import {
  buildAmpQueryInfo,
  clearAmpSession,
  getInstanceWithStatus,
  describeAmp,
  listInstances,
} from "./amp.js";
import { buildEmbed, ensureMessage } from "./discord.js";
import routes from "./routes.js";
import authRouter, { requireAdmin } from "./auth.js";

import { getAmpStats } from "./amp.js";
import { getAmpDerivedState } from "./discord.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Cache de estado de servidores para API pública
const serverStatusCache = new Map();
// Ultima lista de instancias de AMP (se refresca en cada ciclo del bot)
let ampInstancesCache = [];

const refreshAmpInstances = async () => {
  try {
    ampInstancesCache = await listInstances();
  } catch (error) {
    console.warn("[amp] listInstances failed:", error.message);
  }
};

// Dos puertos (2026-10-09): el publico (PANEL_PORT, lo que sale por Traefik a
// www.example.net) solo sirve la web y /api/public; el de gestion
// (PANEL_ADMIN_PORT, publicado en 127.0.0.1) lleva el panel y la API de admin
// y solo se llega por Caddy + Authelia en battlepros.home.arpa.
const app = express();
app.use(express.json());
const adminApp = express();
adminApp.use(express.json());
// Solo en el puerto de gestion: Caddy pone Remote-User tras pasar Authelia.
adminApp.use((req, res, next) => {
  const user = (req.get("Remote-User") || "").trim();
  if (user) req.autheliaUser = user;
  next();
});

// ============ UPLOADS CONFIG ============
const dataDir = path.resolve(process.env.STATUS_DATA_DIR || "data");
const uploadsDir = path.join(dataDir, "uploads");

// Crear directorio de uploads si no existe
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
  console.log(`[uploads] Created directory: ${uploadsDir}`);
}

// Configurar multer storage
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    const uniqueName = `${crypto.randomBytes(16).toString("hex")}${ext}`;
    cb(null, uniqueName);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB max
  fileFilter: (req, file, cb) => {
    const allowed = [".jpg", ".jpeg", ".png", ".gif", ".webp"];
    const ext = path.extname(file.originalname).toLowerCase();
    if (allowed.includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error("Solo se permiten imágenes (jpg, png, gif, webp)"));
    }
  },
});

// Servir imágenes subidas
app.use("/uploads", express.static(uploadsDir));
adminApp.use("/uploads", express.static(uploadsDir));

// Endpoint para subir imágenes
// Solo admins: sin sesion cualquiera podia subir ficheros servidos en /uploads (2026-10-09)
adminApp.post("/api/upload", requireAdmin, upload.single("image"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No se recibió ninguna imagen" });
  }
  const imageUrl = `/uploads/${req.file.filename}`;
  res.json({ url: imageUrl });
});
// ========================================

const health = (req, res) => {
  res.status(200).send("ok");
};
app.get("/health", health);
adminApp.get("/health", health);

// Endpoint público con datos de jugadores y estado (también lo usa el panel)
const publicServers = async (req, res) => {
  try {
    const registered = listServers();
    const linked = new Set(registered.map((s) => s.amp_instance_id).filter(Boolean));
    const servers = registered.map((server) => {
      const cached = serverStatusCache.get(server.id);
      const amp = describeAmp(ampInstancesCache.find((i) => i.InstanceID === server.amp_instance_id));
      return {
        id: server.id,
        name: server.name,
        // La direccion escrita en el panel manda; si no hay, la de AMP.
        host: server.host || amp?.address || null,
        connect_url: amp?.connect_url || null,
        category: server.category || amp?.game || "Otros",
        image_url: server.image_url || amp?.cover || null,
        kind: amp?.kind || (/minecraft/i.test(server.category || "") ? "minecraft" : "other"),
        proxy: amp?.proxy || false,
        auto: false,
        // Datos de cache (actualizados por runUpdate)
        playersOnline: cached?.playersOnline ?? null,
        playersMax: cached?.playersMax ?? null,
        state: cached?.state ?? "Desconocido",
      };
    });
    // Instancias con direccion anunciada en AMP que no estan dadas de alta en
    // el bot: se publican solas en la web (sin mensaje en Discord).
    for (const inst of ampInstancesCache) {
      const amp = describeAmp(inst);
      if (!amp?.advertised || linked.has(inst.InstanceID)) continue;
      const stats = getAmpStats(inst);
      servers.push({
        id: `amp-${inst.InstanceID.slice(0, 8)}`,
        name: inst.FriendlyName || inst.InstanceName,
        host: amp.address,
        connect_url: amp.connect_url,
        category: amp.game || "Otros",
        image_url: amp.cover,
        kind: amp.kind,
        proxy: amp.proxy,
        auto: true,
        playersOnline: stats.playersOnline,
        playersMax: stats.playersMax,
        state: getAmpDerivedState(inst) || "Desconocido",
      });
    }
    res.json(servers);
  } catch (error) {
    console.error("[api] public servers error:", error);
    res.status(500).json({ error: "Error loading servers" });
  }
};
app.get("/api/public/servers", publicServers);
adminApp.get("/api/public/servers", publicServers);
const webDir = path.join(__dirname, "..", "web");

// Publico: nada de /admin ni de la API de gestion. web/ se monta desde el
// host (infra-tf, roles/battlepros_status/files/web).
app.use(["/admin", "/api"], (req, res) => res.status(404).json({ error: "Not found" }));
app.use(express.static(webDir));

adminApp.use("/api/auth", authRouter);
adminApp.use("/api", routes);
adminApp.get("/", (req, res) => res.redirect("/admin/"));
adminApp.use(express.static(webDir));

const port = Number(process.env.PANEL_PORT || 3000);
app.listen(port, () => {
  console.log(`[public] listening on :${port}`);
});
refreshAmpInstances();
const adminPort = Number(process.env.PANEL_ADMIN_PORT || 3001);
adminApp.listen(adminPort, () => {
  console.log(`[panel] listening on :${adminPort}`);
});

const discordToken = process.env.DISCORD_TOKEN;
const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages],
});

const channelCache = new Map();
const embedCache = new Map();

const stableStringify = (value) =>
  JSON.stringify(value, (key, val) => {
    if (val && typeof val === "object" && !Array.isArray(val)) {
      return Object.keys(val)
        .sort()
        .reduce((acc, nextKey) => {
          acc[nextKey] = val[nextKey];
          return acc;
        }, {});
    }
    return val;
  });

const getChannel = async (channelId) => {
  if (channelCache.has(channelId)) {
    return channelCache.get(channelId);
  }
  const channel = await client.channels.fetch(channelId);
  channelCache.set(channelId, channel);
  return channel;
};

const backupDatabase = () => {
  const dataDir = path.resolve(process.env.STATUS_DATA_DIR || "data");
  const dbPath = process.env.STATUS_DB_PATH
    ? path.resolve(process.env.STATUS_DB_PATH)
    : path.join(dataDir, "status.db");
  if (!fs.existsSync(dbPath)) return;
  const backupName = `status.db.bak-${new Date().toISOString().slice(0, 10)}`;
  const backupPath = path.join(path.dirname(dbPath), backupName);
  if (!fs.existsSync(backupPath)) {
    fs.copyFileSync(dbPath, backupPath);
    console.log(`[db] backup created: ${backupName}`);
  }
};

const fetchAmpInfo = async (server) => {
  if (!server.amp_instance_id) return null;
  for (let attempt = 1; attempt <= 2; attempt += 1) {
    try {
      // ampPost() ya hace login perezoso si no hay sesión cacheada (amp.js).
      // Forzar ampLogin() aquí en cada intento generaba un token "Remember Me"
      // nuevo en AMP por cada ciclo de refresco (cada 30s x servidor), sin que
      // AMP los expire nunca: UserData.json llegó a 26k+ tokens y 10MB.
      return await getInstanceWithStatus(server.amp_instance_id);
    } catch (error) {
      console.warn(`[amp] attempt ${attempt} failed for ${server.name}:`, error.message);
      clearAmpSession();
      if (attempt === 2) throw error;
    }
  }
  return null;
};

const updateTargets = async (server, ampInfo, queryInfo) => {
  const targets = listTargets(server.id);
  const embed = buildEmbed(server, ampInfo, queryInfo);
  const { timestamp: _ts, ...embedDataWithoutTs } = embed.toJSON();
  const embedHash = stableStringify(embedDataWithoutTs);

  for (const target of targets) {
    try {
      const channel = await getChannel(target.channel_id);
      if (!channel?.isTextBased()) {
        console.warn(`[discord] channel ${target.channel_id} not text-based`);
        continue;
      }

      const { message, created, usedEmbed } = await ensureMessage(channel, target, embed);
      if (created || message.id !== target.message_id) {
        updateTargetMessage(target.id, message.id);
      }

      if (usedEmbed) {
        embedCache.set(target.id, embedHash);
        continue;
      }

      if (embedCache.get(target.id) === embedHash) {
        continue;
      }

      await message.edit({ embeds: [embed] });
      embedCache.set(target.id, embedHash);
    } catch (error) {
      console.error(`[discord] failed updating target ${target.id}:`, error.message);
    }
  }
};

const runUpdate = async () => {
  await refreshAmpInstances();
  const servers = listServers();

  for (const server of servers) {
    console.log(`[update] ${server.name} starting`);
    let ampInfo = null;
    try {
      ampInfo = await fetchAmpInfo(server);
    } catch (error) {
      console.warn(`[update] AMP fetch failed for ${server.name}`);
    }

    // Obtener stats y estado de AMP
    const ampStats = getAmpStats(ampInfo);
    const ampState = getAmpDerivedState(ampInfo);

    // Actualizar cache para API pública
    serverStatusCache.set(server.id, {
      playersOnline: ampStats.playersOnline,
      playersMax: ampStats.playersMax,
      state: ampState || "Desconocido",
    });

    // Solo usar AMP para queryInfo
    const queryInfo = buildAmpQueryInfo(ampInfo);

    await updateTargets(server, ampInfo, queryInfo);
    console.log(`[update] ${server.name} done`);
  }
};

const startScheduler = async () => {
  const intervalMs = Number(process.env.STATUS_REFRESH_SECONDS || 30) * 1000;
  while (true) {
    try {
      await runUpdate();
    } catch (err) {
      console.error('[scheduler] runUpdate error:', err.message);
    }
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }
};

client.once("clientReady", () => {
  console.log(`[discord] logged in as ${client.user?.tag}`);
  backupDatabase();
  startScheduler().catch(err => console.error('[scheduler] fatal:', err.message));
});

if (!discordToken) {
  console.warn("DISCORD_TOKEN not configured. Discord bot will not start.");
} else {
  client.login(discordToken);
}

// Error handler (MUY importante para evitar crashes por async errors)
const errorHandler = (err, req, res, next) => {
  console.error("[api] error:", err);
  res.status(err.statusCode || 500).json({ error: err.message || "Internal error" });
};
app.use(errorHandler);
adminApp.use(errorHandler);
