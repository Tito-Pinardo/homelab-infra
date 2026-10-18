import { EmbedBuilder } from "discord.js";
import { describeAmp, getAmpStats, readAmpValue } from "./amp.js";

const AMP_TEXT_FIELDS = [
  "State",
  "Status",
  "DisplayState",
  "InstanceState",
  "AppStateLabel",
  "AppStateDescription",
  "StateText",
  "StateMessage",
  "StateDescription",
  "StatusMessage",
  "StatusDescription",
];

const AMP_SLEEP_TOKENS = [
  "sleep",
  "sleeping",
  "suspend",
  "suspended",
  "hibernate",
  "hibernating",
  "idle",
  "standby",
  "paused",
];

const AMP_OFFLINE_TOKENS = [
  "offline",
  "stopped",
  "shutdown",
  "terminated",
  "stopping",
  "error",
  "dead",
];

const AMP_ONLINE_TOKENS = ["running", "online", "started", "ready", "active"];

const normalizeText = (value) => (value ?? "").toString().trim().toLowerCase();

const buildAmpTextSources = (ampInfo) => [
  ampInfo,
  ampInfo?.Status,
  ampInfo?.status,
  ampInfo?.InstanceStatus,
  ampInfo?.instanceStatus,
  ampInfo?.ApplicationState,
  ampInfo?.applicationState,
].filter(Boolean);

const hasStateToken = (ampInfo, tokens) =>
  buildAmpTextSources(ampInfo).some((source) =>
    AMP_TEXT_FIELDS.some((field) => {
      const text = normalizeText(source?.[field]);
      return text && tokens.some((token) => text.includes(token));
    })
  );

export function getAmpDerivedState(ampInfo) {
  if (!ampInfo) return null;

  const appState = Number(readAmpValue(ampInfo, ["AppState", "appState"]));
  // En AMP, el campo AppState varía según versión, pero en tu salida se observa:
  //  - Running=false y AppState=40 (o -1) cuando está apagado
  //  - Running=true y AppState=20 cuando está online (servidor funcionando)
  //  - Running=true y AppState=50 cuando está en "sleep" (instancia activa, servidor dormido)
  const running = readAmpValue(ampInfo, ["Running", "running"]);
  const state = Number(readAmpValue(ampInfo, ["State", "state"]));
  if (appState === 40 || appState === -1) {
    return "Apagado";
  }

  if (appState === 20) {
    return "Online";
  }

  if (appState === 50) {
    return "Sleeping";
  }

  if (running === true) {
    return "Online";
  }

  if (hasStateToken(ampInfo, AMP_SLEEP_TOKENS)) {
    return "Sleeping";
  }

  if (hasStateToken(ampInfo, AMP_OFFLINE_TOKENS)) {
    return "Offline";
  }

  if (hasStateToken(ampInfo, AMP_ONLINE_TOKENS)) {
    return "Online";
  }

  if (running === false || state === 0) {
    return "Apagado";
  }

  return null;
}

export function getAmpStateSignals(ampInfo) {
  if (!ampInfo) return null;

  const textSignals = AMP_TEXT_FIELDS.reduce((acc, field) => {
    const value = ampInfo?.[field];
    if (value != null && value !== "") {
      acc[field] = value;
    }
    return acc;
  }, {});

  return {
    AppState: ampInfo?.AppState ?? null,
    State: ampInfo?.State ?? null,
    Running: ampInfo?.Running ?? null,
    textSignals,
  };
}

function computeState(ampInfo, queryInfo) {
  const ampState = getAmpDerivedState(ampInfo);

  // 1) Si AMP no responde o no hay amp_instance_id, nos basamos solo en query.
  if (!ampInfo) {
    return queryInfo?.ok ? "Online" : "Offline";
  }

  // 2) Si AMP reporta un estado explícito, usamos ese estado primero.
  if (ampState) {
    return ampState;
  }

  // 3) Fallback a query si AMP no trae estado interpretable.
  if (queryInfo?.ok === true) return "Online";
  if (queryInfo?.ok === false) return "Offline";

  return "Online";
}

