const GUILD_ID = "270202578124406784";
const REFRESH_MS = 30_000;

const $ = (id) => document.getElementById(id);
const grid = $("server-sections");
const filters = $("filters");

const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// Las categorías se escriben a mano en el panel ("minecraft", "Minecraft"...):
// se muestran con la primera en mayúscula ("V Rising" se queda igual).
const normCategory = (value) => {
  const text = (value || "Otros").trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
};

const STATES = {
  Online: { cls: "on", label: "Online", order: 0 },
  Sleeping: { cls: "sleep", label: "Dormido", order: 1, note: "En reposo: se despierta al entrar." },
  Offline: { cls: "off", label: "Apagado", order: 2 },
  Apagado: { cls: "off", label: "Apagado", order: 2 },
};
const stateOf = (server) => STATES[server.state] || { cls: "off", label: "Sin datos", order: 3 };

let servers = [];
let activeFilter = "Todos";
// La animación de entrada solo en la primera carga, no en cada refresco.
let intro = true;

const toast = (message) => {
  const el = $("toast");
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove("show"), 2200);
};

const countUp = (el, value) => {
  if (value == null) { el.textContent = "–"; return; }
  const start = Number(el.dataset.value || 0);
  el.dataset.value = value;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || start === value) {
    el.textContent = value;
    return;
  }
  const t0 = performance.now();
  const step = (t) => {
    const k = Math.min(1, (t - t0) / 700);
    el.textContent = Math.round(start + (value - start) * (1 - (1 - k) ** 3));
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
};

const serverCard = (server, index) => {
  const st = stateOf(server);
  const online = server.playersOnline ?? 0;
  const max = server.playersMax;
  const pct = max ? Math.min(100, Math.round((online / max) * 100)) : 0;
  const players = st.cls === "off"
    ? "Nadie jugando"
    : `<b>${online}</b>${max ? ` / ${max}` : ""} jugando`;
  const cover = server.image_url
    ? `<img src="${escapeHtml(server.image_url)}" alt="" loading="lazy" />`
    : `<span class="placeholder">${escapeHtml(normCategory(server.category))}</span>`;
  const addr = server.host
    ? `<div class="addr"><code>${escapeHtml(server.host).replace(/([.:])/g, "<wbr>$1")}</code>
         <button class="copy" type="button" data-copy="${escapeHtml(server.host)}">
           <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-copy" /></svg><span>Copiar</span>
         </button></div>`
    : "";
  // AMP da un enlace steam://connect para los juegos de Steam: abre el juego y entra.
  const connect = server.connect_url && st.cls !== "off"
    ? `<a class="btn btn-connect" href="${escapeHtml(server.connect_url)}">▶ Conectar con Steam</a>`
    : "";
  return `
    <article class="srv is-${st.cls}${intro ? " intro" : ""}" style="${intro ? `animation-delay:${Math.min(index, 5) * 50}ms` : ""}">
      <div class="srv-cover">
        ${cover}
        <span class="pill ${st.cls}"><i></i>${st.label}</span>
        <span class="game-tag">${escapeHtml(normCategory(server.category))}</span>
      </div>
      <div class="srv-body">
        <h3 class="srv-name">${escapeHtml(server.name)}</h3>
        <div class="meter">
          <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-users" /></svg>
          <span>${players}</span>
          ${max && st.cls !== "off" ? `<div class="meter-bar"><span style="width:${pct}%"></span></div>` : ""}
        </div>
        ${st.note ? `<p class="srv-note">${st.note}</p>` : ""}
        ${addr}
        ${connect}
      </div>
    </article>`;
};

// Secciones de la web: Minecraft (con el proxy como cabecera), una propia para
// cada juego con 2 o más servidores, y el resto en "Juegos de Steam" u "Otros".
const buildSections = () => {
  const visible = servers.filter((s) => !s.proxy);
  const proxy = servers.find((s) => s.proxy);
  const sections = [];
  const mc = visible.filter((s) => s.kind === "minecraft");
  if (mc.length || proxy) sections.push({ key: "minecraft", title: "Minecraft", servers: mc, proxy });

  const byGame = new Map();
  visible.filter((s) => s.kind !== "minecraft").forEach((s) => {
    const key = normCategory(s.category).toLowerCase();
    if (!byGame.has(key)) byGame.set(key, { title: normCategory(s.category), servers: [] });
    byGame.get(key).servers.push(s);
  });
  const steam = [];
  const others = [];
  [...byGame].sort(([a], [b]) => a.localeCompare(b)).forEach(([key, game]) => {
    if (game.servers.length >= 2) sections.push({ key, title: game.title, servers: game.servers });
    else (game.servers[0].kind === "steam" ? steam : others).push(game.servers[0]);
  });
  if (steam.length) sections.push({ key: "steam", title: "Juegos de Steam", servers: steam });
  if (others.length) sections.push({ key: "otros", title: "Otros juegos", servers: others });
  return sections;
};

const byState = (a, b) =>
  stateOf(a).order - stateOf(b).order || (b.playersOnline ?? 0) - (a.playersOnline ?? 0) || a.name.localeCompare(b.name);

const proxyBanner = (proxy) => {
  if (!proxy) return "";
  const st = stateOf(proxy);
  return `
    <div class="mc-proxy">
      <div class="mc-proxy-copy">
        <p class="kicker">Java Edition · una sola entrada</p>
        <h4>Todos los mundos por la misma puerta</h4>
        <p class="muted">Entra con la dirección del mundo que quieras y el proxy te lleva directo a él.
          Con la dirección general entras al mundo principal.</p>
      </div>
      <div class="mc-proxy-addr">
        <span class="pill ${st.cls}"><i></i>${st.cls === "on" ? "Proxy en marcha" : st.label}</span>
        <div class="addr"><code>${escapeHtml(proxy.host).replace(/([.:])/g, "<wbr>$1")}</code>
          <button class="copy" type="button" data-copy="${escapeHtml(proxy.host)}">
            <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-copy" /></svg><span>Copiar</span>
          </button></div>
      </div>
    </div>`;
};

