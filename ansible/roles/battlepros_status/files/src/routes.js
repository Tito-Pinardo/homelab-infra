import express from "express";
import {
  addTarget,
  createServer,
  deleteServer,
  deleteTarget,
  getServer,
  listServers,
  listTargets,
  updateServer,
} from "./db.js";
import {
  buildAmpQueryInfo,
  getInstanceWithStatus,
  listInstances,
  resolveInstanceId,
} from "./amp.js";
import { getAmpDerivedState, getAmpStateSignals } from "./discord.js";
import { requireAdmin } from "./auth.js";

const router = express.Router();

// ✅ Helper para capturar errores en handlers async (Express 4)
const asyncHandler = (fn) => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next);

const normalizeText = (value) => {
  if (value == null) return null;
  const trimmed = value.toString().trim();
  return trimmed === "" ? null : trimmed;
};

const buildServerPayload = (body, ampInstanceId) => ({
  name: normalizeText(body?.name),
  amp_instance_id: ampInstanceId,
  host: normalizeText(body?.host),
  category: normalizeText(body?.category),
  image_url: normalizeText(body?.image_url),
});

router.use(requireAdmin);

router.get("/servers", (req, res) => {
  const servers = listServers().map((server) => ({
    ...server,
    targets: listTargets(server.id),
  }));
  res.json(servers);
});

router.post(
  "/servers",
  asyncHandler(async (req, res) => {
    const ampInstanceId = await resolveInstanceId(req.body?.amp_instance_id);
    const payload = buildServerPayload(req.body, ampInstanceId);

    if (!payload.name) {
      return res.status(400).json({ error: "name is required" });
    }

    const server = createServer(payload);
    return res.status(201).json(server);
  })
);

router.put(
  "/servers/:id",
  asyncHandler(async (req, res) => {
    const ampInstanceId = await resolveInstanceId(req.body?.amp_instance_id);
    const updated = updateServer(
      Number(req.params.id),
      buildServerPayload(req.body, ampInstanceId)
    );
    if (!updated) {
      return res.status(404).json({ error: "Server not found" });
    }
    return res.json(updated);
  })
);

router.delete("/servers/:id", (req, res) => {
  const ok = deleteServer(Number(req.params.id));
  if (!ok) {
    return res.status(404).json({ error: "Server not found" });
  }
  return res.status(204).send();
});

router.post("/servers/:id/targets", (req, res) => {
  const server = getServer(Number(req.params.id));
  if (!server) {
    return res.status(404).json({ error: "Server not found" });
  }

  const channelId = (req.body?.channelId || "").toString().trim();
  if (!channelId) {
    return res.status(400).json({ error: "channelId is required" });
  }

  const target = addTarget(server.id, channelId);
  return res.status(201).json(target);
});

router.delete("/targets/:id", (req, res) => {
  const ok = deleteTarget(Number(req.params.id));
  if (!ok) {
    return res.status(404).json({ error: "Target not found" });
  }
  return res.status(204).send();
});

// ✅ Envuelto con asyncHandler para que no crashee el proceso
router.post(
  "/servers/:id/test",
  asyncHandler(async (req, res) => {
    const server = getServer(Number(req.params.id));
    if (!server) {
      return res.status(404).json({ error: "Server not found" });
    }

    // AMP (puede fallar, mejor devolver info de error sin tumbar)
    let ampInfo = null;
    try {
      ampInfo = server.amp_instance_id
        ? await getInstanceWithStatus(server.amp_instance_id)
        : null;
    } catch (e) {
      ampInfo = { ok: false, error: e?.message || "AMP error" };
    }

    const queryInfo = buildAmpQueryInfo(ampInfo && ampInfo.ok === false ? null : ampInfo);

    const ampState = getAmpDerivedState(
      ampInfo && ampInfo.ok === false ? null : ampInfo
    );

    return res.json({
      ampInfo,
      queryInfo,
      derivedState: ampState,
      ampSignals: getAmpStateSignals(
        ampInfo && ampInfo.ok === false ? null : ampInfo
      ),
    });
  })
);

// ✅ Envuelto con asyncHandler
router.get(
  "/amp/instances",
  asyncHandler(async (req, res) => {
    const instances = await listInstances();
    res.json(instances);
  })
);

export default router;
