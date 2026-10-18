import fetch from "node-fetch";
import * as otplib from "otplib";

const { authenticator } = otplib;

let ampSession = null;

const baseUrl = () => {
  const raw = process.env.AMP_BASE_URL || "";
  return raw.replace(/\/$/, "");
};

const normalizeSecret = (s) => {
  const cleaned = (s || "")
    .toString()
    .trim()
    .replace(/\s+/g, ""); // quita espacios y saltos de línea (muy típico en K8s/Argo)
  if (!cleaned) return "";
  const padding = (8 - (cleaned.length % 8)) % 8;
  return `${cleaned}${"=".repeat(padding)}`;
};

const buildHeaders = () => {
  if (!ampSession?.token) {
    return {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
  }
  return {
    "Content-Type": "application/json",
    Accept: "application/json",
    Authorization: `Bearer ${ampSession.token}`,
  };
};

const extractSessionToken = (data) => {
  // AMP puede devolver la sesión en distintos sitios según versión/endpoint
  return (
    data?.sessionID ||
    data?.sessionId ||
    data?.sessionToken ||
    data?.token ||
    data?.data?.sessionID ||
    data?.data?.sessionId ||
    data?.data?.sessionToken ||
    data?.data?.token ||
    data?.result?.sessionID ||
    data?.result?.sessionId ||
    data?.result?.sessionToken ||
    data?.result?.token ||
    data?.result?.data?.sessionID ||
    data?.result?.data?.sessionToken ||
    null
  );
};

const extractBearerToken = (response) => {
  const header =
    response?.headers?.get?.("authorization") ||
    response?.headers?.get?.("Authorization");
  if (!header) return null;
  const token = header.replace(/^Bearer\s+/i, "").trim();
  return token || null;
};

const extractInstanceId = (instance) => {
  const id =
    instance?.InstanceID ??
    instance?.InstanceId ??
    instance?.instanceId ??
    instance?.instanceID ??
    instance?.Id ??
    instance?.id ??
    instance?.Guid ??
    instance?.GUID ??
    instance?.guid ??
    null;
  return id ? id.toString() : null;
};

const isAmpErrorPayload = (payload) =>
  payload &&
  typeof payload === "object" &&
  !Array.isArray(payload) &&
  "Title" in payload &&
  "Message" in payload &&
  "StackTrace" in payload;

const normalizeInstanceList = (payload) => {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;

  const candidates = [
    payload?.data,
    payload?.result,
    payload?.instances,
    payload?.Instances,
    payload?.AvailableInstances,
    payload?.data?.instances,
    payload?.data?.Instances,
    payload?.data?.AvailableInstances,
    payload?.data?.result,
    payload?.result?.data,
    payload?.result?.instances,
    payload?.result?.Instances,
    payload?.result?.AvailableInstances,
    payload?.result?.result,
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (Array.isArray(candidate)) return candidate;
    if (Array.isArray(candidate?.Instances)) return candidate.Instances;
    if (Array.isArray(candidate?.instances)) return candidate.instances;
    if (Array.isArray(candidate?.AvailableInstances)) return candidate.AvailableInstances;
    if (Array.isArray(candidate?.result)) return candidate.result;
  }

  return [];
};

export async function ampLogin() {
  const url = baseUrl();
  if (!url) {
    throw new Error("AMP_BASE_URL not configured");
  }

  // Config TOTP típica (Google Authenticator, etc.)
  authenticator.options = {
    digits: 6,
    step: 30,
    algorithm: "sha1",
  };

  const secret = normalizeSecret(process.env.AMP_2FA_SECRET);
  const token = secret ? authenticator.generate(secret) : undefined;

  const loginBody = {
    username: process.env.AMP_USERNAME,
    password: process.env.AMP_PASSWORD,
    rememberMe: true,
  };
  if (token) loginBody.token = token;

  const response = await fetch(`${url}/API/Core/Login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(loginBody),
  });

  // Ojo: AMP puede devolver JSON con error aunque sea 200; igual miramos ok primero
  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`AMP login returned non-JSON: ${response.status} ${text}`);
  }

  if (!response.ok) {
    throw new Error(`AMP login failed: ${response.status} ${text}`);
  }

  if (data?.success === false) {
    throw new Error(`AMP login success=false: ${JSON.stringify(data)}`);
  }

  const sessionToken = extractSessionToken(data) || extractBearerToken(response);

  ampSession = { token: sessionToken, raw: data };

  if (!ampSession.token) {
    throw new Error(
      `AMP login response missing session token. Response: ${JSON.stringify(data)}`
    );
  }

  return ampSession;
}

export async function ampPost(endpoint, body = {}) {
  if (!ampSession?.token) {
    await ampLogin();
  }
  const url = baseUrl();
  const wrapParameters =
    !body || typeof body !== "object" || !("parameters" in body);
  const buildPayload = (wrap) => {
    const payload = wrap ? { parameters: { ...body } } : { ...body };
    if (ampSession?.token) {
      const parameterTarget =
        payload.parameters && typeof payload.parameters === "object"
          ? payload.parameters
          : payload;
      const hasSession =
        "SessionID" in parameterTarget ||
        "sessionId" in parameterTarget ||
        "sessionID" in parameterTarget ||
        "sessionToken" in parameterTarget;
      if (!hasSession) {
        parameterTarget.SessionID = ampSession.token;
      }
      if (!("SessionID" in payload) && !("sessionID" in payload)) {
        payload.SessionID = ampSession.token;
      }
    }
    return payload;
  };

  const sendRequest = async (payload) => {
    const response = await fetch(`${url}${endpoint}`, {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify(payload),
    });
    const text = await response.text();
    return { ok: response.ok, status: response.status, text };
  };

  const parseJson = (result) => {
    if (!result.text) return {};
    try {
      return JSON.parse(result.text);
    } catch {
      throw new Error(
        `AMP request returned non-JSON: ${result.status} ${result.text}`
      );
    }
  };

  let result = await sendRequest(buildPayload(wrapParameters));
  let parsed = parseJson(result);
  if (wrapParameters && (isAmpErrorPayload(parsed) || !result.ok)) {
    result = await sendRequest(buildPayload(false));
    parsed = parseJson(result);
  }
  if (!result.ok) {
    throw new Error(`AMP request failed: ${result.status} ${result.text}`);
  }
  if (isAmpErrorPayload(parsed)) {
    throw new Error(`AMP request failed: ${parsed.Title} ${parsed.Message}`);
  }
  return parsed;
}

export async function getInstance(instanceId) {
  if (!instanceId) return null;
  let resolvedId = instanceId;
  if (/^[0-9a-f]{8}$/i.test(instanceId)) {
    const instances = await listInstances();
    const match = instances.find((instance) =>
      extractInstanceId(instance)?.startsWith(instanceId)
    );
    const matchId = extractInstanceId(match);
    if (matchId) {
      resolvedId = matchId;
    }
  }

  const data = await ampPost("/API/ADSModule/GetInstance", {
    InstanceId: resolvedId,
  });
  return (
    data?.data ??
    data?.instance ??
    data?.result?.data ??
    data?.result?.Instance ??
    data?.result?.instance ??
    data?.result ??
    data
  );
}

const normalizeNumber = (value, nestedKeys = ["current", "Current", "online", "Online"]) => {
  if (value == null) return null;
  if (Array.isArray(value)) return value.length;
  if (typeof value === "object") {
    for (const key of nestedKeys) {
      if (key in value) {
        const nested = value[key];
        if (nested != null) return normalizeNumber(nested, nestedKeys);
      }
    }
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const readFromSources = (sources, keys, nestedKeys) => {
  for (const source of sources) {
    if (!source || typeof source !== "object") continue;
    for (const key of keys) {
      if (!(key in source)) continue;
      const value = normalizeNumber(source[key], nestedKeys);
      if (value != null) return value;
    }
  }
  return null;
};

export const readAmpValue = (ampInfo, keys) => {
  if (!ampInfo) return null;
  const sources = [
    ampInfo,
    ampInfo?.Status,
    ampInfo?.status,
    ampInfo?.InstanceStatus,
    ampInfo?.instanceStatus,
    ampInfo?.ApplicationState,
    ampInfo?.applicationState,
  ].filter(Boolean);
  for (const source of sources) {
    for (const key of keys) {
      if (key in source && source[key] != null) {
        return source[key];
      }
    }
  }
  return null;
};

const buildAmpSources = (ampInfo) => {
  const sources = [
    ampInfo,
    ampInfo?.Metrics,
    ampInfo?.metrics,
    ampInfo?.ApplicationMetrics,
    ampInfo?.applicationMetrics,
    ampInfo?.InstanceMetrics,
    ampInfo?.instanceMetrics,
    ampInfo?.Status,
    ampInfo?.status,
    ampInfo?.ApplicationState,
    ampInfo?.applicationState,
  ].filter(Boolean);

  if (ampInfo?.Players && typeof ampInfo.Players === "object") {
    sources.push(ampInfo.Players);
  }
  if (ampInfo?.players && typeof ampInfo.players === "object") {
    sources.push(ampInfo.players);
  }
  return sources;
};

export function getAmpStats(ampInfo) {
  if (!ampInfo) return { playersOnline: null, playersMax: null, latency: null };
  
  // Obtener jugadores únicamente desde Metrics["Active Users"] de AMP
  const activeUsers = ampInfo?.Metrics?.["Active Users"];
  let playersOnline = null;
  let playersMax = null;
  
  if (activeUsers && typeof activeUsers === "object") {
    playersOnline = normalizeNumber(activeUsers.RawValue);
    playersMax = normalizeNumber(activeUsers.MaxValue);
  }

  return { playersOnline, playersMax, latency: null };
}

export function buildAmpQueryInfo(ampInfo) {
  if (!ampInfo) {
    return { ok: false, reason: "no-amp" };
  }
  const { playersOnline, playersMax, latency } = getAmpStats(ampInfo);
  const appState = Number(ampInfo?.AppState ?? ampInfo?.Status?.AppState ?? ampInfo?.status?.AppState);
  const running = ampInfo?.Running ?? ampInfo?.Status?.Running ?? ampInfo?.status?.Running;
  const state = Number(ampInfo?.State ?? ampInfo?.Status?.State ?? ampInfo?.status?.State);
  const ok = !(running === false || appState === 40 || appState === -1 || state === 0);
  return {
    ok,
    latency: latency ?? null,
    playersOnline: playersOnline ?? null,
    playersMax: playersMax ?? null,
    raw: ampInfo,
    source: "amp",
  };
}

const extractStatusPayload = (payload) =>
  payload?.data ??
  payload?.status ??
  payload?.result?.data ??
  payload?.result?.status ??
  payload?.result ??
  payload ??
  null;

export async function getInstanceStatus(instanceId) {
  if (!instanceId) return null;
  const endpoints = [
    "/API/ADSInstance/GetServerStatus",
    "/API/ADSInstance/GetStatus",
    "/API/ADSInstance/GetInstanceStatus",
  ];

  let lastError = null;
  for (const endpoint of endpoints) {
    try {
      const data = await ampPost(endpoint, {
        InstanceId: instanceId,
        InstanceID: instanceId,
      });
      const status = extractStatusPayload(data);
      if (status && typeof status === "object") {
        return status;
      }
    } catch (error) {
      lastError = error;
    }
  }

  if (lastError) {
    throw lastError;
  }
  return null;
}

export async function getInstanceWithStatus(instanceId) {
  const instance = await getInstance(instanceId);
  if (!instance) return null;
  let status = null;
  try {
    status = await getInstanceStatus(instanceId);
  } catch (error) {
    status = null;
  }

  if (!status || typeof status !== "object") {
    return instance;
  }

  const merged = { ...instance, Status: status };
  for (const [key, value] of Object.entries(status)) {
    if (merged[key] == null) {
      merged[key] = value;
    }
  }
  return merged;
}

export async function listInstances() {
  const data = await ampPost("/API/ADSModule/GetInstances", {});
  const instances = normalizeInstanceList(data);

  if (Array.isArray(instances)) {
    const flattened = instances.flatMap((entry) => {
      if (Array.isArray(entry?.Instances)) return entry.Instances;
      if (Array.isArray(entry?.instances)) return entry.instances;
      if (Array.isArray(entry?.AvailableInstances)) return entry.AvailableInstances;
      return entry;
    });
    const seen = new Set();
    return flattened
      .map((inst) => {
        const id = extractInstanceId(inst);
        if (!id) return null;
        return { ...inst, InstanceID: id };
      })
      .filter(Boolean)
      .filter((inst) => {
        if (seen.has(inst.InstanceID)) return false;
        seen.add(inst.InstanceID);
        return true;
      });
  }

  return [];
}

export function clearAmpSession() {
  ampSession = null;
}

export async function resolveInstanceId(instanceId) {
  const raw = (instanceId || "").toString().trim();
  if (!raw) return null;
  if (/^[0-9a-f]{8}$/i.test(raw)) {
    const instances = await listInstances();
    const match = instances.find((instance) =>
      extractInstanceId(instance)?.startsWith(raw)
    );
    const matchId = extractInstanceId(match);
    if (matchId) {
      return matchId;
    }
  }
  return raw;
}

// Datos de "publicacion" que AMP ya sabe de cada instancia (los mismos que
// su pagina Community /c/<id>): direccion anunciada con puerto, enlace
// steam://connect y caratula oficial. La "Advertised Connection Address" es
// tambien la señal que usa amp_publicar para abrir router y DNS.
const STEAM_CDN = "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps";
// AMP llama "Minecraft" al modulo (no "MinecraftModule").
const MODULE_GAMES = { Minecraft: "Minecraft", MinecraftModule: "Minecraft" };

export const describeAmp = (inst) => {
  if (!inst) return null;
  const advertised = inst.DeploymentArgs?.["Core.AMP.AdvertisedAddress"] || null;
  const endpoint = (inst.ApplicationEndpoints || []).find(
    (e) => e?.Endpoint && !/sftp/i.test(e.DisplayName || "") && !e.Endpoint.startsWith("0.0.0.0")
  );
  const source = inst.DisplayImageSource || "";
  let cover = null;
  if (source.startsWith("steam:")) cover = `${STEAM_CDN}/${source.slice(6)}/header.jpg`;
  else if (source.startsWith("url:")) cover = source.slice(4);
  const game =
    inst.ModuleDisplayName && inst.ModuleDisplayName !== "Generic"
      ? inst.ModuleDisplayName
      : MODULE_GAMES[inst.Module] || null;
  // Los Minecraft entran todos por velocity (25565, el puerto por defecto): su
  // puerto propio no se abre en el router, asi que la direccion va sin puerto
  // aunque en AMP este marcada "Advertised address includes port".
  const isMinecraft = MODULE_GAMES[inst.Module] === "Minecraft";
  // La pagina Community de AMP (/c/<id>) enseña endpoint.Endpoint tal cual: en
  // los Minecraft solo sirve si va sin puerto o con el 25565 de velocity.
  const communityOk = Boolean(advertised) && (!isMinecraft || !/:(?!25565$)\d+$/.test(endpoint?.Endpoint || ""));
  // El proxy (velocity) es el unico Minecraft en el 25565: la entrada comun a
  // todos los mundos, que se eligen por subdominio ([forced-hosts]).
  const proxy = isMinecraft && String(inst.DeploymentArgs?.["MinecraftModule.Minecraft.PortNumber"]) === "25565";
  const steam =
    source.startsWith("steam:") ||
    /steamstatic\.com\/.*\/apps\/\d+\//.test(source) ||
    Boolean(endpoint?.Uri?.startsWith("steam://"));
  return {
    advertised,
    communityOk,
    kind: isMinecraft ? "minecraft" : steam ? "steam" : "other",
    proxy,
    address: advertised
      ? isMinecraft
        ? advertised.replace(/:\d+$/, "")
        : endpoint?.Endpoint || advertised
      : null,
    connect_url: endpoint?.Uri?.startsWith("steam://") ? endpoint.Uri : null,
    cover,
    game,
  };
};
