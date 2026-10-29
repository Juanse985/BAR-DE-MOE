const API = "/api",
  SESSION_KEY = "barmoe_access_token",
  USER_KEY = "barmoe_user";
const MENU = {
  ADMINISTRADOR: [
    "sedes",
    "mesas",
    "tipos-producto",
    "proveedores",
    "productos",
    "usuarios",
    "auditoria",
  ],
  MESERO: ["mesas", "pedidos"],
  CAJERO: ["pedidos", "facturacion", "consulta-facturas", "reporte-ventas"],
};
const LABELS = {
  sedes: "Sedes",
  mesas: "Mesas",
  "tipos-producto": "Tipos de producto",
  proveedores: "Proveedores",
  productos: "Productos",
  usuarios: "Usuarios",
  auditoria: "Auditoria",
  pedidos: "Pedidos",
  facturacion: "Facturacion",
  "consulta-facturas": "Consulta de facturas",
  "reporte-ventas": "Reporte de ventas",
};
const RESOURCES = {
  sedes: {
    title: "Sedes",
    endpoint: "sedes",
    fields: [
      { key: "nombre", label: "Nombre", required: true },
      { key: "direccion", label: "Direccion" },
      { key: "telefono", label: "Telefono" },
    ],
    active: "activa",
  },
  mesas: {
    title: "Mesas",
    endpoint: "mesas",
    fields: [
      { key: "sede_id", label: "Sede", ref: "sedes", required: true, fixed: true },
      { key: "numero", label: "Numero", type: "number", required: true, fixed: true },
      { key: "capacidad", label: "Capacidad", type: "number", required: true },
    ],
    active: "activa",
  },
  "tipos-producto": {
    title: "Tipos de producto",
    endpoint: "tipos-producto",
    fields: [
      { key: "nombre", label: "Nombre", required: true },
      { key: "descripcion", label: "Descripcion" },
    ],
    active: "activo",
  },
  proveedores: {
    title: "Proveedores",
    endpoint: "proveedores",
    fields: [
      { key: "nit", label: "NIT", required: true, fixed: true },
      { key: "nombre", label: "Nombre", required: true },
      { key: "contacto", label: "Contacto" },
      { key: "telefono", label: "Telefono" },
    ],
    active: "activo",
  },
  productos: {
    title: "Productos",
    endpoint: "productos",
    fields: [
      { key: "codigo", label: "Codigo", required: true, fixed: true },
      { key: "nombre", label: "Nombre", required: true },
      { key: "sede_id", label: "Sede", ref: "sedes", required: true, fixed: true },
      { key: "tipo_producto_id", label: "Tipo", ref: "tipos", required: true },
      { key: "proveedor_id", label: "Proveedor", ref: "proveedores", required: true },
      {
        key: "valor_compra",
        label: "Valor compra",
        type: "number",
        required: true,
      },
      {
        key: "valor_venta",
        label: "Valor venta",
        type: "number",
        required: true,
      },
    ],
    active: "activo",
  },
};
let state = {
  user: readJson(USER_KEY),
  token: sessionStorage.getItem(SESSION_KEY),
  route: "inicio",
  items: [],
  filter: "",
  sedeFilter: "",
  tipoFilter: "",
  cat: { sedes: [], tipos: [], proveedores: [] },
  idleTimer: null,
  lastActivityAt: 0,
  // HU-007: filtros y página del listado de usuarios (se piden al servidor).
  userQuery: { sede_id: "", perfil: "", pagina: 1 },
  // HU-008: filtros y página de la consulta de auditoría.
  audit: { modulo: "auth", desde: "", hasta: "", usuario: "", sede_id: "", pagina: 1 },
  lastTotal: 0,
};
const TAMANO_PAGINA = 20;
// HU-003, HU-004 y HU-006: motivo que se muestra en el login cuando el
// servidor cierra la sesión.
const MOTIVOS_CIERRE = {
  SESION_EXPIRADA: () =>
    `Se cerro la sesion por ${Math.round(inactivityLimit() / 60000)} minutos de inactividad.`,
  SESION_CERRADA: () => "Tu sesion fue cerrada. Ingresa nuevamente.",
  USUARIO_INACTIVO: () => "Tu usuario esta inactivo. Contacta al administrador.",
};
function readJson(key) {
  try {
    return JSON.parse(sessionStorage.getItem(key));
  } catch {
    return null;
  }
}
function esc(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
      })[c],
  );
}
function headers(json = false) {
  return {
    Authorization: `Bearer ${state.token}`,
    ...(json ? { "Content-Type": "application/json" } : {}),
  };
}
function message(error) {
  return (
    error?.error?.mensaje ||
    error?.detail ||
    "No fue posible completar la operacion."
  );
}
// Sedes, tipos y proveedores: se eligen de una lista y la tabla muestra el
// nombre, no el número. Así nadie tiene que escribir un id a mano.
async function loadCatalogs() {
  const [sedes, tipos, proveedores] = await Promise.all([
    request("/parametrizacion/sedes?solo_activas=false"),
    request("/parametrizacion/tipos-producto"),
    request("/parametrizacion/proveedores"),
  ]);
  state.cat = { sedes, tipos, proveedores };
}
function refName(ref, id) {
  if (id === null || id === undefined || id === "") return "";
  const found = (state.cat[ref] || []).find((item) => item.id === Number(id));
  return found ? found.nombre : `#${id}`;
}
function refOptions(ref, selected = "", placeholder = "Selecciona una opcion") {
  const activo = (item) => item.activa !== false && item.activo !== false;
  const items = (state.cat[ref] || []).filter(
    (item) => activo(item) || item.id === Number(selected),
  );
  return (
    `<option value="">${esc(placeholder)}</option>` +
    items
      .map(
        (item) =>
          `<option value="${item.id}" ${item.id === Number(selected) ? "selected" : ""}>${esc(item.nombre)}</option>`,
      )
      .join("")
  );
}
function cellValue(field, item) {
  return field.ref ? refName(field.ref, item[field.key]) : item[field.key];
}
async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
      ...options,
      headers: {
        ...headers(Boolean(options.body)),
        ...(options.headers || {}),
      },
    }),
    data = await response.json().catch(() => ({})),
    code = data?.error?.codigo;
  if (
    [401, 403].includes(response.status) &&
    [
      "NO_AUTENTICADO",
      "SESION_CERRADA",
      "SESION_EXPIRADA",
      "TOKEN_INVALIDO",
      "USUARIO_INACTIVO",
    ].includes(code)
  ) {
    // Si otra petición en paralelo ya llevó al login, no se repinta.
    if (!state.token) throw Error("sesion");
    // HU-004 criterio 4: se vuelve al login indicando el motivo del cierre.
    const motivo = MOTIVOS_CIERRE[code]?.() || "La sesion expiro. Ingresa nuevamente.";
    clearSession();
    renderLogin(motivo);
    throw Error("sesion");
  }
  if (!response.ok) throw Error(message(data));
  state.lastTotal = Number(response.headers.get("X-Total-Count") || 0);
  return data;
}
function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(USER_KEY);
  state = { ...state, token: null, user: null };
  clearTimeout(state.idleTimer);
  document.getElementById("modal")?.remove();
}
function esAdmin() {
  return state.user?.perfil === "ADMINISTRADOR";
}
function allowed(route) {
  return state.user && (MENU[state.user.perfil] || []).includes(route);
}
function inactivityLimit() {
  return (state.user?.inactividad_segundos || 180) * 1000;
}
function closeInactiveSession() {
  const inactiveFor = Date.now() - state.lastActivityAt;
  const remaining = inactivityLimit() - inactiveFor;

  if (remaining > 0) {
    state.idleTimer = setTimeout(closeInactiveSession, remaining);
    return;
  }

  const motivo = MOTIVOS_CIERRE.SESION_EXPIRADA();
  clearSession();
  renderLogin(motivo);
}
function resetInactivityTimer() {
  if (!state.token) return;

  state.lastActivityAt = Date.now();
  clearTimeout(state.idleTimer);
  state.idleTimer = setTimeout(closeInactiveSession, inactivityLimit());
}
function handlePointerMove() {
  if (state.token && Date.now() - state.lastActivityAt > 1000) {
    resetInactivityTimer();
  }
}
function idle() {
  state.lastActivityAt = Date.now();
  clearTimeout(state.idleTimer);
  state.idleTimer = setTimeout(closeInactiveSession, inactivityLimit());
}
document.addEventListener("click", resetInactivityTimer);
document.addEventListener("keydown", resetInactivityTimer);
document.addEventListener("pointerdown", resetInactivityTimer);
document.addEventListener("pointermove", handlePointerMove);
document.addEventListener("touchstart", resetInactivityTimer, {
  passive: true,
});
document.addEventListener("wheel", resetInactivityTimer, { passive: true });
function renderLogin(note = "") {
  document.getElementById("app").innerHTML =
    `<main class="login-shell"><section class="container"><div class="brand"><span class="brand-mark">M</span><span>BAR DE MOE</span></div><h1 class="heading">Bienvenido de nuevo</h1><p class="login-kicker">Operacion multisede</p><p class="subtle">Ingresa con tus credenciales para continuar.</p>${note ? `<p class="error" role="alert">${esc(note)}</p>` : ""}<form class="form" id="login-form"><label>Usuario<input class="input" name="usuario" autocomplete="username" placeholder="Tu usuario" required></label><label>Contraseña<input class="input" name="password" type="password" autocomplete="current-password" placeholder="Tu contraseña" required></label><button class="login-button" id="login-submit" disabled>Ingresar</button></form><p class="agreement">Acceso seguro para el equipo de Bar de Moe</p></section></main>`;
  const form = document.getElementById("login-form"),
    submit = document.getElementById("login-submit");
  const habilitar = () => {
    submit.disabled = ![...form.elements]
      .slice(0, 2)
      .every((field) => field.value.trim());
  };
  form.addEventListener("input", habilitar);
  form.addEventListener("change", habilitar);
  form.addEventListener("submit", login);
}
async function login(event) {
  event.preventDefault();
  const form = new FormData(event.target),
    submit = document.getElementById("login-submit");
  submit.disabled = true;
  submit.textContent = "Ingresando...";
  try {
    const response = await fetch(`${API}/auth/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          usuario: form.get("usuario"),
          password: form.get("password"),
        }),
      }),
      data = await response.json();
    if (!response.ok) throw Error(message(data));
    state.token = data.access_token;
    state.user = {
      ...data.usuario,
      inactividad_segundos: data.inactividad_segundos,
    };
    sessionStorage.setItem(SESSION_KEY, state.token);
    sessionStorage.setItem(USER_KEY, JSON.stringify(state.user));
    idle();
    data.usuario.debe_cambiar_password ? renderPasswordChange() : renderShell();
  } catch (error) {
    renderLogin(error.message);
  }
}
// HU-005: cambio de la propia contraseña. Es obligatorio después de un
// restablecimiento (HU-006) y voluntario desde "Cambiar mi contraseña".
function renderPasswordChange(note = "", voluntario = false) {
  const titulo = voluntario ? "Cambiar mi contraseña" : "Actualiza tu contraseña",
    kicker = voluntario ? "Mi cuenta" : "Cambio obligatorio",
    texto = voluntario
      ? "Escribe tu contraseña actual y la nueva."
      : "Por seguridad, debes crear una nueva contraseña antes de continuar.";
  document.getElementById("app").innerHTML =
    `<main class="login-shell"><section class="container"><div class="brand"><span class="brand-mark">M</span><span>BAR DE MOE</span></div><h1 class="heading">${titulo}</h1><p class="login-kicker">${kicker}</p><p class="subtle">${texto}</p>${note ? `<p class="error" role="alert">${esc(note)}</p>` : ""}<form class="form" id="password-form"><label>Contraseña actual<input class="input" name="actual" type="password" autocomplete="current-password" placeholder="Contraseña actual" required></label><label>Contraseña nueva<input class="input" name="nueva" type="password" autocomplete="new-password" placeholder="Contraseña nueva" minlength="8" maxlength="72" required></label><label>Confirmar contraseña nueva<input class="input" name="confirmar" type="password" autocomplete="new-password" placeholder="Repite la contraseña nueva" minlength="8" maxlength="72" required></label><p class="subtle">Minimo 8 caracteres, con al menos una mayuscula, una minuscula y un numero. La contraseña se guarda cifrada; no se puede repetir la anterior.</p><button class="login-button">Guardar</button>${voluntario ? '<button type="button" class="ghost" id="cancel-password">Cancelar</button>' : ""}</form></section></main>`;
  document
    .getElementById("cancel-password")
    ?.addEventListener("click", () => renderShell());
  document
    .getElementById("password-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.target);
      if (form.get("nueva") !== form.get("confirmar")) {
        renderPasswordChange("La confirmacion no coincide con la contraseña nueva.", voluntario);
        return;
      }
      try {
        await request("/auth/auth/cambiar-password", {
          method: "POST",
          body: JSON.stringify({
            password_actual: form.get("actual"),
            password_nueva: form.get("nueva"),
          }),
        });
        state.user.debe_cambiar_password = false;
        sessionStorage.setItem(USER_KEY, JSON.stringify(state.user));
        renderShell();
      } catch (error) {
        // Si la sesión se cerró, request() ya llevó al login con el motivo.
        if (state.token) renderPasswordChange(error.message, voluntario);
      }
    });
}
function renderShell(route = state.route) {
  state.route = route === "inicio" || allowed(route) ? route : "inicio";
  const links = (MENU[state.user.perfil] || [])
    .map(
      (item) =>
        `<button class="${item === state.route ? "active" : ""}" data-route="${item}">${LABELS[item]}</button>`,
    )
    .join("");
  document.getElementById("app").innerHTML =
    `<div class="shell"><aside class="sidebar"><div class="brand"><span class="brand-mark">M</span><span>BAR DE MOE</span></div><nav class="nav" aria-label="Menu principal">${links}</nav><div class="user-mini"><strong>${esc(state.user.nombre)}</strong><br>${esc(state.user.perfil)}<br><button class="ghost" id="change-password" style="margin-top:12px;background:transparent;color:white;border-color:rgba(255,255,255,.45)">Cambiar mi contraseña</button><br><button class="ghost" id="logout" style="margin-top:8px;color:white;border-color:rgba(255,255,255,.35)">Cerrar sesion</button></div></aside><main class="content"><div class="workspace-frame" id="view"></div></main></div>`;
  document
    .querySelectorAll("[data-route]")
    .forEach((button) =>
      button.addEventListener("click", () => renderShell(button.dataset.route)),
    );
  document.getElementById("logout").addEventListener("click", logout);
  document
    .getElementById("change-password")
    .addEventListener("click", () => renderPasswordChange("", true));
  renderView();
}
async function logout() {
  try {
    await request("/auth/auth/logout", { method: "POST" });
  } catch {}
  clearSession();
  renderLogin("Sesion cerrada.");
}
function renderView() {
  if (state.route === "inicio") return home();
  if (state.route === "usuarios") return users();
  if (state.route === "auditoria") return auditoria();
  if (RESOURCES[state.route]) return resource(state.route);
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">${LABELS[state.route]}</p><h1>Modulo en preparacion</h1><p class="subtle">Tu perfil tiene acceso a esta opcion. El servicio funcional se incorporara en el siguiente sprint.</p></div></div><section class="panel"><h2>Acceso autorizado</h2><p class="subtle">La ruta esta protegida por perfil y tu sesion permanece activa.</p></section>`;
}
async function users() {
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">Seguridad</p><h1>Usuarios</h1><p class="subtle">Crea cuentas para tu equipo, asigna un perfil y entrega una contraseña inicial.</p></div><div class="topbar-actions"><button class="primary" id="new-user">+ Nuevo usuario</button></div></div><section class="panel"><div class="toolbar"><input id="user-search" placeholder="Buscar por nombre o usuario" aria-label="Buscar usuarios"><select id="user-sede" aria-label="Filtrar por sede"></select><select id="user-perfil" aria-label="Filtrar por perfil"><option value="">Todos los perfiles</option><option value="ADMINISTRADOR">Administrador</option><option value="CAJERO">Cajero</option><option value="MESERO">Mesero</option></select><button class="ghost" id="refresh-users">Actualizar</button></div><div id="users-table"></div><div class="toolbar" id="users-pager"></div></section>`;
  // HU-007 criterio 4: filtro por sede y perfil en el servidor, paginado.
  document.getElementById("user-perfil").value = state.userQuery.perfil;
  ["sede", "perfil"].forEach((campo) =>
    document.getElementById(`user-${campo}`).addEventListener("change", (event) => {
      state.userQuery[campo === "sede" ? "sede_id" : "perfil"] = event.target.value;
      state.userQuery.pagina = 1;
      loadUsers();
    }),
  );
  document
    .getElementById("new-user")
    .addEventListener("click", () => userForm());
  document
    .getElementById("refresh-users")
    .addEventListener("click", () => loadUsers());
  document.getElementById("user-search").addEventListener("input", (event) => {
    state.filter = event.target.value.toLowerCase();
    drawUsers();
  });
  await loadUsers();
}
async function loadUsers() {
  try {
    await loadCatalogs();
    const sede = document.getElementById("user-sede");
    if (sede) {
      sede.innerHTML = refOptions("sedes", state.userQuery.sede_id, "Todas las sedes");
      sede.value = state.userQuery.sede_id;
    }
    const q = state.userQuery,
      params = new URLSearchParams({ pagina: q.pagina, tamano: TAMANO_PAGINA });
    if (q.sede_id) params.set("sede_id", q.sede_id);
    if (q.perfil) params.set("perfil", q.perfil);
    state.users = await request(`/auth/usuarios?${params}`);
    state.usersTotal = state.lastTotal;
    state.error = "";
    drawUsers();
  } catch (error) {
    if (state.token) {
      state.error = error.message;
      drawUsers();
    }
  }
}
// Botones Anterior / Siguiente para un listado paginado por el servidor.
function drawPager(id, pagina, total, irA) {
  const el = document.getElementById(id);
  if (!el) return;
  const paginas = Math.max(1, Math.ceil(total / TAMANO_PAGINA));
  el.innerHTML = `<button class="ghost" data-pag="-1" ${pagina <= 1 ? "disabled" : ""}>Anterior</button><span class="subtle">Pagina ${pagina} de ${paginas} · ${total} registros</span><button class="ghost" data-pag="1" ${pagina >= paginas ? "disabled" : ""}>Siguiente</button>`;
  el.querySelectorAll("[data-pag]").forEach((button) =>
    button.addEventListener("click", () => irA(pagina + Number(button.dataset.pag))),
  );
}
function drawUsers() {
  if (!document.getElementById("users-table")) return;
  const usersList = (state.users || []).filter((item) =>
    JSON.stringify(item).toLowerCase().includes(state.filter),
  );
  document.getElementById("users-table").innerHTML = state.error
    ? `<p class="error">${esc(state.error)}</p>`
    : usersList.length
      ? `<div class="table-wrap"><table><thead><tr><th>Nombre</th><th>Usuario</th><th>Perfil</th><th>Sede</th><th>Estado</th><th>Acceso</th><th>Acciones</th></tr></thead><tbody>${usersList.map((item) => `<tr><td>${esc(item.nombre)}</td><td>${esc(item.usuario)}</td><td><span class="role-badge">${esc(item.perfil)}</span></td><td>${item.sede_id ? esc(refName("sedes", item.sede_id)) : "Todas"}</td><td><span class="badge ${item.estado === "ACTIVO" ? "active" : "inactive"}">${esc(item.estado)}</span></td><td>${item.bloqueado ? '<span class="badge inactive">Bloqueado</span>' : item.debe_cambiar_password ? "Cambio pendiente" : "Listo"}</td><td><div class="user-actions">${item.bloqueado ? `<button class="ghost unlock-user" data-id="${item.id}">Desbloquear</button>` : ""}<button class="ghost edit-user" data-id="${item.id}">Editar</button><button class="ghost reset-user" data-id="${item.id}">Restablecer clave</button><button class="ghost toggle-user ${item.estado === "INACTIVO" ? "activate" : "deactivate"}" data-id="${item.id}" data-state="${item.estado}">${item.estado === "INACTIVO" ? "Activar" : "Desactivar"}</button></div></td></tr>`).join("")}</tbody></table></div>`
      : `<div class="empty">No hay usuarios para mostrar.</div>`;
  drawPager("users-pager", state.userQuery.pagina, state.usersTotal || 0, (pagina) => {
    state.userQuery.pagina = pagina;
    loadUsers();
  });
  document
    .querySelectorAll(".edit-user")
    .forEach((button) =>
      button.addEventListener("click", () =>
        editUserForm(state.users.find((u) => u.id === Number(button.dataset.id))),
      ),
    );
  document
    .querySelectorAll(".reset-user")
    .forEach((button) =>
      button.addEventListener("click", () =>
        resetUserPassword(Number(button.dataset.id)),
      ),
    );
  document
    .querySelectorAll(".unlock-user")
    .forEach((button) =>
      button.addEventListener("click", () =>
        unlockUser(Number(button.dataset.id)),
      ),
    );
  document
    .querySelectorAll(".toggle-user")
    .forEach((button) =>
      button.addEventListener("click", () =>
        toggleUserStatus(Number(button.dataset.id), button.dataset.state),
      ),
    );
}
function userForm() {
  document.body.insertAdjacentHTML(
    "beforeend",
    `<div class="modal-backdrop" id="modal"><section class="modal"><div class="topbar"><div><p class="eyebrow">Administracion</p><h2>Crear usuario</h2></div><button class="ghost" id="close-modal">Cerrar</button></div><p class="subtle">La persona recibira estas credenciales y debera cambiar la contraseña al ingresar.</p><form id="user-form"><div class="form-grid"><label>Cedula<input name="cedula" minlength="5" maxlength="20" required></label><label>Nombre completo<input name="nombre" minlength="3" maxlength="120" required></label><label>Usuario<input name="usuario" minlength="4" maxlength="60" autocomplete="off" required></label><label>Contraseña inicial<input name="password" type="password" minlength="8" maxlength="72" autocomplete="new-password" required></label><label>Perfil<select name="perfil" required><option value="CAJERO">Cajero</option><option value="MESERO">Mesero</option><option value="ADMINISTRADOR">Administrador</option></select></label><label>Sede<select name="sede_id">${refOptions("sedes", "", "Todas (solo administrador)")}</select></label></div><p class="subtle">El cajero y el mesero solo ven la informacion de su sede.</p><div id="form-error"></div><div class="modal-actions"><button type="button" class="ghost" id="cancel-modal">Cancelar</button><button class="primary">Crear usuario</button></div></form></section></div>`,
  );
  const close = () => document.getElementById("modal")?.remove();
  document.getElementById("close-modal").addEventListener("click", close);
  document.getElementById("cancel-modal").addEventListener("click", close);
  document
    .getElementById("user-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.target));
      if (values.sede_id === "") values.sede_id = null;
      else values.sede_id = Number(values.sede_id);
      if (values.perfil !== "ADMINISTRADOR" && values.sede_id === null) {
        document.getElementById("form-error").innerHTML =
          '<p class="error">El cajero y el mesero deben tener una sede.</p>';
        return;
      }
      try {
        await request("/auth/usuarios", {
          method: "POST",
          body: JSON.stringify(values),
        });
        close();
        state.filter = "";
        await loadUsers();
      } catch (error) {
        const destino = document.getElementById("form-error");
        if (destino) destino.innerHTML = `<p class="error">${esc(error.message)}</p>`;
      }
    });
}
// HU-007: modificar nombre, perfil y sede. Cédula y usuario no se cambian.
function editUserForm(item) {
  if (!item) return;
  const opcion = (valor, texto) =>
    `<option value="${valor}" ${item.perfil === valor ? "selected" : ""}>${texto}</option>`;
  document.body.insertAdjacentHTML(
    "beforeend",
    `<div class="modal-backdrop" id="modal"><section class="modal"><div class="topbar"><div><p class="eyebrow">Administracion</p><h2>Editar usuario</h2></div><button class="ghost" id="close-modal">Cerrar</button></div><form id="edit-user-form"><div class="form-grid"><label>Cedula<input value="${esc(item.cedula)}" disabled></label><label>Usuario<input value="${esc(item.usuario)}" disabled></label><label>Nombre completo<input name="nombre" minlength="3" maxlength="120" value="${esc(item.nombre)}" required></label><label>Perfil<select name="perfil" required>${opcion("CAJERO", "Cajero")}${opcion("MESERO", "Mesero")}${opcion("ADMINISTRADOR", "Administrador")}</select></label><label>Sede<select name="sede_id">${refOptions("sedes", item.sede_id ?? "", "Todas (solo administrador)")}</select></label></div><p class="subtle">Los campos en gris no se pueden cambiar. Para activar o inactivar usa los botones del listado.</p><div id="form-error"></div><div class="modal-actions"><button type="button" class="ghost" id="cancel-modal">Cancelar</button><button class="primary">Guardar cambios</button></div></form></section></div>`,
  );
  const close = () => document.getElementById("modal")?.remove();
  document.getElementById("close-modal").addEventListener("click", close);
  document.getElementById("cancel-modal").addEventListener("click", close);
  document
    .getElementById("edit-user-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.target));
      values.sede_id = values.sede_id === "" ? null : Number(values.sede_id);
      if (values.perfil !== "ADMINISTRADOR" && values.sede_id === null) {
        document.getElementById("form-error").innerHTML =
          '<p class="error">El cajero y el mesero deben tener una sede.</p>';
        return;
      }
      try {
        await request(`/auth/usuarios/${item.id}`, {
          method: "PATCH",
          body: JSON.stringify(values),
        });
        close();
        await loadUsers();
      } catch (error) {
        const destino = document.getElementById("form-error");
        if (destino) destino.innerHTML = `<p class="error">${esc(error.message)}</p>`;
      }
    });
}
async function resetUserPassword(userId) {
  const password = window.prompt(
    "Escribe la nueva contraseña inicial (mínimo 8 caracteres):",
  );
  if (!password) return;
  try {
    await request(`/auth/usuarios/${userId}/restablecer-password`, {
      method: "POST",
      body: JSON.stringify({ password_nueva: password }),
    });
    await loadUsers();
  } catch (error) {
    state.error = error.message;
    drawUsers();
  }
}
async function unlockUser(userId) {
  try {
    await request(`/auth/usuarios/${userId}/desbloquear`, { method: "POST" });
    await loadUsers();
  } catch (error) {
    state.error = error.message;
    drawUsers();
  }
}
async function toggleUserStatus(userId, currentState) {
  const nextState = currentState === "ACTIVO" ? "INACTIVO" : "ACTIVO";
  const action = nextState === "INACTIVO" ? "desactivar" : "activar";
  if (!window.confirm(`¿Deseas ${action} esta cuenta?`)) return;
  try {
    // Endpoints propios de activar/inactivar (integración Sprint 1).
    await request(
      `/auth/usuarios/${userId}/${nextState === "INACTIVO" ? "inactivar" : "activar"}`,
      { method: "POST" },
    );
    await loadUsers();
  } catch (error) {
    state.error = error.message;
    drawUsers();
  }
}
// HU-008: consulta de la auditoría (solo ADMINISTRADOR). Filtros por fecha,
// usuario y sede; resultado paginado del más reciente al más antiguo. La
// pantalla es de solo lectura: no hay botones para editar ni borrar.
async function auditoria() {
  const a = state.audit;
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">Seguridad</p><h1>Consulta de auditoria</h1><p class="subtle">Quien hizo que, en que sede y a que hora.</p></div></div><section class="panel"><form class="toolbar" id="audit-form"><select name="modulo" aria-label="Modulo"><option value="auth">Seguridad y usuarios</option><option value="parametrizacion">Parametrizacion</option></select><label class="subtle">Desde <input type="date" name="desde" value="${esc(a.desde)}"></label><label class="subtle">Hasta <input type="date" name="hasta" value="${esc(a.hasta)}"></label><input name="usuario" placeholder="Usuario" aria-label="Usuario" value="${esc(a.usuario)}"><select name="sede_id" aria-label="Sede"></select><button class="primary">Filtrar</button></form><div id="audit-table"></div><div class="toolbar" id="audit-pager"></div><p class="subtle">Resultado paginado, del mas reciente al mas antiguo. Los registros no se editan ni se borran.</p></section>`;
  const form = document.getElementById("audit-form");
  form.modulo.value = a.modulo;
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const datos = Object.fromEntries(new FormData(form));
    if (datos.desde && datos.hasta && datos.desde > datos.hasta) {
      document.getElementById("audit-table").innerHTML =
        '<p class="error">La fecha Desde no puede ser posterior a Hasta.</p>';
      return;
    }
    state.audit = { ...datos, usuario: datos.usuario.trim(), pagina: 1 };
    loadAudit();
  });
  try {
    await loadCatalogs();
    form.sede_id.innerHTML = refOptions("sedes", a.sede_id, "Todas las sedes");
    form.sede_id.value = a.sede_id;
  } catch {
    if (!state.token) return;
  }
  await loadAudit();
}
function fechaLocal(valor) {
  // El servidor guarda en UTC; si la fecha llega sin zona, se toma como UTC.
  const texto = /[zZ]|[+-]\d\d:?\d\d$/.test(valor) ? valor : `${valor}Z`;
  return new Date(texto).toLocaleString("es-CO", {
    dateStyle: "short",
    timeStyle: "short",
  });
}
async function loadAudit() {
  const a = state.audit,
    params = new URLSearchParams({ pagina: a.pagina, tamano: TAMANO_PAGINA });
  // Los días se toman en la hora local del navegador y se envían en UTC.
  if (a.desde) params.set("desde", new Date(`${a.desde}T00:00:00`).toISOString());
  if (a.hasta) params.set("hasta", new Date(`${a.hasta}T23:59:59.999`).toISOString());
  if (a.usuario) params.set("usuario", a.usuario);
  if (a.sede_id) params.set("sede_id", a.sede_id);
  let filas = [],
    error = "";
  try {
    filas = await request(`/${a.modulo === "parametrizacion" ? "parametrizacion" : "auth"}/auditoria?${params}`);
  } catch (e) {
    if (!state.token) return;
    error = e.message;
  }
  const total = state.lastTotal,
    destino = document.getElementById("audit-table");
  if (!destino) return;
  destino.innerHTML = error
    ? `<p class="error">${esc(error)}</p>`
    : filas.length
      ? `<div class="table-wrap"><table><thead><tr><th>Fecha y hora</th><th>Usuario</th><th>Sede</th><th>Accion</th><th>Entidad</th><th>Resultado</th><th>IP</th></tr></thead><tbody>${filas.map((r) => `<tr><td>${esc(fechaLocal(r.fecha))}</td><td>${esc(r.usuario || "")}</td><td>${r.sede_id ? esc(refName("sedes", r.sede_id)) : ""}</td><td>${esc(r.accion)}${r.detalle ? `<br><span class="subtle">${esc(r.detalle)}</span>` : ""}</td><td>${esc(r.entidad || "")}${r.entidad_id ? ` #${esc(r.entidad_id)}` : ""}</td><td><span class="badge ${r.resultado === "OK" ? "active" : "inactive"}">${esc(r.resultado)}</span></td><td>${esc(r.ip || "")}</td></tr>`).join("")}</tbody></table></div>`
      : '<div class="empty">No hay registros para esos filtros.</div>';
  drawPager("audit-pager", a.pagina, error ? 0 : total, (pagina) => {
    state.audit.pagina = pagina;
    loadAudit();
  });
}
function home() {
  if (state.user.sede_id) {
    request(`/parametrizacion/sedes/${state.user.sede_id}`)
      .then((sede) => {
        const el = document.getElementById("home-sede");
        if (el) el.textContent = sede.nombre;
      })
      .catch(() => {});
  }
  document.getElementById("view").innerHTML =
    `<div class="dashboard-view"><div class="topbar"><div><p class="eyebrow">Panel personal</p><h1>Hola, ${esc(state.user.nombre.split(" ")[0])}</h1><p class="subtle">Esta es tu informacion de acceso y las funciones principales de tu cargo.</p></div></div><div class="profile-layout single-panel"><section class="panel profile-card"><h2>Mi informacion</h2><div class="profile-details"><div><span>Nombre completo</span><strong>${esc(state.user.nombre)}</strong></div><div><span>Cedula</span><strong>${esc(state.user.cedula)}</strong></div><div><span>Usuario</span><strong>${esc(state.user.usuario)}</strong></div><div><span>Cargo</span><strong>${esc(state.user.perfil)}</strong></div><div><span>Sede</span><strong id="home-sede">${state.user.sede_id ? `Sede #${state.user.sede_id}` : "Todas las sedes"}</strong></div><div><span>Estado</span><strong><span class="badge active">${esc(state.user.estado)}</span></strong></div></div></section></div></div>`;
}
async function resource(key) {
  const r = RESOURCES[key];
  const productFilters =
    (hasSedeFilter(key)
      ? `<select id="sede-filter" aria-label="Filtrar por sede"><option value="">Todas las sedes</option></select>`
      : "") +
    (hasTipoFilter(key)
      ? `<select id="tipo-filter" aria-label="Filtrar por tipo"><option value="">Todos los tipos</option></select>`
      : "");
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">Parametrizacion</p><h1>${r.title}</h1><p class="subtle">Gestiona registros, busca coincidencias y distingue los elementos inactivos.</p></div>${esAdmin() ? '<div class="topbar-actions"><button class="primary" id="new-item">+ Nuevo</button></div>' : ""}</div><section class="panel"><div class="toolbar"><input id="search" placeholder="Buscar en el listado" aria-label="Buscar">${productFilters}<button class="ghost" id="refresh">Actualizar</button></div><div id="table"></div></section>`;
  document
    .getElementById("new-item")
    ?.addEventListener("click", () => form(key));
  document.getElementById("refresh").addEventListener("click", () => load(key));
  document.getElementById("search").addEventListener("input", (event) => {
    state.filter = event.target.value.toLowerCase();
    table(key);
  });
  ["sede", "tipo"].forEach((name) =>
    document
      .getElementById(`${name}-filter`)
      ?.addEventListener("change", (event) => {
        state[`${name}Filter`] = event.target.value;
        table(key);
      }),
  );
  await load(key);
}
function hasSedeFilter(key) {
  return esAdmin() && RESOURCES[key].fields.some((f) => f.key === "sede_id");
}
function hasTipoFilter(key) {
  return key === "productos";
}
async function load(key) {
  try {
    await loadCatalogs();
    state.items = await request(
      `/parametrizacion/${RESOURCES[key].endpoint}?solo_activos=false`,
    );
    state.error = "";
    fillFilters();
    table(key);
  } catch (error) {
    if (error.message !== "sesion") {
      state.error = error.message;
      table(key);
    }
  }
}
function fillFilters() {
  const sede = document.getElementById("sede-filter"),
    tipo = document.getElementById("tipo-filter");
  if (sede) {
    sede.innerHTML = refOptions("sedes", state.sedeFilter, "Todas las sedes");
    sede.value = state.sedeFilter;
  }
  if (tipo) {
    tipo.innerHTML = refOptions("tipos", state.tipoFilter, "Todos los tipos");
    tipo.value = state.tipoFilter;
  }
}
function table(key) {
  const r = RESOURCES[key],
    rows = state.items.filter(
      (item) =>
        r.fields
          .map((f) => cellValue(f, item))
          .join(" ")
          .toLowerCase()
          .includes(state.filter) &&
        (!hasSedeFilter(key) ||
          !state.sedeFilter ||
          String(item.sede_id) === state.sedeFilter) &&
        (!hasTipoFilter(key) ||
          !state.tipoFilter ||
          String(item.tipo_producto_id) === state.tipoFilter),
    );
  document.getElementById("table").innerHTML = state.error
    ? `<p class="error">${esc(state.error)}</p>`
    : rows.length
      ? `<div class="table-wrap"><table><thead><tr>${r.fields.map((f) => `<th>${f.label}</th>`).join("")}<th>Estado</th><th></th></tr></thead><tbody>${rows.map((item) => `<tr>${r.fields.map((f) => `<td>${esc(cellValue(f, item))}</td>`).join("")}<td><span class="badge ${item[r.active] === false ? "inactive" : "active"}">${item[r.active] === false ? "Inactivo" : "Activo"}</span></td><td>${esAdmin() ? `<button class="ghost edit" data-id="${item.id}">Editar</button>` : ""}</td></tr>`).join("")}</tbody></table></div>`
      : `<div class="empty">No hay registros para mostrar.</div>`;
  document.querySelectorAll(".edit").forEach((button) =>
    button.addEventListener("click", () =>
      form(
        key,
        state.items.find((item) => item.id === Number(button.dataset.id)),
      ),
    ),
  );
}
// Al editar, los campos "fixed" van deshabilitados: el navegador no los envía
// y la API no los cambia (H-01 de docs/05-contratos.md).
function fieldHtml(f, item) {
  const locked = item && f.fixed ? "disabled" : "",
    required = f.required && !locked ? "required" : "";
  if (f.ref)
    return `<label>${f.label}<select name="${f.key}" ${required} ${locked}>${refOptions(f.ref, item?.[f.key] ?? "")}</select></label>`;
  return `<label>${f.label}<input name="${f.key}" type="${f.type || "text"}" value="${esc(item?.[f.key])}" ${required} ${locked}></label>`;
}
function form(key, item = null) {
  const r = RESOURCES[key];
  document.body.insertAdjacentHTML(
    "beforeend",
    `<div class="modal-backdrop" id="modal"><section class="modal"><div class="topbar"><div><p class="eyebrow">${item ? "Editar registro" : "Nuevo registro"}</p><h2>${r.title}</h2></div><button class="ghost" id="close-modal">Cerrar</button></div><form id="resource-form"><div class="form-grid">${r.fields.map((f) => fieldHtml(f, item)).join("")}</div>${item && r.fields.some((f) => f.fixed) ? '<p class="subtle">Los campos en gris no se pueden cambiar despues de crear el registro.</p>' : ""}<div id="form-error"></div><div class="modal-actions"><button type="button" class="ghost" id="cancel-modal">Cancelar</button><button class="primary">Guardar</button></div></form></section></div>`,
  );
  const close = () => document.getElementById("modal")?.remove();
  document.getElementById("close-modal").addEventListener("click", close);
  document.getElementById("cancel-modal").addEventListener("click", close);
  document
    .getElementById("resource-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.target));
      r.fields
        .filter((f) => f.type === "number" || f.ref)
        .forEach((f) => {
          if (values[f.key] !== undefined && values[f.key] !== "")
            values[f.key] = Number(values[f.key]);
        });
      try {
        await request(
          `/parametrizacion/${r.endpoint}${item ? `/${item.id}` : ""}`,
          { method: item ? "PATCH" : "POST", body: JSON.stringify(values) },
        );
        close();
        state.filter = "";
        await load(key);
      } catch (error) {
        document.getElementById("form-error").innerHTML =
          `<p class="error">${esc(error.message)}</p>`;
      }
    });
}
if (state.token && state.user) {
  idle();
  state.user.debe_cambiar_password ? renderPasswordChange() : renderShell();
} else renderLogin();
