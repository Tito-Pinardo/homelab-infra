const GUILD_ID = "270202578124406784";
const REFRESH_MS = 20_000;

const $ = (id) => document.getElementById(id);
const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const normCategory = (value) => {
  const text = (value || "Otros").trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
};

const STATES = {
  Online: { cls: "on", label: "Online" },
  Sleeping: { cls: "sleep", label: "Dormido" },
  Offline: { cls: "off", label: "Apagado" },
  Apagado: { cls: "off", label: "Apagado" },
};
const stateOf = (name) => STATES[name] || { cls: "off", label: name || "Sin datos" };

let servers = [];
let live = new Map();
let ampInstances = [];
let editingId = null;
let targetServerId = null;
let cropper = null;

// ---------- utilidades ----------
const toast = (message, type = "info") => {
  const el = document.createElement("div");
  el.className = `toast ${type === "ok" ? "ok" : type === "error" ? "err" : ""}`;
  el.textContent = message;
  $("toasts").append(el);
  setTimeout(() => el.remove(), type === "error" ? 6000 : 3000);
};

const api = async (path, options = {}) => {
  const response = await fetch(`/api${path}`, {
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!response.ok) {
    let message = response.statusText;
    try {
      message = (await response.json()).error || message;
    } catch { /* respuesta sin JSON */ }
    if (response.status === 401) message = "La sesión ha caducado: recarga la página para volver a entrar.";
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
};

const busy = async (button, fn) => {
  button.disabled = true;
  try {
    return await fn();
  } finally {
    button.disabled = false;
  }
};

const confirmDialog = (title, text) =>
  new Promise((resolve) => {
    const dialog = $("confirm-dialog");
    $("confirm-title").textContent = title;
    $("confirm-text").textContent = text;
    const onClick = (event) => {
      const value = event.target.closest("button[value]")?.value;
      if (!value) return;
      dialog.removeEventListener("click", onClick);
      dialog.close();
      resolve(value === "yes");
    };
    dialog.addEventListener("click", onClick);
    dialog.addEventListener("cancel", () => resolve(false), { once: true });
    dialog.showModal();
  });

const instanceById = (id) => ampInstances.find((i) => String(i.InstanceID) === String(id));
const instanceLabel = (i) => `${i.FriendlyName || i.InstanceName}${i.ModuleDisplayName ? ` · ${i.ModuleDisplayName}` : ""}${i.Running ? "" : " (parada)"}`;

// ---------- pintar ----------
const renderStats = () => {
  const on = servers.filter((s) => stateOf(live.get(s.id)?.state).cls !== "off");
  $("s-total").textContent = servers.length;
  $("s-online").textContent = on.length;
  $("s-players").textContent = on.reduce((sum, s) => sum + (live.get(s.id)?.playersOnline || 0), 0);
  $("s-targets").textContent = servers.reduce((sum, s) => sum + (s.targets?.length || 0), 0);
  $("s-amp").textContent = ampInstances.length ? `${ampInstances.filter((i) => i.Running).length}/${ampInstances.length}` : "–";
};

const card = (server) => {
  const status = live.get(server.id);
  const st = stateOf(status?.state);
  const instance = instanceById(server.amp_instance_id);
  const players = status?.playersOnline != null ? `${status.playersOnline}${status.playersMax ? ` / ${status.playersMax}` : ""}` : "–";
  // Sin carátula propia, la que da AMP/Steam (viene ya resuelta en el estado en vivo).
  const cover = server.image_url || status?.image_url;
  const thumb = cover
    ? `<img src="${escapeHtml(cover)}" alt="" loading="lazy" />`
    : escapeHtml(normCategory(server.category));
  const targets = (server.targets || [])
    .map((t) => `
      <span class="target">
        <a href="https://discord.com/channels/${GUILD_ID}/${escapeHtml(t.channel_id)}${t.message_id ? `/${escapeHtml(t.message_id)}` : ""}" target="_blank" rel="noreferrer" title="Abrir el mensaje en Discord">#${escapeHtml(t.channel_id)}</a>
        <button type="button" data-action="delete-target" data-id="${t.id}" data-server="${server.id}" title="Dejar de publicar aquí">✕</button>
      </span>`)
    .join("");
  return `
    <article class="card">
      <div class="card-top">
        <div class="thumb">${thumb}</div>
        <div>
          <div class="card-title">
            <h3>${escapeHtml(server.name)}</h3>
            <span class="pill ${st.cls}"><i></i>${escapeHtml(st.label)}</span>
          </div>
          <div class="meta">
            <span>${escapeHtml(normCategory(server.category))} · <b>${players}</b> jugadores</span>
            <span class="mono">${server.host ? escapeHtml(server.host) : status?.host ? `${escapeHtml(status.host)} <span class="from-amp">de AMP</span>` : "sin dirección"}</span>
            <span>AMP: <b>${instance ? escapeHtml(instanceLabel(instance)) : server.amp_instance_id ? "instancia no encontrada" : "sin enlazar"}</b></span>
          </div>
        </div>
      </div>
      <div class="targets">
        <p class="targets-label">Canales de Discord</p>
        <div class="target-list">${targets || '<span class="no-targets">No se publica en ningún canal</span>'}</div>
      </div>
      <div class="card-actions">
        <button class="btn btn-ghost btn-sm" type="button" data-action="test" data-server="${server.id}">Probar</button>
        <button class="btn btn-ghost btn-sm" type="button" data-action="edit" data-server="${server.id}">Editar</button>
        <button class="btn btn-ghost btn-sm" type="button" data-action="add-target" data-server="${server.id}">+ Canal</button>
        <button class="btn btn-danger btn-sm" type="button" data-action="delete" data-server="${server.id}">Borrar</button>
      </div>
    </article>`;
};

// Lo que AMP publica (tiene "Advertised Connection Address") pero no está
// dado de alta en el bot: sale en la web, pero sin mensaje en Discord.
const renderAuto = () => {
  const auto = [...live.values()].filter((s) => s.auto);
  $("auto-section").hidden = !auto.length;
  $("auto-list").innerHTML = auto
    .map((s) => {
      const st = stateOf(s.state);
      return `
        <div class="auto-item">
          <div class="thumb">${s.image_url ? `<img src="${escapeHtml(s.image_url)}" alt="" loading="lazy" />` : escapeHtml(normCategory(s.category))}</div>
          <div>
            <p class="auto-name">${escapeHtml(s.name)} <span class="pill ${st.cls}"><i></i>${escapeHtml(st.label)}</span></p>
            <p class="muted small">${s.proxy ? "Proxy de Minecraft · entrada general en la web" : escapeHtml(normCategory(s.category))} · <span class="mono">${escapeHtml(s.host || "")}</span></p>
          </div>
          <button class="btn btn-ghost btn-sm" type="button" data-adopt="${escapeHtml(s.id)}">+ Añadir al bot</button>
        </div>`;
    })
    .join("");
};

const renderList = () => {
  renderAuto();
  const q = $("search").value.trim().toLowerCase();
  const list = servers.filter((s) => !q || [s.name, s.category, s.host].some((v) => (v || "").toLowerCase().includes(q)));
  $("server-list").innerHTML = list.length
    ? list.map(card).join("")
    : `<div class="empty">${servers.length ? "Nada coincide con la búsqueda." : "Todavía no hay servidores. Pulsa «Nuevo servidor» para añadir el primero."}</div>`;
  renderStats();
  $("categories").innerHTML = [...new Set(servers.map((s) => normCategory(s.category)))].map((c) => `<option value="${escapeHtml(c)}">`).join("");
};

// ---------- datos ----------
const loadLive = async () => {
  const data = await api("/public/servers");
  live = new Map(data.map((s) => [s.id, s]));
};

const loadAll = async ({ quiet = false } = {}) => {
  try {
    const [list] = await Promise.all([api("/servers"), loadLive()]);
    servers = list;
    renderList();
    $("updated").textContent = `Actualizado a las ${new Date().toLocaleTimeString("es-ES")}`;
  } catch (error) {
    if (!quiet) toast(error.message, "error");
  }
};

const loadAmp = async () => {
  try {
    const data = await api("/amp/instances");
    ampInstances = (Array.isArray(data) ? data : []).sort((a, b) => (a.FriendlyName || "").localeCompare(b.FriendlyName || ""));
  } catch (error) {
    ampInstances = [];
    toast(`No se pudo leer la lista de AMP: ${error.message}`, "error");
  }
};

// ---------- alta / edición ----------
const destroyCropper = () => {
  cropper?.destroy();
  cropper = null;
  $("cropper-wrap").hidden = true;
};

const setCoverPreview = (url) => {
  $("cover-preview").innerHTML = url ? `<img src="${escapeHtml(url)}" alt="" />` : "<span>Sin imagen</span>";
};

const fillAmpSelect = (selected) => {
  const options = ['<option value="">Sin AMP (solo manual)</option>']
    .concat(ampInstances.map((i) => `<option value="${escapeHtml(i.InstanceID)}">${escapeHtml(instanceLabel(i))}</option>`));
  if (selected && !instanceById(selected)) options.push(`<option value="${escapeHtml(selected)}">Instancia desconocida (${escapeHtml(selected)})</option>`);
  $("f-amp-select").innerHTML = options.join("");
  $("f-amp-select").value = selected || "";
};

const openServerDialog = (server = null) => {
  editingId = server?.id ?? null;
  $("server-form").reset();
  destroyCropper();
  $("server-dialog-title").textContent = server ? `Editar «${server.name}»` : "Nuevo servidor";
  $("f-name").value = server?.name || "";
  $("f-category").value = server?.category || "";
  $("f-host").value = server?.host || "";
  $("f-amp").value = server?.amp_instance_id || "";
  $("f-image-url").value = server?.image_url || "";
  fillAmpSelect(server?.amp_instance_id);
  setCoverPreview(server?.image_url);
  $("server-dialog").showModal();
};

const uploadCroppedImage = async () => {
  const canvas = cropper.getCroppedCanvas({ width: 960, height: 540, imageSmoothingQuality: "high" });
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.88));
  const form = new FormData();
  form.append("image", blob, "cover.jpg");
  const response = await fetch("/api/upload", { method: "POST", credentials: "include", body: form });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.error || "No se pudo subir la imagen");
  return result.url;
};

