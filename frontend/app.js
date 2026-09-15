const API = "/api",
  SESSION_KEY = "barmoe_access_token",
  USER_KEY = "barmoe_user";
const MENU = {
  ADMINISTRADOR: ["sedes", "mesas", "proveedores", "productos", "usuarios"],
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
      { key: "sede_id", label: "Sede", type: "number", required: true },
      { key: "numero", label: "Numero", type: "number", required: true },
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
      { key: "nit", label: "NIT", required: true },
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
      { key: "codigo", label: "Codigo", required: true },
      { key: "nombre", label: "Nombre", required: true },
      { key: "sede_id", label: "Sede", type: "number", required: true },
      {
        key: "tipo_producto_id",
        label: "Tipo",
        type: "number",
        required: true,
      },
      {
        key: "proveedor_id",
        label: "Proveedor",
        type: "number",
        required: true,
      },
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
  idleTimer: null,
  lastActivityAt: 0,
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
    response.status === 401 &&
    [
      "NO_AUTENTICADO",
      "SESION_CERRADA",
      "SESION_EXPIRADA",
      "TOKEN_INVALIDO",
      "USUARIO_INACTIVO",
    ].includes(code)
  ) {
    clearSession();
    throw Error("La sesion expiro. Ingresa nuevamente.");
  }
  if (!response.ok) throw Error(message(data));
  return data;
}
function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(USER_KEY);
  state = { ...state, token: null, user: null };
  clearTimeout(state.idleTimer);
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

  clearSession();
  renderLogin("La sesion se cerro por tres minutos de inactividad.");
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
  form.addEventListener("input", () => {
    submit.disabled = ![...form.elements]
      .slice(0, 2)
      .every((field) => field.value.trim());
  });
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
function renderPasswordChange(note = "") {
  document.getElementById("app").innerHTML =
    `<main class="login-shell"><section class="container"><div class="brand"><span class="brand-mark">M</span><span>BAR DE MOE</span></div><h1 class="heading">Actualiza tu contraseña</h1><p class="login-kicker">Cambio obligatorio</p><p class="subtle">Por seguridad, debes crear una nueva contraseña antes de continuar.</p>${note ? `<p class="error" role="alert">${esc(note)}</p>` : ""}<form class="form" id="password-form"><label>Contraseña actual<input class="input" name="actual" type="password" autocomplete="current-password" placeholder="Contraseña actual" required></label><label>Nueva contraseña<input class="input" name="nueva" type="password" autocomplete="new-password" placeholder="Nueva contraseña" minlength="8" required></label><button class="login-button">Guardar contraseña</button></form></section></main>`;
  document
    .getElementById("password-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.target);
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
        if (!state.token) {
          renderLogin(error.message);
        } else {
          renderPasswordChange(error.message);
        }
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
    `<div class="shell"><aside class="sidebar"><div class="brand"><span class="brand-mark">M</span><span>BAR DE MOE</span></div><nav class="nav" aria-label="Menu principal">${links}</nav><div class="user-mini"><strong>${esc(state.user.nombre)}</strong><br>${esc(state.user.perfil)}<br><button class="ghost" id="logout" style="margin-top:12px;color:white;border-color:rgba(255,255,255,.35)">Cerrar sesion</button></div></aside><main class="content"><div class="workspace-frame" id="view"></div></main></div>`;
  document
    .querySelectorAll("[data-route]")
    .forEach((button) =>
      button.addEventListener("click", () => renderShell(button.dataset.route)),
    );
  document.getElementById("logout").addEventListener("click", logout);
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
  if (RESOURCES[state.route]) return resource(state.route);
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">${LABELS[state.route]}</p><h1>Modulo en preparacion</h1><p class="subtle">Tu perfil tiene acceso a esta opcion. El servicio funcional se incorporara en el siguiente sprint.</p></div></div><section class="panel"><h2>Acceso autorizado</h2><p class="subtle">La ruta esta protegida por perfil y tu sesion permanece activa.</p></section>`;
}
async function users() {
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">Seguridad</p><h1>Usuarios</h1><p class="subtle">Crea cuentas para tu equipo, asigna un perfil y entrega una contraseña inicial.</p></div><div class="topbar-actions"><button class="primary" id="new-user">+ Nuevo usuario</button></div></div><section class="panel"><div class="toolbar"><input id="user-search" placeholder="Buscar por nombre o usuario" aria-label="Buscar usuarios"><button class="ghost" id="refresh-users">Actualizar</button></div><div id="users-table"></div></section>`;
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
    state.users = await request("/auth/usuarios");
    state.error = "";
    drawUsers();
  } catch (error) {
    if (state.token) {
      state.error = error.message;
      drawUsers();
    }
  }
}
function drawUsers() {
  const usersList = (state.users || []).filter((item) =>
    JSON.stringify(item).toLowerCase().includes(state.filter),
  );
  document.getElementById("users-table").innerHTML = state.error
    ? `<p class="error">${esc(state.error)}</p>`
    : usersList.length
      ? `<div class="table-wrap"><table><thead><tr><th>Nombre</th><th>Usuario</th><th>Perfil</th><th>Sede</th><th>Estado</th><th>Acceso</th><th>Acciones</th></tr></thead><tbody>${usersList.map((item) => `<tr><td>${esc(item.nombre)}</td><td>${esc(item.usuario)}</td><td><span class="role-badge">${esc(item.perfil)}</span></td><td>${item.sede_id ?? "Todas"}</td><td><span class="badge ${item.estado === "ACTIVO" ? "active" : "inactive"}">${esc(item.estado)}</span></td><td>${item.debe_cambiar_password ? "Cambio pendiente" : "Listo"}</td><td><div class="user-actions"><button class="ghost reset-user" data-id="${item.id}">Restablecer clave</button><button class="ghost toggle-user ${item.estado === "INACTIVO" ? "activate" : "deactivate"}" data-id="${item.id}" data-state="${item.estado}">${item.estado === "INACTIVO" ? "Activar" : "Desactivar"}</button></div></td></tr>`).join("")}</tbody></table></div>`
      : `<div class="empty">No hay usuarios para mostrar.</div>`;
  document
    .querySelectorAll(".reset-user")
    .forEach((button) =>
      button.addEventListener("click", () =>
        resetUserPassword(Number(button.dataset.id)),
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
    `<div class="modal-backdrop" id="modal"><section class="modal"><div class="topbar"><div><p class="eyebrow">Administracion</p><h2>Crear usuario</h2></div><button class="ghost" id="close-modal">Cerrar</button></div><p class="subtle">La persona recibira estas credenciales y debera cambiar la contraseña al ingresar.</p><form id="user-form"><div class="form-grid"><label>Cedula<input name="cedula" minlength="5" maxlength="20" required></label><label>Nombre completo<input name="nombre" minlength="3" maxlength="120" required></label><label>Usuario<input name="usuario" minlength="4" maxlength="60" autocomplete="off" required></label><label>Contraseña inicial<input name="password" type="password" minlength="8" maxlength="72" autocomplete="new-password" required></label><label>Perfil<select name="perfil" required><option value="CAJERO">Cajero</option><option value="MESERO">Mesero</option><option value="ADMINISTRADOR">Administrador</option></select></label><label>Sede<input name="sede_id" type="number" min="1" placeholder="ID de sede"></label></div><div id="form-error"></div><div class="modal-actions"><button type="button" class="ghost" id="cancel-modal">Cancelar</button><button class="primary">Crear usuario</button></div></form></section></div>`,
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
      try {
        await request("/auth/usuarios", {
          method: "POST",
          body: JSON.stringify(values),
        });
        close();
        state.filter = "";
        await loadUsers();
      } catch (error) {
        document.getElementById("form-error").innerHTML =
          `<p class="error">${esc(error.message)}</p>`;
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
async function toggleUserStatus(userId, currentState) {
  const nextState = currentState === "ACTIVO" ? "INACTIVO" : "ACTIVO";
  const action = nextState === "INACTIVO" ? "desactivar" : "activar";
  if (!window.confirm(`¿Deseas ${action} esta cuenta?`)) return;
  try {
    await request(`/auth/usuarios/${userId}`, {
      method: "PATCH",
      body: JSON.stringify({ estado: nextState }),
    });
    await loadUsers();
  } catch (error) {
    state.error = error.message;
    drawUsers();
  }
}
function home() {
  document.getElementById("view").innerHTML =
    `<div class="dashboard-view"><div class="topbar"><div><p class="eyebrow">Panel personal</p><h1>Hola, ${esc(state.user.nombre.split(" ")[0])}</h1><p class="subtle">Esta es tu informacion de acceso y las funciones principales de tu cargo.</p></div></div><div class="profile-layout single-panel"><section class="panel profile-card"><h2>Mi informacion</h2><div class="profile-details"><div><span>Nombre completo</span><strong>${esc(state.user.nombre)}</strong></div><div><span>Cedula</span><strong>${esc(state.user.cedula)}</strong></div><div><span>Usuario</span><strong>${esc(state.user.usuario)}</strong></div><div><span>Cargo</span><strong>${esc(state.user.perfil)}</strong></div><div><span>Sede</span><strong>${state.user.sede_id ? `Sede #${state.user.sede_id}` : "Todas las sedes"}</strong></div><div><span>Estado</span><strong><span class="badge active">${esc(state.user.estado)}</span></strong></div></div></section></div></div>`;
}
async function resource(key) {
  const r = RESOURCES[key];
  const productFilters =
    key === "productos"
      ? `<select id="sede-filter" aria-label="Filtrar por sede"><option value="">Todas las sedes</option></select><select id="tipo-filter" aria-label="Filtrar por tipo"><option value="">Todos los tipos</option></select>`
      : "";
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">Parametrizacion</p><h1>${r.title}</h1><p class="subtle">Gestiona registros, busca coincidencias y distingue los elementos inactivos.</p></div><div class="topbar-actions"><button class="primary" id="new-item">+ Nuevo</button></div></div><section class="panel"><div class="toolbar"><input id="search" placeholder="Buscar en el listado" aria-label="Buscar">${productFilters}<button class="ghost" id="refresh">Actualizar</button></div><div id="table"></div></section>`;
  document
    .getElementById("new-item")
    .addEventListener("click", () => form(key));
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
async function load(key) {
  try {
    state.items = await request(
      `/parametrizacion/${RESOURCES[key].endpoint}?solo_activos=false`,
    );
    state.error = "";
    if (key === "productos") fillProductFilters();
    table(key);
  } catch (error) {
    if (error.message !== "sesion") {
      state.error = error.message;
      table(key);
    }
  }
}
function fillProductFilters() {
  const sede = document.getElementById("sede-filter"),
    tipo = document.getElementById("tipo-filter");
  if (!sede || !tipo) return;
  const sedes = [...new Set(state.items.map((item) => item.sede_id))].sort(),
    tipos = [
      ...new Set(state.items.map((item) => item.tipo_producto_id)),
    ].sort();
  sede.innerHTML =
    '<option value="">Todas las sedes</option>' +
    sedes
      .map((value) => `<option value="${value}">Sede ${value}</option>`)
      .join("");
  tipo.innerHTML =
    '<option value="">Todos los tipos</option>' +
    tipos
      .map((value) => `<option value="${value}">Tipo ${value}</option>`)
      .join("");
  sede.value = state.sedeFilter;
  tipo.value = state.tipoFilter;
}
function table(key) {
  const r = RESOURCES[key],
    rows = state.items.filter(
      (item) =>
        JSON.stringify(item).toLowerCase().includes(state.filter) &&
        (!state.sedeFilter || String(item.sede_id) === state.sedeFilter) &&
        (!state.tipoFilter ||
          String(item.tipo_producto_id) === state.tipoFilter),
    );
  document.getElementById("table").innerHTML = state.error
    ? `<p class="error">${esc(state.error)}</p>`
    : rows.length
      ? `<div class="table-wrap"><table><thead><tr>${r.fields.map((f) => `<th>${f.label}</th>`).join("")}<th>Estado</th><th></th></tr></thead><tbody>${rows.map((item) => `<tr>${r.fields.map((f) => `<td>${esc(item[f.key])}</td>`).join("")}<td><span class="badge ${item[r.active] === false ? "inactive" : "active"}">${item[r.active] === false ? "Inactivo" : "Activo"}</span></td><td><button class="ghost edit" data-id="${item.id}">Editar</button></td></tr>`).join("")}</tbody></table></div>`
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
function form(key, item = null) {
  const r = RESOURCES[key];
  document.body.insertAdjacentHTML(
    "beforeend",
    `<div class="modal-backdrop" id="modal"><section class="modal"><div class="topbar"><div><p class="eyebrow">${item ? "Editar registro" : "Nuevo registro"}</p><h2>${r.title}</h2></div><button class="ghost" id="close-modal">Cerrar</button></div><form id="resource-form"><div class="form-grid">${r.fields.map((f) => `<label>${f.label}<input name="${f.key}" type="${f.type || "text"}" value="${esc(item?.[f.key])}" ${f.required ? "required" : ""}></label>`).join("")}</div><div id="form-error"></div><div class="modal-actions"><button type="button" class="ghost" id="cancel-modal">Cancelar</button><button class="primary">Guardar</button></div></form></section></div>`,
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
        .filter((f) => f.type === "number")
        .forEach((f) => {
          if (values[f.key] !== "") values[f.key] = Number(values[f.key]);
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
