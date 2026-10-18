import net from "net";
import * as gamedig from "gamedig";

const gamedigQuery = gamedig.query ?? gamedig.default?.query;

const tcpProbe = (host, port, timeoutMs = 5000) =>
  new Promise((resolve) => {
    const start = Date.now();
    const socket = new net.Socket();

    const cleanup = (result) => {
      socket.removeAllListeners();
      socket.destroy();
      resolve(result);
    };

    socket.setTimeout(timeoutMs);
    socket.once("error", () => cleanup({ ok: false, reason: "tcp-error" }));
    socket.once("timeout", () => cleanup({ ok: false, reason: "tcp-timeout" }));
    socket.connect(port, host, () => {
      const latency = Date.now() - start;
      cleanup({ ok: true, latency });
    });
  });

export async function queryGame({ type, host, port, queryPort }) {
  if (!type || type === "none") {
    return { ok: false, reason: "no-query" };
  }

  if (type === "tcp") {
    const result = await tcpProbe(host, port);
    return {
      ok: result.ok,
      latency: result.latency ?? null,
      playersOnline: null,
      playersMax: null,
      raw: result.ok ? { tcp: true } : { reason: result.reason },
    };
  }

  if (!gamedigQuery) {
    return { ok: false, reason: "gamedig-unavailable" };
  }

  try {
    const response = await gamedigQuery({
      type,
      host,
      port,
      queryPort,
      maxAttempts: 2,
      socketTimeout: 5000,
    });

    return {
      ok: true,
      latency: response.ping ?? null,
      playersOnline: response.players?.length ?? null,
      playersMax: response.maxplayers ?? null,
      raw: response,
    };
  } catch (error) {
    return {
      ok: false,
      reason: error?.message || "query-failed",
    };
  }
}
