import Database from "better-sqlite3";
import fs from "fs";
import path from "path";

const dataDir = path.resolve(process.env.STATUS_DATA_DIR || "data");
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const dbPath = process.env.STATUS_DB_PATH
  ? path.resolve(process.env.STATUS_DB_PATH)
  : path.join(dataDir, "status.db");
const db = new Database(dbPath);

db.pragma("journal_mode = WAL");

db.exec(`
  CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    amp_instance_id TEXT,
    host TEXT,
    category TEXT,
    image_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS discord_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    channel_id TEXT NOT NULL,
    message_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
  );

  CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS admin_sessions (
    token TEXT PRIMARY KEY,
    user_json TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );
`);

const migrateServersTable = () => {
  // Check if servers_old exists from a partial migration - recover if so
  const tables = db
    .prepare("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('servers', 'servers_old')")
    .all()
    .map((t) => t.name);

  if (tables.includes("servers_old") && !tables.includes("servers")) {
    // Partial migration: servers was renamed to servers_old but new table wasn't created
    // Just rename it back so we can try again
    db.exec("ALTER TABLE servers_old RENAME TO servers;");
  } else if (tables.includes("servers_old") && tables.includes("servers")) {
    // Both exist - drop the old one and keep the new one (migration was mostly complete)
    db.exec("DROP TABLE servers_old;");
  }

  const columns = db.prepare("PRAGMA table_info(servers)").all();
  if (!columns.length) return;

  const existing = columns.map((col) => col.name);
  const desired = [
    "id",
    "name",
    "amp_instance_id",
    "host",
    "category",
    "image_url",
    "created_at",
    "updated_at",
  ];

  const hasMismatch =
    existing.some((column) => !desired.includes(column)) ||
    desired.some((column) => !existing.includes(column));

  if (!hasMismatch) return;

  // Build select columns based on what exists in the old table
  const selectColumns = [
    "id",
    "name",
    "amp_instance_id",
    "host",
    existing.includes("category") ? "category" : "NULL AS category",
    existing.includes("image_url") ? "image_url" : "NULL AS image_url",
    existing.includes("created_at")
      ? "created_at"
      : "CURRENT_TIMESTAMP AS created_at",
    existing.includes("updated_at")
      ? "updated_at"
      : "CURRENT_TIMESTAMP AS updated_at",
  ];

  db.exec("PRAGMA foreign_keys = OFF;");
  db.exec("BEGIN;");
  db.exec("ALTER TABLE servers RENAME TO servers_old;");
  db.exec(`
    CREATE TABLE servers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      amp_instance_id TEXT,
      host TEXT,
      category TEXT,
      image_url TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
  `);
  db.exec(`
    INSERT INTO servers (
      id,
      name,
      amp_instance_id,
      host,
      category,
      image_url,
      created_at,
      updated_at
    )
    SELECT ${selectColumns.join(", ")}
    FROM servers_old;
  `);
  db.exec("DROP TABLE servers_old;");
  db.exec("COMMIT;");
  db.exec("PRAGMA foreign_keys = ON;");
};

migrateServersTable();

const listServersStmt = db.prepare("SELECT * FROM servers ORDER BY category, id DESC");
const getServerStmt = db.prepare("SELECT * FROM servers WHERE id = ?");
const createServerStmt = db.prepare(`
  INSERT INTO servers (name, amp_instance_id, host, category, image_url)
  VALUES (@name, @amp_instance_id, @host, @category, @image_url)
`);
const updateServerStmt = db.prepare(`
  UPDATE servers
  SET name = @name,
      amp_instance_id = @amp_instance_id,
      host = @host,
      category = @category,
      image_url = @image_url,
      updated_at = CURRENT_TIMESTAMP
  WHERE id = @id
`);
const deleteServerStmt = db.prepare("DELETE FROM servers WHERE id = ?");

const listTargetsStmt = db.prepare(
  "SELECT * FROM discord_targets WHERE server_id = ? ORDER BY id DESC"
);
const addTargetStmt = db.prepare(
  "INSERT INTO discord_targets (server_id, channel_id) VALUES (?, ?)"
);
const deleteTargetStmt = db.prepare("DELETE FROM discord_targets WHERE id = ?");
const updateTargetMessageStmt = db.prepare(
  "UPDATE discord_targets SET message_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
);

const getSettingStmt = db.prepare("SELECT value FROM settings WHERE key = ?");
const setSettingStmt = db.prepare(
  "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP"
);
const getAdminSessionStmt = db.prepare(
  "SELECT user_json, expires_at FROM admin_sessions WHERE token = ?"
);
const createAdminSessionStmt = db.prepare(
  "INSERT INTO admin_sessions (token, user_json, expires_at) VALUES (?, ?, ?)"
);
const deleteAdminSessionStmt = db.prepare("DELETE FROM admin_sessions WHERE token = ?");
const deleteExpiredAdminSessionsStmt = db.prepare(
  "DELETE FROM admin_sessions WHERE expires_at < ?"
);

export function listServers() {
  return listServersStmt.all();
}

export function getServer(id) {
  return getServerStmt.get(id);
}

export function createServer(data) {
  const payload = {
    name: data.name,
    amp_instance_id: data.amp_instance_id ?? null,
    host: data.host ?? null,
    category: data.category ?? null,
    image_url: data.image_url ?? null,
  };
  const result = createServerStmt.run(payload);
  return getServer(result.lastInsertRowid);
}

export function updateServer(id, data) {
  const current = getServer(id);
  if (!current) return null;
  const payload = {
    id,
    name: data.name ?? current.name,
    amp_instance_id: data.amp_instance_id ?? current.amp_instance_id,
    host: data.host ?? current.host,
    category: data.category ?? current.category,
    image_url: data.image_url ?? current.image_url,
  };
  updateServerStmt.run(payload);
  return getServer(id);
}

export function deleteServer(id) {
  return deleteServerStmt.run(id).changes > 0;
}

export function listTargets(serverId) {
  return listTargetsStmt.all(serverId);
}

export function addTarget(serverId, channelId) {
  const result = addTargetStmt.run(serverId, channelId);
  return { id: result.lastInsertRowid, server_id: serverId, channel_id: channelId };
}

export function deleteTarget(targetId) {
  return deleteTargetStmt.run(targetId).changes > 0;
}

export function updateTargetMessage(targetId, messageId) {
  updateTargetMessageStmt.run(messageId, targetId);
  return true;
}

export function getSetting(key) {
  const row = getSettingStmt.get(key);
  return row ? row.value : null;
}

export function setSetting(key, value) {
  setSettingStmt.run(key, value);
  return { key, value };
}

export function getAdminSession(token) {
  const row = getAdminSessionStmt.get(token);
  if (!row) return null;
  return {
    token,
    user: JSON.parse(row.user_json),
    expiresAt: row.expires_at,
  };
}

export function createAdminSession({ token, user, expiresAt }) {
  createAdminSessionStmt.run(token, JSON.stringify(user), expiresAt);
  return { token, user, expiresAt };
}

export function deleteAdminSession(token) {
  return deleteAdminSessionStmt.run(token).changes > 0;
}

export function deleteExpiredAdminSessions(now = Date.now()) {
  return deleteExpiredAdminSessionsStmt.run(now).changes;
}

export default db;