const saveServer = async () => {
  const payload = {
    name: $("f-name").value.trim(),
    amp_instance_id: $("f-amp").value.trim() || null,
    host: $("f-host").value.trim() || null,
    category: $("f-category").value.trim() || null,
    image_url: $("f-image-url").value || null,
  };
  if (!payload.name) {
    $("f-name").focus();
    return;
  }
  if (cropper) payload.image_url = await uploadCroppedImage();
  if (editingId) {
    await api(`/servers/${editingId}`, { method: "PUT", body: JSON.stringify(payload) });
  } else {
    await api("/servers", { method: "POST", body: JSON.stringify(payload) });
  }
  $("server-dialog").close();
  destroyCropper();
  toast(editingId ? "Servidor actualizado" : "Servidor creado", "ok");
  await loadAll();
};

// ---------- prueba ----------
const showTest = (server, result) => {
  const st = stateOf(result.derivedState);
  const amp = result.ampInfo && result.ampInfo.ok !== false ? result.ampInfo : null;
  const q = result.queryInfo || {};
  const rows = [
    ["Instancia", amp ? `${amp.FriendlyName || amp.InstanceName} (${amp.ModuleDisplayName || amp.Module})` : result.ampInfo?.error || "Sin AMP"],
    ["Proceso en AMP", amp ? (amp.Running ? "En marcha" : "Parado") : "–"],
    ["AppState", result.ampSignals?.AppState ?? "–"],
    ["Jugadores", q.playersOnline != null ? `${q.playersOnline}${q.playersMax ? ` / ${q.playersMax}` : ""}` : "–"],
    ["Versión de AMP", amp?.AMPVersion || "–"],
    ["Dirección", server.host || "–"],
  ];
  $("test-title").textContent = `Prueba: ${server.name}`;
  $("test-body").innerHTML = `
    <div class="test-state"><span class="pill ${st.cls}"><i></i>${escapeHtml(st.label)}</span><strong>${escapeHtml(st.label)}</strong></div>
    <dl class="kv">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${escapeHtml(v)}</dd>`).join("")}</dl>
    <details><summary>Respuesta completa</summary><pre>${escapeHtml(JSON.stringify(result, null, 2))}</pre></details>`;
  $("test-dialog").showModal();
};

// ---------- eventos ----------
$("server-list").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const server = servers.find((s) => s.id === Number(button.dataset.server));
  try {
    switch (button.dataset.action) {
      case "edit":
        if (!ampInstances.length) await loadAmp();
        openServerDialog(server);
        break;
      case "add-target":
        targetServerId = server.id;
        $("target-form").reset();
        $("target-server-name").textContent = server.name;
        $("target-dialog").showModal();
        break;
      case "test":
        await busy(button, async () => showTest(server, await api(`/servers/${server.id}/test`, { method: "POST" })));
        break;
      case "delete":
        if (await confirmDialog(`¿Borrar «${server.name}»?`, "Deja de aparecer en la web y el bot deja de actualizar sus mensajes en Discord.")) {
          await api(`/servers/${server.id}`, { method: "DELETE" });
          toast("Servidor borrado", "ok");
          await loadAll();
        }
        break;
      case "delete-target":
        if (await confirmDialog("¿Quitar este canal?", `«${server.name}» dejará de publicarse en ese canal de Discord.`)) {
          await api(`/targets/${button.dataset.id}`, { method: "DELETE" });
          toast("Canal quitado", "ok");
          await loadAll();
        }
        break;
      default:
    }
  } catch (error) {
    toast(error.message, "error");
  }
});

$("auto-list").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-adopt]");
  if (!button) return;
  const entry = live.get(button.dataset.adopt);
  if (!ampInstances.length) await busy(button, loadAmp);
  const prefix = button.dataset.adopt.replace(/^amp-/, "");
  const instance = ampInstances.find((i) => String(i.InstanceID).startsWith(prefix));
  openServerDialog({ name: entry.name, category: entry.category, amp_instance_id: instance?.InstanceID || prefix });
  editingId = null;
  $("server-dialog-title").textContent = `Añadir «${entry.name}» al bot`;
});

$("new-server").addEventListener("click", async (event) => {
  await busy(event.currentTarget, async () => {
    if (!ampInstances.length) await loadAmp();
  });
  openServerDialog();
});

$("refresh").addEventListener("click", (event) => busy(event.currentTarget, async () => {
  await Promise.all([loadAll(), loadAmp()]);
  renderList();
}));
$("search").addEventListener("input", renderList);

$("f-amp-select").addEventListener("change", () => {
  const instance = instanceById($("f-amp-select").value);
  $("f-amp").value = $("f-amp-select").value;
  if (!instance) return;
  if (!$("f-name").value.trim()) $("f-name").value = instance.FriendlyName || instance.InstanceName || "";
  if (!$("f-category").value.trim() && instance.ModuleDisplayName && instance.ModuleDisplayName !== "Generic") {
    $("f-category").value = instance.ModuleDisplayName;
  }
});
$("f-amp").addEventListener("input", () => {
  $("f-amp-select").value = instanceById($("f-amp").value.trim()) ? $("f-amp").value.trim() : "";
});

$("f-image-file").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    toast("La imagen pasa de 5 MB", "error");
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    destroyCropper();
    const img = $("cropper-image");
    img.onload = () => {
      $("cropper-wrap").hidden = false;
      $("cover-preview").innerHTML = "";
      cropper = new Cropper(img, {
        aspectRatio: 16 / 9,
        viewMode: 1,
        dragMode: "move",
        autoCropArea: 1,
        background: false,
        preview: $("cover-preview"),
      });
    };
    img.src = reader.result;
  };
  reader.readAsDataURL(file);
});
$("f-image-clear").addEventListener("click", () => {
  destroyCropper();
  $("f-image-file").value = "";
  $("f-image-url").value = "";
  setCoverPreview(null);
});

$("server-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await busy($("server-save"), saveServer);
  } catch (error) {
    toast(error.message, "error");
  }
});

$("target-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await api(`/servers/${targetServerId}/targets`, {
      method: "POST",
      body: JSON.stringify({ channelId: $("t-channel").value.trim() }),
    });
    $("target-dialog").close();
    toast("Canal añadido: el mensaje aparecerá en la próxima actualización del bot", "ok");
    await loadAll();
  } catch (error) {
    toast(error.message, "error");
  }
});

document.querySelectorAll("[data-close]").forEach((button) =>
  button.addEventListener("click", () => {
    button.closest("dialog").close();
    destroyCropper();
  }));

// ---------- arranque ----------
const init = async () => {
  let auth = { authenticated: false };
  try {
    auth = await api("/auth/status");
  } catch { /* sin sesión */ }
  if (!auth.authenticated) {
    $("locked").hidden = false;
    return;
  }
  $("user-chip").textContent = auth.user?.globalName || auth.user?.username || "Admin";
  $("user-chip").hidden = false;
  $("app").hidden = false;
  await Promise.all([loadAmp(), loadAll()]);
  renderList();
  setInterval(() => {
    if (!document.hidden && !document.querySelector("dialog[open]")) loadAll({ quiet: true });
  }, REFRESH_MS);
};

init();