let sections = [];

const renderFilters = () => {
  const total = sections.reduce((n, sec) => n + sec.servers.length, 0);
  if (activeFilter !== "Todos" && !sections.some((sec) => sec.key === activeFilter)) activeFilter = "Todos";
  filters.innerHTML = [["Todos", "Todos", total], ...sections.map((sec) => [sec.key, sec.title, sec.servers.length])]
    .map(([key, title, n]) => `<button class="chip" role="tab" type="button" data-filter="${escapeHtml(key)}"
        aria-selected="${key === activeFilter}">${escapeHtml(title)}<span class="count">${n}</span></button>`)
    .join("");
};

const renderServers = () => {
  const shown = sections.filter((sec) => activeFilter === "Todos" || sec.key === activeFilter);
  let index = 0;
  grid.innerHTML = shown.length
    ? shown.map((sec) => `
        <section class="game-section">
          <h3 class="game-title">${escapeHtml(sec.title)}<span>${sec.servers.length}</span></h3>
          ${sec.key === "minecraft" ? proxyBanner(sec.proxy) : ""}
          <div class="server-grid">${[...sec.servers].sort(byState).map((s) => serverCard(s, index++)).join("")}</div>
        </section>`).join("")
    : `<div class="empty">Ahora mismo no hay servidores publicados. Pásate por el Discord y pide el tuyo.</div>`;
};

const loadServers = async () => {
  try {
    const response = await fetch("/api/public/servers", { cache: "no-store" });
    if (!response.ok) throw new Error(response.statusText);
    servers = await response.json();
    sections = buildSections();
    // El proxy de Minecraft no cuenta como servidor (ni sus jugadores, que ya
    // están en los mundos).
    const games = servers.filter((s) => !s.proxy);
    const on = games.filter((s) => stateOf(s).cls !== "off");
    countUp($("stat-online"), on.length);
    $("stat-total").textContent = ` / ${games.length}`;
    countUp($("stat-players"), on.reduce((sum, s) => sum + (s.playersOnline || 0), 0));
    renderFilters();
    renderServers();
    intro = false;
    $("servers-updated").textContent = `Actualizado a las ${new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })}`;
  } catch {
    if (!servers.length) {
      grid.innerHTML = `<div class="empty">No se ha podido cargar el estado de los servidores. Prueba en un momento.</div>`;
    }
  }
};

const STATUS_CLASS = { online: "", idle: "idle", dnd: "dnd" };

const loadDiscord = async () => {
  try {
    const response = await fetch(`https://discord.com/api/guilds/${GUILD_ID}/widget.json`);
    if (!response.ok) throw new Error(response.statusText);
    const data = await response.json();
    countUp($("stat-discord"), data.presence_count ?? 0);
    $("discord-count").textContent = data.presence_count ?? 0;
    if (data.name) {
      $("discord-name").textContent = data.name;
      $("discord-name-card").textContent = data.name;
    }
    const members = data.members || [];
    const shown = members.slice(0, 14);
    $("discord-members").innerHTML = shown.length
      ? shown.map((m) => `
          <li class="member">
            <span class="avatar"><img src="${escapeHtml(m.avatar_url)}" alt="" loading="lazy" width="32" height="32" /><i class="${STATUS_CLASS[m.status] ?? ""}"></i></span>
            <span>
              <span class="member-name">${escapeHtml(m.username)}</span>
              ${m.game?.name ? `<span class="member-game">Jugando a ${escapeHtml(m.game.name)}</span>` : ""}
            </span>
          </li>`).join("") +
        (members.length > shown.length ? `<li class="member-more">y ${members.length - shown.length} más…</li>` : "")
      : `<li class="muted small">Ahora mismo no hay nadie conectado.</li>`;
  } catch {
    $("discord-members").innerHTML = `<li class="muted small">No se ha podido cargar el Discord.</li>`;
  }
};

const copyText = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const area = Object.assign(document.createElement("textarea"), { value: text });
    document.body.append(area);
    area.select();
    const ok = document.execCommand("copy");
    area.remove();
    return ok;
  }
};

grid.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy]");
  if (!button) return;
  if (await copyText(button.dataset.copy)) {
    button.classList.add("done");
    button.querySelector("span").textContent = "¡Copiado!";
    toast(`${button.dataset.copy} copiado. ¡A jugar!`);
    setTimeout(() => {
      button.classList.remove("done");
      button.querySelector("span").textContent = "Copiar";
    }, 1800);
  }
});

filters.addEventListener("click", (event) => {
  const chip = event.target.closest("[data-filter]");
  if (!chip) return;
  activeFilter = chip.dataset.filter;
  renderFilters();
  renderServers();
});

// Normas en español / inglés
const setLang = (lang) => {
  document.querySelectorAll("[data-es]").forEach((el) => {
    el.textContent = el.dataset[lang];
  });
  document.querySelectorAll(".lang button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
};
document.querySelector(".lang").addEventListener("click", (event) => {
  const button = event.target.closest("[data-lang]");
  if (button) setLang(button.dataset.lang);
});
if (location.hash === "#rules") {
  setLang("en");
}

$("year").textContent = new Date().getFullYear();
loadServers();
loadDiscord();
setInterval(() => {
  if (!document.hidden) loadServers();
}, REFRESH_MS);
setInterval(() => {
  if (!document.hidden) loadDiscord();
}, REFRESH_MS * 4);
