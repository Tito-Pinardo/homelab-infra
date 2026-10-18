import crypto from "crypto";
import express from "express";
import fetch from "node-fetch";
import {
  createAdminSession,
  deleteAdminSession,
  deleteExpiredAdminSessions,
  getAdminSession,
} from "./db.js";

const COOKIE_NAME = "bp_admin_session";
const SESSION_TTL_MS = 1000 * 60 * 60 * 12;
const STATE_TTL_MS = 1000 * 60 * 10;

const oauthStates = new Map();

const getAdminIds = () => {
  const ids = process.env.PANEL_ADMIN_DISCORD_IDS || process.env.PANEL_ADMIN_DISCORD_ID;
  if (!ids) return [];
  return ids
    .split(",")
    .map((id) => id.trim())
    .filter(Boolean);
};

const parseCookies = (header) => {
  if (!header) return {};
  return header.split(";").reduce((acc, pair) => {
    const [rawKey, ...rest] = pair.trim().split("=");
    if (!rawKey) return acc;
    acc[rawKey] = decodeURIComponent(rest.join("="));
    return acc;
  }, {});
};

const getSession = (req) => {
  const cookies = parseCookies(req.headers.cookie || "");
  const token = cookies[COOKIE_NAME];
  if (!token) return null;
  deleteExpiredAdminSessions();
  const session = getAdminSession(token);
  if (!session) return null;
  if (session.expiresAt < Date.now()) {
    deleteAdminSession(token);
    return null;
  }
  return session;
};

const setSessionCookie = (res, token) => {
  const isProd = process.env.NODE_ENV === "production";
  res.cookie(COOKIE_NAME, token, {
    httpOnly: true,
    secure: isProd,
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_TTL_MS,
  });
};

const clearSessionCookie = (res) => {
  res.clearCookie(COOKIE_NAME, { path: "/" });
};

const createSession = (user) => {
  const token = crypto.randomBytes(32).toString("hex");
  createAdminSession({
    user,
    expiresAt: Date.now() + SESSION_TTL_MS,
    token,
  });
  return token;
};

const getDiscordConfig = () => ({
  clientId: process.env.DISCORD_CLIENT_ID,
  clientSecret: process.env.DISCORD_CLIENT_SECRET,
  redirectUri: process.env.DISCORD_OAUTH_REDIRECT_URI,
});

const ensureDiscordConfig = (res) => {
  const config = getDiscordConfig();
  if (!config.clientId || !config.clientSecret || !config.redirectUri) {
    res.status(500).json({ error: "Discord OAuth not configured" });
    return null;
  }
  return config;
};

const isAdminUser = (userId) => {
  const adminIds = getAdminIds();
  return adminIds.includes(String(userId));
};

const buildUserPayload = (user) => ({
  id: user.id,
  username: user.username,
  globalName: user.global_name,
  avatar: user.avatar,
});

// Panel interno (puerto de admin, solo 127.0.0.1): Caddy ya ha validado al
// usuario con Authelia y pasa Remote-User. index.js solo rellena
// req.autheliaUser en ese puerto, nunca en el publico (2026-10-09).
const getAutheliaUser = (req) =>
  req.autheliaUser
    ? { id: `authelia:${req.autheliaUser}`, username: req.autheliaUser, global_name: req.autheliaUser, avatar: null }
    : null;

export const requireAdmin = (req, res, next) => {
  const autheliaUser = getAutheliaUser(req);
  if (autheliaUser) {
    req.user = autheliaUser;
    return next();
  }
  if (getAdminIds().length === 0) {
    return res.status(500).json({ error: "PANEL_ADMIN_DISCORD_ID not configured" });
  }
  const session = getSession(req);
  if (!session) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  if (!isAdminUser(session.user.id)) {
    return res.status(403).json({ error: "Forbidden" });
  }
  req.user = session.user;
  return next();
};

const router = express.Router();

router.get("/status", (req, res) => {
  const autheliaUser = getAutheliaUser(req);
  if (autheliaUser) {
    return res.json({ authenticated: true, user: buildUserPayload(autheliaUser) });
  }
  const session = getSession(req);
  if (!session) {
    return res.json({ authenticated: false });
  }
  return res.json({
    authenticated: true,
    user: buildUserPayload(session.user),
  });
});

router.get("/discord", (req, res) => {
  const config = ensureDiscordConfig(res);
  if (!config) return;
  const state = crypto.randomBytes(16).toString("hex");
  oauthStates.set(state, Date.now());
  const params = new URLSearchParams({
    client_id: config.clientId,
    redirect_uri: config.redirectUri,
    response_type: "code",
    scope: "identify",
    state,
  });
  res.redirect(`https://discord.com/api/oauth2/authorize?${params.toString()}`);
});

router.get("/discord/callback", async (req, res) => {
  const config = ensureDiscordConfig(res);
  if (!config) return;
  const { code, state } = req.query;
  if (!code || !state || !oauthStates.has(state)) {
    return res.status(400).send("Invalid OAuth state.");
  }
  const createdAt = oauthStates.get(state);
  oauthStates.delete(state);
  if (Date.now() - createdAt > STATE_TTL_MS) {
    return res.status(400).send("Expired OAuth state.");
  }

  try {
    const tokenParams = new URLSearchParams();
    tokenParams.append("client_id", config.clientId);
    tokenParams.append("client_secret", config.clientSecret);
    tokenParams.append("grant_type", "authorization_code");
    tokenParams.append("code", code);
    tokenParams.append("redirect_uri", config.redirectUri);

    const tokenResponse = await fetch("https://discord.com/api/oauth2/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: tokenParams,
    });

    if (!tokenResponse.ok) {
      const message = await tokenResponse.text();
      return res.status(401).send(message || "Discord token exchange failed.");
    }

    const tokenData = await tokenResponse.json();
    const userResponse = await fetch("https://discord.com/api/users/@me", {
      headers: {
        Authorization: `Bearer ${tokenData.access_token}`,
      },
    });

    if (!userResponse.ok) {
      return res.status(401).send("Failed to fetch Discord user.");
    }

    const user = await userResponse.json();
    if (!isAdminUser(user.id)) {
      return res.status(403).send("No autorizado.");
    }

    const sessionToken = createSession(user);
    setSessionCookie(res, sessionToken);
    return res.redirect("/admin/");
  } catch (error) {
    return res.status(500).send(error.message || "OAuth error.");
  }
});

router.post("/logout", (req, res) => {
  const session = getSession(req);
  if (session) {
    const cookies = parseCookies(req.headers.cookie || "");
    const token = cookies[COOKIE_NAME];
    if (token) deleteAdminSession(token);
  }
  clearSessionCookie(res);
  res.json({ ok: true });
});

export default router;