function stateColor(state) {
  if (state === "Online") return 0x22c55e; // verde
  if (state === "Sleeping") return 0xf59e0b; // ámbar
  if (state === "Apagado") return 0x6b7280; // gris
  return 0xef4444; // rojo
}

const DEFAULT_LAYOUT = ["state", "players", "host"];
const PUBLIC_SITE = "https://www.example.net";
// Pagina Community de AMP (/c/<8 primeros del ID>): conexion directa, copiar
// direccion, steam://connect. Solo si la instancia tiene direccion anunciada;
// sin ella AMP enseña la IP interna o nombres que ya no existen.
const AMP_COMMUNITY_URL = (process.env.AMP_COMMUNITY_URL || "").replace(/\/$/, "");
const serverLink = (server, ampInfo) =>
  AMP_COMMUNITY_URL && server.amp_instance_id && describeAmp(ampInfo)?.communityOk
    ? `${AMP_COMMUNITY_URL}/c/${server.amp_instance_id.slice(0, 8)}`
    : PUBLIC_SITE;
const STATE_LABELS = { Online: "🟢 Online", Sleeping: "🌙 Dormido", Apagado: "⚫ Apagado", Offline: "🔴 Sin respuesta" };

function buildFields(server, state, ampInfo, queryInfo) {
  const ampStats = getAmpStats(ampInfo);
  // Solo usar datos de AMP, sin fallback a query
  const playersOnline = ampStats.playersOnline;
  const playersMax = ampStats.playersMax;

  const playersValue =
    playersOnline != null && playersMax != null
      ? `${playersOnline}/${playersMax}`
      : playersOnline != null
        ? `${playersOnline}`
        : "N/D";

  return {
    state: { name: "Estado", value: STATE_LABELS[state] || state, inline: true },
    players: {
      name: "Jugadores",
      value: playersValue,
      inline: true,
    },
    amp_instance: {
      name: "AMP",
      value:
        ampInfo?.FriendlyName ||
        ampInfo?.InstanceName ||
        server.amp_instance_id ||
        "N/D",
      inline: false,
    },
    host: {
      name: "Dirección",
      value: `\`${server.host || describeAmp(ampInfo)?.address || "N/D"}\``,
      inline: false,
    },
  };
}

/**
 * Firma EXACTA que usa tu index.js:
 * buildEmbed(server, ampInfo, queryInfo)
 */
export function buildEmbed(server, ampInfo, queryInfo) {
  const state = computeState(ampInfo, queryInfo);
  const fields = buildFields(server, state, ampInfo, queryInfo);
  const ordered = DEFAULT_LAYOUT.map((key) => fields[key]).filter(Boolean);

  const embed = new EmbedBuilder()
    .setTitle(server.name)
    .setURL(serverLink(server, ampInfo))
    .setColor(stateColor(state))
    .addFields(ordered)
    .setFooter({ text: "example.net · copia la dirección y entra" })
    .setTimestamp(new Date());
  // Caratula: la subida en el panel o, si no hay, la de Steam/AMP.
  const cover = server.image_url || describeAmp(ampInfo)?.cover;
  if (cover) embed.setThumbnail(cover.startsWith("/") ? `${PUBLIC_SITE}${cover}` : cover);
  return embed;
}

/**
 * Firma EXACTA que usa tu index.js:
 * ensureMessage(channel, target, embed) -> { message, created, usedEmbed }
 */
export async function ensureMessage(channel, target, embed) {
  // target tiene: channel_id, message_id, etc.
  // Intentamos recuperar el mensaje existente si hay message_id
  if (target?.message_id) {
    const existing = await channel.messages.fetch(target.message_id).catch(() => null);
    if (existing) {
      return { message: existing, created: false, usedEmbed: false };
    }
  }

  // Si no existe, creamos uno nuevo ya con el embed (así evitamos message.edit)
  const createdMessage = await channel.send({ embeds: [embed] });
  return { message: createdMessage, created: true, usedEmbed: true };
}
