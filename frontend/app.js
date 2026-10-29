const API = "/api",
  SESSION_KEY = "barmoe_access_token",
  USER_KEY = "barmoe_user",
  LANG_KEY = "barmoe_lang",
  LOCAL_STOCK_KEY = "barmoe_local_stock",
  LOCAL_ORDERS_KEY = "barmoe_local_orders",
  LOCAL_TABLES_KEY = "barmoe_local_tables";

const MENU = {
  ADMINISTRADOR: [
    "sedes",
    "mesas",
    "tipos-producto",
    "proveedores",
    "productos",
    "inventario",
    "pedidos",
    "usuarios",
  ],
  MESERO: ["mesas", "inventario", "pedidos"],
  CAJERO: [
    "mesas",
    "inventario",
    "pedidos",
    "facturacion",
    "consulta-facturas",
    "reporte-ventas",
  ],
};

const I18N = {
  es: {
    brandSub: "Operación multisede",
    welcomeBack: "Bienvenido de nuevo",
    loginPrompt: "Ingresa con tus credenciales para continuar.",
    usernameLabel: "Usuario",
    usernamePlaceholder: "Tu usuario",
    passwordLabel: "Contraseña",
    passwordPlaceholder: "Tu contraseña",
    loginBtn: "Ingresar",
    loggingInBtn: "Ingresando...",
    loginFooter: "Acceso seguro para el equipo de Bar de Moe",
    updatePassTitle: "Actualiza tu contraseña",
    mandatoryChange: "Cambio obligatorio",
    updatePassPrompt:
      "Por seguridad, debes crear una nueva contraseña (mínimo 8 caracteres, mayúscula, minúscula y número) antes de continuar.",
    currentPassLabel: "Contraseña actual",
    newPassLabel: "Nueva contraseña",
    savePassBtn: "Guardar contraseña",
    logoutBtn: "Cerrar sesión",
    sessionClosed: "Has cerrado sesión correctamente.",
    sessionExpired:
      "Tu sesión ha expirado o fue cerrada. Por favor, ingresa tus credenciales nuevamente.",
    inactivityClosed:
      "Por tu seguridad, la sesión se cerró automáticamente tras 3 minutos de inactividad (RNF-03).",
    personalPanel: "Panel personal",
    hello: "Hola",
    homeSub:
      "Esta es tu información de acceso y las funciones principales habilitadas para tu cargo.",
    myInfo: "Mi información",
    fullName: "Nombre completo",
    idCard: "Cédula",
    role: "Cargo / Perfil",
    branch: "Sede asignada",
    allBranches: "Todas las sedes",
    status: "Estado",
    nav: {
      sedes: "Sedes",
      mesas: "Mapa de mesas",
      "tipos-producto": "Tipos de producto",
      proveedores: "Proveedores",
      productos: "Productos",
      inventario: "Inventario por sede",
      pedidos: "Toma de pedidos",
      usuarios: "Usuarios",
      facturacion: "Facturación",
      "consulta-facturas": "Consulta de facturas",
      "reporte-ventas": "Reporte de ventas",
    },
    fields: {
      nombre: "Nombre completo",
      direccion: "Dirección",
      telefono: "Teléfono",
      sede_id: "Sede",
      numero: "Número de mesa",
      capacidad: "Capacidad (personas)",
      descripcion: "Descripción",
      nit: "NIT",
      contacto: "Contacto comercial",
      codigo: "Código",
      tipo_producto_id: "Tipo de producto",
      proveedor_id: "Proveedor",
      valor_compra: "Valor compra ($)",
      valor_venta: "Valor venta ($)",
      stock: "Existencias (unidades)",
      stock_minimo: "Stock mínimo alerta",
      cedula: "Cédula",
      usuario: "Usuario",
      password: "Contraseña",
      perfil: "Perfil",
      estado: "Estado",
      cantidad: "Cantidad",
      mesa_id: "Mesa",
    },
    common: {
      parametrization: "Parametrización maestra",
      security: "Seguridad",
      operations: "Operación · Sprint 2",
      newBtn: "+ Nuevo",
      refresh: "Actualizar",
      searchPlaceholder: "Buscar en el listado...",
      allBranchesFilter: "Todas las sedes",
      allTypesFilter: "Todos los tipos",
      selectOption: "Selecciona una opción",
      active: "Activo",
      inactive: "Inactivo",
      activate: "Activar",
      deactivate: "Desactivar",
      edit: "Editar",
      close: "Cerrar",
      cancel: "Cancelar",
      save: "Guardar",
      scopeCol: "Alcance",
      allBranchesBadge: "Todas las sedes",
      globalProductHint:
        "Este producto queda habilitado en el catálogo de todas las sedes. Las existencias (stock) se administran individualmente por sede en 'Inventario por sede'.",
      noRecords: "No se encontraron registros con los filtros actuales.",
      editRecord: "Editar registro",
      newRecord: "Nuevo registro",
      lockedFieldsHint:
        "Los campos sombreados son identificadores fijos y no se pueden modificar después de crear el registro.",
      resourceSub:
        "Crea, edita, activa o inactiva registros maestros de la plataforma.",
      prepTitle: "Módulo programado para próximo Sprint",
      prepSub:
        "Tu perfil tiene acceso autorizado a esta vista. Este módulo corresponde a los Sprints 3 y 4 del Product Backlog.",
      authAccess: "Acceso autorizado por perfil",
      authAccessSub:
        "La ruta está protegida según tu rol y tu sesión permanece activa.",
    },
    users: {
      title: "Gestión de Usuarios",
      sub: "Crea, edita, activa o desactiva cuentas para tu equipo, asigna perfiles y administra el acceso por sede.",
      newBtn: "+ Nuevo usuario",
      editTitle: "Editar usuario",
      searchPlaceholder: "Buscar por nombre completo, usuario o cédula...",
      accessCol: "Acceso",
      actionsCol: "Acciones",
      blocked: "Bloqueado",
      pendingPass: "Cambio pendiente",
      ready: "Listo",
      unlock: "Desbloquear",
      resetPass: "Password",
      activate: "Activar",
      deactivate: "Desactivar",
      createTitle: "Crear usuario",
      createHint:
        "La persona recibirá estas credenciales y deberá cambiar la contraseña en su primer ingreso.",
      editHint:
        "Actualiza el nombre completo, perfil, sede asignada o estado de la cuenta.",
      allAdminOnly: "Todas las sedes (solo Administrador)",
      branchMandatoryHint:
        "El cajero y el mesero deben tener una sede asignada y solo verán información de su sede.",
      branchMandatoryError:
        "Acción requerida: El perfil Cajero o Mesero requiere seleccionar una sede específica.",
      promptNewPass:
        "Escribe la nueva contraseña temporal (mínimo 8 caracteres, con mayúscula, minúscula y número):",
      confirmToggle: "¿Confirmas que deseas {action} esta cuenta de usuario?",
    },
    inventory: {
      eyebrow: "HU-012 · M3 Inventario",
      title: "Inventario individual por sede",
      sub: "Cada sede maneja su propio stock independiente sobre el catálogo global de productos.",
      totalRefs: "Referencias en la sede",
      totalUnits: "Unidades totales en stock",
      lowStockAlerts: "Alertas (bajo stock / agotado)",
      allStockStates: "Todos los niveles de stock",
      inStock: "Disponible",
      lowStock: "Bajo stock",
      outOfStock: "Agotado",
      stockCol: "Existencias sede",
      minCol: "Mínimo",
      levelCol: "Nivel",
      adjustBtn: "Ajustar stock",
      modalTitle: "Movimiento de inventario en sede",
      moveType: "Tipo de movimiento",
      typeEntry: "Entrada de mercancía (+ sumar)",
      typeExit: "Salida / Merma (- restar)",
      typeSet: "Ajuste exacto (= fijar stock)",
      qtyLabel: "Cantidad de unidades",
      minStockLabel: "Alerta de stock mínimo",
      reasonLabel: "Motivo / Observación",
      reasonPlaceholder: "Ej: Recepción proveedor Bavaria, conteo físico...",
      saveAdjust: "Aplicar en esta sede",
    },
    tables: {
      eyebrow: "HU-013 · M4 Mesas",
      title: "Mapa de mesas de la sede",
      sub: "Visualiza en rejilla 3×N la ocupación en tiempo real de cada mesa y administra sus pedidos.",
      mapView: "Mapa 3×N",
      tableView: "Vista lista",
      newTableBtn: "+ Nueva mesa",
      totalTables: "Total mesas activas",
      freeTables: "Mesas libres",
      occupiedTables: "Mesas ocupadas",
      allStates: "Todos los estados",
      free: "LIBRE",
      occupied: "OCUPADA",
      capacity: "Capacidad",
      people: "personas",
      takeOrder: "Tomar pedido",
      viewOrder: "Ver pedido",
      markFree: "Liberar mesa",
      markOccupied: "Ocupar mesa",
      activeOrderBadge: "Pedido #{id} · ${total} ({items} ítems)",
      searchTable: "Buscar por número de mesa o sede...",
    },
    orders: {
      eyebrow: "HU-014 · M4 Pedidos",
      title: "Pantalla de toma de pedido",
      sub: "Selecciona una mesa de la sede, verifica existencias de esa sede en lista y registra el pedido.",
      catalogTitle: "1. Productos disponibles en la sede",
      selectTableLabel: "Mesa a atender",
      selectTablePrompt: "-- Selecciona una mesa activa --",
      searchProdPlaceholder: "Buscar producto por nombre o código...",
      availableLabel: "Stock sede",
      addBtn: "+ Agregar",
      outBtn: "Agotado",
      ticketTitle: "2. Comanda del pedido",
      noTableSelected: "Selecciona una mesa arriba para iniciar el pedido.",
      emptyCart:
        "Aún no has agregado productos. Usa el botón '+ Agregar' de la lista.",
      notesLabel: "Observaciones del pedido (opcional)",
      notesPlaceholder: "Ej: Cervezas bien frías, sin pitillo, vasos extra...",
      totalLabel: "Total del pedido",
      confirmBtn: "Confirmar pedido",
      clearCartBtn: "Vaciar",
      orderCreatedSuccess:
        "¡Pedido #{id} registrado con éxito! Se descontó el stock de la sede y la mesa pasó a ocupada.",
      stockLimitError:
        "No puedes agregar más unidades de '{name}': solo hay {stock} unidades disponibles en el inventario de esta sede.",
      selectTableError:
        "Debes seleccionar una mesa activa antes de confirmar el pedido.",
      emptyCartError:
        "Agrega al menos un producto al pedido antes de confirmar.",
      historyTitle: "Pedidos activos y recientes de la sede",
      allOrderStates: "Todos los estados",
      stateOpen: "ABIERTO",
      stateDelivered: "ENTREGADO",
      stateClosed: "CERRADO",
      stateCancelled: "CANCELADO",
      colOrder: "Pedido",
      colTable: "Mesa",
      colWaiter: "Atendió (Nombre completo)",
      colItems: "Productos solicitados",
      colTotal: "Total",
      colState: "Estado",
      colActions: "Acciones",
      deliverBtn: "Entregar",
      closeOrderBtn: "Cerrar y liberar mesa",
      cancelOrderBtn: "Cancelar (devolver stock)",
    },
  },
  en: {
    brandSub: "Multi-branch operation",
    welcomeBack: "Welcome back",
    loginPrompt: "Sign in with your credentials to continue.",
    usernameLabel: "Username",
    usernamePlaceholder: "Your username",
    passwordLabel: "Password",
    passwordPlaceholder: "Your password",
    loginBtn: "Sign In",
    loggingInBtn: "Signing in...",
    loginFooter: "Secure access for Moe's Tavern team",
    updatePassTitle: "Update your password",
    mandatoryChange: "Mandatory password change",
    updatePassPrompt:
      "For security reasons, please create a new password (min. 8 characters, uppercase, lowercase, and number) before continuing.",
    currentPassLabel: "Current password",
    newPassLabel: "New password",
    savePassBtn: "Save new password",
    logoutBtn: "Sign out",
    sessionClosed: "You have signed out successfully.",
    sessionExpired:
      "Your session expired or was closed. Please sign in again.",
    inactivityClosed:
      "For your security, your session was automatically closed after 3 minutes of inactivity (RNF-03).",
    personalPanel: "Personal dashboard",
    hello: "Hello",
    homeSub:
      "Here is your access information and the main operations enabled for your role.",
    myInfo: "My profile details",
    fullName: "Full name",
    idCard: "ID / Document",
    role: "Role / Profile",
    branch: "Assigned branch",
    allBranches: "All branches",
    status: "Status",
    nav: {
      sedes: "Branches",
      mesas: "Table map",
      "tipos-producto": "Product types",
      proveedores: "Suppliers",
      productos: "Products",
      inventario: "Branch inventory",
      pedidos: "Order taking",
      usuarios: "Users",
      facturacion: "Billing",
      "consulta-facturas": "Invoices lookup",
      "reporte-ventas": "Sales report",
    },
    fields: {
      nombre: "Full name / Name",
      direccion: "Address",
      telefono: "Phone",
      sede_id: "Branch",
      numero: "Table number",
      capacidad: "Capacity (guests)",
      descripcion: "Description",
      nit: "Tax ID (NIT)",
      contacto: "Contact person",
      codigo: "Code",
      tipo_producto_id: "Product type",
      proveedor_id: "Supplier",
      valor_compra: "Purchase cost ($)",
      valor_venta: "Sale price ($)",
      stock: "Stock (units)",
      stock_minimo: "Min. stock alert",
      cedula: "ID number",
      usuario: "Username",
      password: "Password",
      perfil: "Role",
      estado: "Status",
      cantidad: "Quantity",
      mesa_id: "Table",
    },
    common: {
      parametrization: "Master Setup",
      security: "Security",
      operations: "Operations · Sprint 2",
      newBtn: "+ New",
      refresh: "Refresh",
      searchPlaceholder: "Search records...",
      allBranchesFilter: "All branches",
      allTypesFilter: "All product types",
      selectOption: "Select an option",
      active: "Active",
      inactive: "Inactive",
      activate: "Activate",
      deactivate: "Deactivate",
      edit: "Edit",
      close: "Close",
      cancel: "Cancel",
      save: "Save",
      scopeCol: "Scope",
      allBranchesBadge: "All branches",
      globalProductHint:
        "This product is created and updated across all branches. Stock is managed individually per branch in 'Branch inventory'.",
      noRecords: "No records match the current filters.",
      editRecord: "Edit record",
      newRecord: "New record",
      lockedFieldsHint:
        "Shaded fields are fixed identifiers and cannot be modified after creation.",
      resourceSub:
        "Create, edit, activate, or deactivate master records across the platform.",
      prepTitle: "Module scheduled for upcoming Sprint",
      prepSub:
        "Your profile has authorized access to this route. This functional service belongs to Sprints 3 and 4.",
      authAccess: "Role-authorized access",
      authAccessSub:
        "This route is protected by your profile and your session remains active.",
    },
    users: {
      title: "User Management",
      sub: "Create, edit, activate, or deactivate staff accounts, assign roles, and manage branch access.",
      newBtn: "+ New user",
      editTitle: "Edit user",
      searchPlaceholder: "Search by full name, username, or ID...",
      accessCol: "Access",
      actionsCol: "Actions",
      blocked: "Locked",
      pendingPass: "Password change pending",
      ready: "Ready",
      unlock: "Unlock",
      resetPass: "Password",
      activate: "Activate",
      deactivate: "Deactivate",
      createTitle: "Create user",
      createHint:
        "The staff member will receive these credentials and must change their password upon first login.",
      editHint:
        "Update the staff member's full name, role, assigned branch, or account status.",
      allAdminOnly: "All branches (Administrator only)",
      branchMandatoryHint:
        "Cashiers and waiters must be assigned to a branch and can only view data from their branch.",
      branchMandatoryError:
        "Action required: Cashier and Waiter roles must have a specific branch assigned.",
      promptNewPass:
        "Enter the new temporary password (min. 8 characters, with uppercase, lowercase, and number):",
      confirmToggle: "Are you sure you want to {action} this user account?",
    },
    inventory: {
      eyebrow: "HU-012 · M3 Inventory",
      title: "Branch inventory",
      sub: "Each branch manages its own independent stock over the global product catalog.",
      totalRefs: "Branch catalog items",
      totalUnits: "Total units in stock",
      lowStockAlerts: "Alerts (low / out of stock)",
      allStockStates: "All stock levels",
      inStock: "In stock",
      lowStock: "Low stock",
      outOfStock: "Out of stock",
      stockCol: "Branch stock",
      minCol: "Min. alert",
      levelCol: "Level",
      adjustBtn: "Adjust stock",
      modalTitle: "Branch inventory movement",
      moveType: "Movement type",
      typeEntry: "Stock entry (+ add units)",
      typeExit: "Stock exit / shrinkage (- deduct)",
      typeSet: "Exact stock count (= set total)",
      qtyLabel: "Number of units",
      minStockLabel: "Minimum stock alert threshold",
      reasonLabel: "Reason / Notes",
      reasonPlaceholder: "E.g., Supplier delivery, physical count...",
      saveAdjust: "Apply to this branch",
    },
    tables: {
      eyebrow: "HU-013 · M4 Tables",
      title: "Branch table map",
      sub: "Monitor real-time table occupancy in a 3×N grid and open or manage active table orders.",
      mapView: "3×N Map",
      tableView: "List view",
      newTableBtn: "+ New table",
      totalTables: "Active tables",
      freeTables: "Free tables",
      occupiedTables: "Occupied tables",
      allStates: "All statuses",
      free: "FREE",
      occupied: "OCCUPIED",
      capacity: "Capacity",
      people: "guests",
      takeOrder: "Take order",
      viewOrder: "View order",
      markFree: "Free table",
      markOccupied: "Occupy table",
      activeOrderBadge: "Order #{id} · ${total} ({items} items)",
      searchTable: "Search by table number or branch...",
    },
    orders: {
      eyebrow: "HU-014 · M4 Orders",
      title: "Order taking screen",
      sub: "Select a table in your branch, check branch stock in list view, and submit the customer order.",
      catalogTitle: "1. Available branch products",
      selectTableLabel: "Table to serve",
      selectTablePrompt: "-- Select an active table --",
      searchProdPlaceholder: "Search product by name or code...",
      availableLabel: "Branch stock",
      addBtn: "+ Add",
      outBtn: "Out of stock",
      ticketTitle: "2. Order ticket",
      noTableSelected: "Select a table above to start building the order.",
      emptyCart:
        "No products added yet. Use the '+ Add' button in the product list.",
      notesLabel: "Order notes (optional)",
      notesPlaceholder: "E.g., Extra cold beers, extra glasses...",
      totalLabel: "Order total",
      confirmBtn: "Confirm order",
      clearCartBtn: "Clear",
      orderCreatedSuccess:
        "Order #{id} submitted! Branch stock was deducted and the table is now marked as occupied.",
      stockLimitError:
        "Cannot add more units of '{name}': only {stock} units are available in this branch's inventory.",
      selectTableError:
        "Please select an active table before confirming the order.",
      emptyCartError:
        "Please add at least one product to the order before confirming.",
      historyTitle: "Active and recent branch orders",
      allOrderStates: "All statuses",
      stateOpen: "OPEN",
      stateDelivered: "DELIVERED",
      stateClosed: "CLOSED",
      stateCancelled: "CANCELLED",
      colOrder: "Order",
      colTable: "Table",
      colWaiter: "Server (Full Name)",
      colItems: "Ordered items",
      colTotal: "Total",
      colState: "Status",
      colActions: "Actions",
      deliverBtn: "Mark delivered",
      closeOrderBtn: "Close & free table",
      cancelOrderBtn: "Cancel (restore stock)",
    },
  },
};

const ERROR_MESSAGES = {
  es: {
    CREDENCIALES_INVALIDAS:
      "Credenciales incorrectas: el usuario o la contraseña no coinciden. Verifica mayúsculas y números (después de 3 intentos fallidos la cuenta se bloqueará por seguridad).",
    USUARIO_BLOQUEADO:
      "Cuenta bloqueada por seguridad tras múltiples intentos fallidos (HU-002). Solicita a un Administrador que desbloquee tu usuario desde el módulo de Usuarios.",
    USUARIO_INACTIVO:
      "Tu cuenta de usuario se encuentra inactiva. Comunícate con el Administrador del sistema para reactivar tu acceso.",
    SESION_ACTIVA:
      "Ya existe una sesión activa con este usuario en otro dispositivo o pestaña (HU-003 · Sesión única). Cierra la otra sesión o espera 3 minutos de inactividad.",
    DEMASIADOS_INTENTOS:
      "Se detectaron demasiados intentos fallidos desde esta dirección IP. Por seguridad, espera unos minutos antes de volver a intentarlo.",
    SESION_EXPIRADA:
      "Tu sesión se cerró automáticamente por permanecer más de 3 minutos sin actividad (RNF-03). Inicia sesión de nuevo.",
    SESION_CERRADA:
      "La sesión ya no está activa. Por favor inicia sesión nuevamente.",
    TOKEN_INVALIDO:
      "Tu credencial de sesión no es válida o expiró. Inicia sesión nuevamente.",
    NO_AUTENTICADO:
      "Debes iniciar sesión con tu cuenta para acceder a esta función.",
    SIN_PERMISOS:
      "Acceso denegado: tu perfil actual no tiene permisos para realizar esta operación (reservada para Administradores).",
    SEDE_NO_AUTORIZADA:
      "Acceso restringido por sede: tu perfil operativo solo está autorizado para consultar y operar registros de tu propia sede asignada.",
    SIN_SEDE:
      "Tu cuenta operativa no tiene una sede asignada. Pide al Administrador que te asigne una sede.",
    SEDE_DUPLICADA:
      "Ya existe una sede registrada con ese mismo nombre. Usa un nombre distinto.",
    MESA_DUPLICADA:
      "Ese número de mesa ya está registrado en la sede seleccionada. Elige otro número de mesa.",
    TIPO_DUPLICADO:
      "Ya existe un tipo de producto con ese nombre. Ingresa un nombre diferente.",
    PROVEEDOR_DUPLICADO:
      "Ya existe un proveedor registrado con ese número de NIT.",
    PRODUCTO_DUPLICADO:
      "Ese código de producto ya existe en el catálogo. Usa un código único.",
    USUARIO_DUPLICADO:
      "Ese nombre de usuario ya está en uso por otra persona. Elige uno diferente.",
    CEDULA_DUPLICADA:
      "Ya existe un usuario registrado con ese número de cédula.",
    MARGEN_NEGATIVO:
      "Regla de negocio: el valor de venta no puede ser menor que el valor de compra (generaría margen negativo).",
    PASSWORD_DEBIL:
      "Contraseña insegura: debe tener entre 8 y 72 caracteres e incluir al menos una letra mayúscula, una minúscula y un número.",
    PASSWORD_REPETIDA:
      "La nueva contraseña debe ser diferente a tu contraseña actual.",
    SEDE_CON_RECURSOS_ACTIVOS:
      "No se puede desactivar esta sede porque aún tiene mesas o productos activos asociados. Inactívalos primero.",
    TIPO_CON_PRODUCTOS_ACTIVOS:
      "No se puede desactivar este tipo de producto porque tiene productos activos asociados en el catálogo.",
    PROVEEDOR_CON_PRODUCTOS_ACTIVOS:
      "No se puede desactivar este proveedor porque tiene productos activos asociados en el catálogo.",
    OPERACION_SOBRE_SI_MISMO:
      "Por seguridad, no puedes desactivar tu propia cuenta ni quitarte el rol de Administrador.",
    SEDE_OBLIGATORIA:
      "Los perfiles Cajero y Mesero deben tener obligatoriamente una sede asignada.",
    STOCK_INSUFICIENTE:
      "Inventario insuficiente en la sede para completar la operación con las unidades solicitadas.",
    MESA_INACTIVA:
      "La mesa seleccionada está inactiva y no admite pedidos en este momento.",
    PRODUCTO_INACTIVO:
      "Uno de los productos seleccionados está inactivo y no puede venderse.",
  },
  en: {
    CREDENCIALES_INVALIDAS:
      "Invalid credentials: username or password does not match. Check capitalization and numbers (accounts lock after 3 failed attempts).",
    USUARIO_BLOQUEADO:
      "Account locked for security after multiple failed login attempts (HU-002). Please ask an Administrator to unlock your account.",
    USUARIO_INACTIVO:
      "Your user account is currently inactive. Contact the system Administrator to reactivate your access.",
    SESION_ACTIVA:
      "This user already has an active session open in another device or tab (HU-003 · Single session). Sign out from the other session or wait 3 minutes.",
    DEMASIADOS_INTENTOS:
      "Too many failed login attempts from this IP address. Please wait a few minutes before trying again.",
    SESION_EXPIRADA:
      "Your session was automatically closed after 3 minutes of inactivity (RNF-03). Please sign in again.",
    SESION_CERRADA: "Your session is no longer active. Please sign in again.",
    TOKEN_INVALIDO:
      "Your session token is invalid or has expired. Please sign in again.",
    NO_AUTENTICADO: "You must be signed in to perform this action.",
    SIN_PERMISOS:
      "Access denied: your current role does not have permission to perform this action (Administrator required).",
    SEDE_NO_AUTORIZADA:
      "Branch access restricted: your role is only authorized to view and operate records belonging to your assigned branch.",
    SIN_SEDE:
      "Your operational account does not have an assigned branch. Ask an Administrator to assign one.",
    SEDE_DUPLICADA:
      "A branch with this name already exists. Please choose a different name.",
    MESA_DUPLICADA:
      "This table number already exists in the selected branch. Please choose a different number.",
    TIPO_DUPLICADO:
      "A product type with this name already exists. Please use a different name.",
    PROVEEDOR_DUPLICADO:
      "A supplier with this Tax ID (NIT) is already registered.",
    PRODUCTO_DUPLICADO:
      "This product code already exists in the catalog. Please use a unique code.",
    USUARIO_DUPLICADO:
      "This username is already taken. Please choose a different username.",
    CEDULA_DUPLICADA:
      "A user with this ID / Document number is already registered.",
    MARGEN_NEGATIVO:
      "Business rule violation: sale price cannot be lower than purchase cost (would cause a negative margin).",
    PASSWORD_DEBIL:
      "Weak password: must be 8–72 characters long and include at least one uppercase letter, one lowercase letter, and one number.",
    PASSWORD_REPETIDA:
      "Your new password must be different from your current password.",
    SEDE_CON_RECURSOS_ACTIVOS:
      "Cannot deactivate this branch because it still has active tables or products. Deactivate them first.",
    TIPO_CON_PRODUCTOS_ACTIVOS:
      "Cannot deactivate this product type because it has active products linked to it.",
    PROVEEDOR_CON_PRODUCTOS_ACTIVOS:
      "Cannot deactivate this supplier because it has active products linked to it.",
    OPERACION_SOBRE_SI_MISMO:
      "For safety, you cannot deactivate your own account or remove your own Administrator role.",
    SEDE_OBLIGATORIA:
      "Cashier and Waiter profiles must have an assigned branch.",
    STOCK_INSUFICIENTE:
      "Insufficient branch stock to complete the operation with the requested quantity.",
    MESA_INACTIVA:
      "The selected table is inactive and cannot take orders right now.",
    PRODUCTO_INACTIVO:
      "One of the selected products is inactive and cannot be ordered.",
  },
};

const RESOURCES = {
  sedes: {
    endpoint: "sedes",
    fields: [
      { key: "nombre", required: true },
      { key: "direccion" },
      { key: "telefono" },
    ],
    active: "activa",
  },
  mesas: {
    endpoint: "mesas",
    fields: [
      { key: "sede_id", ref: "sedes", required: true, fixed: true },
      { key: "numero", type: "number", required: true, fixed: true },
      { key: "capacidad", type: "number", required: true },
    ],
    active: "activa",
  },
  "tipos-producto": {
    endpoint: "tipos-producto",
    fields: [{ key: "nombre", required: true }, { key: "descripcion" }],
    active: "activo",
  },
  proveedores: {
    endpoint: "proveedores",
    fields: [
      { key: "nit", required: true, fixed: true },
      { key: "nombre", required: true },
      { key: "contacto" },
      { key: "telefono" },
    ],
    active: "activo",
  },
  productos: {
    endpoint: "productos",
    globalCatalog: true,
    fields: [
      { key: "codigo", required: true, fixed: true },
      { key: "nombre", required: true },
      { key: "tipo_producto_id", ref: "tipos", required: true },
      { key: "proveedor_id", ref: "proveedores", required: true },
      { key: "valor_compra", type: "number", required: true },
      { key: "valor_venta", type: "number", required: true },
    ],
    active: "activo",
  },
};

let state = {
  lang: localStorage.getItem(LANG_KEY) || "es",
  user: readJson(USER_KEY),
  token: sessionStorage.getItem(SESSION_KEY),
  route: "inicio",
  items: [],
  rawProducts: [],
  users: [],
  orders: [],
  mesasView: "map",
  mesaEstadoFilter: "",
  stockStateFilter: "",
  orderStateFilter: "",
  selectedMesaId: "",
  cart: [],
  orderNote: "",
  orderBanner: "",
  filter: "",
  sedeFilter: "",
  tipoFilter: "",
  cat: { sedes: [], tipos: [], proveedores: [] },
  idleTimer: null,
  lastActivityAt: 0,
};

function dict() {
  return I18N[state.lang] || I18N.es;
}
function fieldLabel(key) {
  return dict().fields[key] || key;
}
function navLabel(route) {
  return dict().nav[route] || route;
}
function setLang(lang) {
  state.lang = lang === "en" ? "en" : "es";
  localStorage.setItem(LANG_KEY, state.lang);
  document.documentElement.lang = state.lang;
  if (!state.token || !state.user) {
    renderLogin();
  } else if (state.user.debe_cambiar_password) {
    renderPasswordChange();
  } else {
    renderShell(state.route);
  }
}
function langSwitcherHtml() {
  return `<div class="lang-switch" role="group" aria-label="Language / Idioma"><button type="button" class="${state.lang === "es" ? "active" : ""}" data-set-lang="es">ES</button><button type="button" class="${state.lang === "en" ? "active" : ""}" data-set-lang="en">EN</button></div>`;
}
function bindLangSwitcher() {
  document.querySelectorAll("[data-set-lang]").forEach((btn) => {
    btn.addEventListener("click", () => setLang(btn.dataset.setLang));
  });
}

function readJson(key, store = sessionStorage) {
  try {
    return JSON.parse(store.getItem(key));
  } catch {
    return null;
  }
}
function readLocalMap(key) {
  return readJson(key, localStorage) || {};
}
function writeLocalMap(key, val) {
  try {
    localStorage.setItem(key, JSON.stringify(val));
  } catch {}
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

function formatValidationDetail(item) {
  const f = fieldLabel(item.campo || "");
  const raw = String(item.error || "");
  const isEn = state.lang === "en";
  const minMatch = raw.match(/at least (\d+) character/i);
  if (minMatch) {
    return isEn
      ? `${f}: must contain at least ${minMatch[1]} characters.`
      : `${f}: debe tener al menos ${minMatch[1]} caracteres.`;
  }
  const maxMatch = raw.match(/at most (\d+) character/i);
  if (maxMatch) {
    return isEn
      ? `${f}: cannot exceed ${maxMatch[1]} characters.`
      : `${f}: no puede superar ${maxMatch[1]} caracteres.`;
  }
  if (/greater than or equal to 0/i.test(raw)) {
    return isEn
      ? `${f}: must be 0 or a positive number.`
      : `${f}: debe ser un número mayor o igual a 0.`;
  }
  if (/greater than 0/i.test(raw)) {
    return isEn
      ? `${f}: must be greater than 0.`
      : `${f}: debe ser un número mayor que 0.`;
  }
  const leMatch = raw.match(/less than or equal to (\d+)/i);
  if (leMatch) {
    return isEn
      ? `${f}: maximum allowed value is ${leMatch[1]}.`
      : `${f}: el valor máximo permitido es ${leMatch[1]}.`;
  }
  if (/valid number|valid integer|valid decimal/i.test(raw)) {
    return isEn
      ? `${f}: please enter a valid numeric value.`
      : `${f}: debes ingresar un valor numérico válido.`;
  }
  if (/field required/i.test(raw)) {
    return isEn
      ? `${f}: this field is required.`
      : `${f}: este campo es obligatorio.`;
  }
  const clean = raw.replace(/^Value error,\s*/i, "");
  return f ? `${f}: ${clean}` : clean;
}

function message(error) {
  const code = error?.error?.codigo;
  const details = error?.error?.detalle;
  const langMap = ERROR_MESSAGES[state.lang] || ERROR_MESSAGES.es;

  if (code === "DATOS_INVALIDOS" && Array.isArray(details) && details.length) {
    const prefix =
      state.lang === "en"
        ? "Please review the following fields: "
        : "Por favor corrige los siguientes campos: ";
    return prefix + details.map(formatValidationDetail).join(" · ");
  }
  if (code && langMap[code]) {
    if (code === "STOCK_INSUFICIENTE" && error?.error?.mensaje) {
      return `${langMap[code]} (${error.error.mensaje})`;
    }
    return langMap[code];
  }
  return (
    error?.error?.mensaje ||
    error?.detail ||
    (state.lang === "en"
      ? "Could not complete the operation. Please check your connection and input data."
      : "No fue posible completar la operación. Verifica los datos ingresados e inténtalo de nuevo.")
  );
}

// Per-branch stock helper (keyed by product.id, which is unique per branch + code)
function getEffectiveStock(product) {
  const overrides = readLocalMap(LOCAL_STOCK_KEY);
  const saved = overrides[product.id];
  const stock =
    saved?.stock !== undefined
      ? Number(saved.stock)
      : product.stock !== undefined && product.stock !== null
        ? Number(product.stock)
        : 24;
  const stock_minimo =
    saved?.stock_minimo !== undefined
      ? Number(saved.stock_minimo)
      : product.stock_minimo !== undefined && product.stock_minimo !== null
        ? Number(product.stock_minimo)
        : 5;
  return { ...product, stock, stock_minimo };
}
function saveLocalStock(productId, stock, stock_minimo) {
  const overrides = readLocalMap(LOCAL_STOCK_KEY);
  overrides[productId] = { stock: Number(stock), stock_minimo: Number(stock_minimo) };
  writeLocalMap(LOCAL_STOCK_KEY, overrides);
}
function clearLocalMesaState(mesaId) {
  const overrides = readLocalMap(LOCAL_TABLES_KEY);
  if (overrides[mesaId] !== undefined) {
    delete overrides[mesaId];
    writeLocalMap(LOCAL_TABLES_KEY, overrides);
  }
}
function getEffectiveMesa(mesa) {
  const overrides = readLocalMap(LOCAL_TABLES_KEY);
  if (overrides[mesa.id]) {
    return { ...mesa, estado: overrides[mesa.id] };
  }
  return mesa;
}
function saveLocalMesaState(mesaId, estado) {
  const overrides = readLocalMap(LOCAL_TABLES_KEY);
  overrides[mesaId] = estado;
  writeLocalMap(LOCAL_TABLES_KEY, overrides);
}

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
function refOptions(ref, selected = "", placeholder = dict().common.selectOption) {
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

function resolveUserFullName(usernameOrName) {
  if (!usernameOrName) return "";
  if (state.user && state.user.usuario === usernameOrName) {
    return state.user.nombre || usernameOrName;
  }
  const found = (state.users || []).find(
    (u) => u.usuario === usernameOrName || u.nombre === usernameOrName,
  );
  return found ? found.nombre : usernameOrName;
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
    clearSession();
    throw Error(dict().sessionExpired);
  }
  if (!response.ok) throw Error(message(data));
  return data;
}

function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(USER_KEY);
  state = { ...state, token: null, user: null, cart: [] };
  clearTimeout(state.idleTimer);
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

  clearSession();
  renderLogin(dict().inactivityClosed);
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
document.addEventListener("touchstart", resetInactivityTimer, { passive: true });
document.addEventListener("wheel", resetInactivityTimer, { passive: true });

function renderLogin(note = "") {
  const d = dict();
  document.getElementById("app").innerHTML =
    `<main class="login-shell"><section class="container"><div class="login-top-row"><div class="brand"><span class="brand-mark">M</span><span>BAR DE MOE</span></div>${langSwitcherHtml()}</div><h1 class="heading">${esc(d.welcomeBack)}</h1><p class="login-kicker">${esc(d.brandSub)}</p><p class="subtle">${esc(d.loginPrompt)}</p>${note ? `<p class="error" role="alert">${esc(note)}</p>` : ""}<form class="form" id="login-form"><label>${esc(d.usernameLabel)}<input class="input" name="usuario" autocomplete="username" placeholder="${esc(d.usernamePlaceholder)}" required></label><label>${esc(d.passwordLabel)}<input class="input" name="password" type="password" autocomplete="current-password" placeholder="${esc(d.passwordPlaceholder)}" required></label><button class="login-button" id="login-submit" disabled>${esc(d.loginBtn)}</button></form><p class="agreement">${esc(d.loginFooter)}</p></section></main>`;
  bindLangSwitcher();
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
  const d = dict();
  const form = new FormData(event.target),
    submit = document.getElementById("login-submit");
  submit.disabled = true;
  submit.textContent = d.loggingInBtn;
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
  const d = dict();
  document.getElementById("app").innerHTML =
    `<main class="login-shell"><section class="container"><div class="login-top-row"><div class="brand"><span class="brand-mark">M</span><span>BAR DE MOE</span></div>${langSwitcherHtml()}</div><h1 class="heading">${esc(d.updatePassTitle)}</h1><p class="login-kicker">${esc(d.mandatoryChange)}</p><p class="subtle">${esc(d.updatePassPrompt)}</p>${note ? `<p class="error" role="alert">${esc(note)}</p>` : ""}<form class="form" id="password-form"><label>${esc(d.currentPassLabel)}<input class="input" name="actual" type="password" autocomplete="current-password" placeholder="${esc(d.currentPassLabel)}" required></label><label>${esc(d.newPassLabel)}<input class="input" name="nueva" type="password" autocomplete="new-password" placeholder="${esc(d.newPassLabel)}" minlength="8" required></label><button class="login-button">${esc(d.savePassBtn)}</button></form></section></main>`;
  bindLangSwitcher();
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
  const d = dict();
  state.route = route === "inicio" || allowed(route) ? route : "inicio";
  const links = (MENU[state.user.perfil] || [])
    .map(
      (item) =>
        `<button class="${item === state.route ? "active" : ""}" data-route="${item}">${esc(navLabel(item))}</button>`,
    )
    .join("");
  document.getElementById("app").innerHTML =
    `<div class="shell"><aside class="sidebar"><div class="sidebar-header"><div class="brand" id="go-home" style="cursor:pointer"><span class="brand-mark">M</span><span>BAR DE MOE</span></div>${langSwitcherHtml()}</div><nav class="nav" aria-label="Menu principal">${links}</nav><div class="user-mini"><div><strong>${esc(state.user.nombre)}</strong><br><span style="opacity:0.85">${esc(state.user.perfil)}</span></div><button class="ghost" id="logout" style="margin-top:10px">${esc(d.logoutBtn)}</button></div></aside><main class="content"><div class="workspace-frame" id="view"></div></main></div>`;
  bindLangSwitcher();
  document.getElementById("go-home")?.addEventListener("click", () => renderShell("inicio"));
  document
    .querySelectorAll("[data-route]")
    .forEach((button) =>
      button.addEventListener("click", () => {
        state.filter = "";
        state.error = "";
        state.orderBanner = "";
        renderShell(button.dataset.route);
      }),
    );
  document.getElementById("logout").addEventListener("click", logout);
  renderView();
}

async function logout() {
  try {
    await request("/auth/auth/logout", { method: "POST" });
  } catch {}
  clearSession();
  renderLogin(dict().sessionClosed);
}

function renderView() {
  if (state.route === "inicio") return home();
  if (state.route === "usuarios") return users();
  if (state.route === "inventario") return inventoryView();
  if (state.route === "mesas") return tablesMapView();
  if (state.route === "pedidos") return ordersPosView();
  if (RESOURCES[state.route]) return resource(state.route);
  const d = dict();
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">${esc(navLabel(state.route))}</p><h1>${esc(d.common.prepTitle)}</h1><p class="subtle">${esc(d.common.prepSub)}</p></div></div><section class="panel"><h2>${esc(d.common.authAccess)}</h2><p class="subtle">${esc(d.common.authAccessSub)}</p></section>`;
}

// ====================================================== HOME (Full Name displayed)
function home() {
  const d = dict();
  if (state.user.sede_id) {
    request(`/parametrizacion/sedes/${state.user.sede_id}`)
      .then((sede) => {
        const el = document.getElementById("home-sede");
        if (el) el.textContent = sede.nombre;
      })
      .catch(() => {});
  }
  document.getElementById("view").innerHTML =
    `<div class="dashboard-view"><div class="topbar"><div><p class="eyebrow">${esc(d.personalPanel)}</p><h1>${esc(d.hello)}, ${esc(state.user.nombre)}</h1></div></div><div class="profile-layout single-panel"><section class="panel profile-card"><h2>${esc(d.myInfo)}</h2><div class="profile-details"><div><span>${esc(d.fullName)}</span><strong>${esc(state.user.nombre)}</strong></div><div><span>${esc(d.idCard)}</span><strong>${esc(state.user.cedula)}</strong></div><div><span>${esc(d.usernameLabel)}</span><strong>${esc(state.user.usuario)}</strong></div><div><span>${esc(d.role)}</span><strong>${esc(state.user.perfil)}</strong></div><div><span>${esc(d.branch)}</span><strong id="home-sede">${state.user.sede_id ? `Sede #${state.user.sede_id}` : esc(d.allBranches)}</strong></div><div><span>${esc(d.status)}</span><strong><span class="badge active">${esc(state.user.estado)}</span></strong></div></div></section></div></div>`;
}

// Ensure every global product exists in every branch so branch inventory is always complete
async function ensureProductsInAllBranches(rawProducts) {
  if (!esAdmin() || !state.cat.sedes?.length || !rawProducts?.length) return rawProducts;
  const byCode = new Map();
  rawProducts.forEach((p) => {
    if (!byCode.has(p.codigo)) byCode.set(p.codigo, p);
  });
  let createdAny = false;
  for (const [codigo, template] of byCode.entries()) {
    for (const sede of state.cat.sedes) {
      const existsInSede = rawProducts.some(
        (p) => p.codigo === codigo && Number(p.sede_id) === Number(sede.id),
      );
      if (!existsInSede) {
        try {
          await request("/parametrizacion/productos", {
            method: "POST",
            body: JSON.stringify({
              codigo: template.codigo,
              nombre: template.nombre,
              sede_id: sede.id,
              tipo_producto_id: template.tipo_producto_id,
              proveedor_id: template.proveedor_id,
              valor_compra: template.valor_compra,
              valor_venta: template.valor_venta,
              stock: 24,
              stock_minimo: template.stock_minimo ?? 5,
            }),
          });
          createdAny = true;
        } catch {}
      }
    }
  }
  if (createdAny) {
    try {
      return await request("/parametrizacion/inventario?solo_activos=false");
    } catch {
      return await request("/parametrizacion/productos?solo_activos=false");
    }
  }
  return rawProducts;
}

// ====================================================== HU-012: INVENTARIO POR SEDE
async function inventoryView() {
  const d = dict();
  const sedeSelect = esAdmin()
    ? `<select id="inv-sede-filter" aria-label="${esc(d.fields.sede_id)}"><option value="">${esc(d.common.allBranchesFilter)}</option></select>`
    : "";
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">${esc(d.inventory.eyebrow)}</p><h1>${esc(d.inventory.title)}</h1></div></div><div class="stats" id="inv-stats"></div><section class="panel"><div class="toolbar"><input id="inv-search" placeholder="${esc(d.common.searchPlaceholder)}" aria-label="${esc(d.common.searchPlaceholder)}">${sedeSelect}<select id="inv-tipo-filter" aria-label="${esc(d.fields.tipo_producto_id)}"><option value="">${esc(d.common.allTypesFilter)}</option></select><select id="inv-state-filter"><option value="">${esc(d.inventory.allStockStates)}</option><option value="DISPONIBLE">${esc(d.inventory.inStock)}</option><option value="BAJO">${esc(d.inventory.lowStock)}</option><option value="AGOTADO">${esc(d.inventory.outOfStock)}</option></select><button class="ghost" id="inv-refresh">${esc(d.common.refresh)}</button></div><div id="inv-table"></div></section>`;

  document.getElementById("inv-search").addEventListener("input", (e) => {
    state.filter = e.target.value.toLowerCase();
    drawInventory();
  });
  document.getElementById("inv-sede-filter")?.addEventListener("change", (e) => {
    state.sedeFilter = e.target.value;
    drawInventory();
  });
  document.getElementById("inv-tipo-filter").addEventListener("change", (e) => {
    state.tipoFilter = e.target.value;
    drawInventory();
  });
  document.getElementById("inv-state-filter").addEventListener("change", (e) => {
    state.stockStateFilter = e.target.value;
    drawInventory();
  });
  document.getElementById("inv-refresh").addEventListener("click", loadInventory);
  await loadInventory();
}

async function loadInventory() {
  try {
    await loadCatalogs();
    let raw = [];
    try {
      raw = await request("/parametrizacion/inventario?solo_activos=false");
    } catch {
      raw = await request("/parametrizacion/productos?solo_activos=false");
    }
    raw = await ensureProductsInAllBranches(raw);
    state.items = raw.map(getEffectiveStock);
    state.error = "";
    const sedeEl = document.getElementById("inv-sede-filter");
    const tipoEl = document.getElementById("inv-tipo-filter");
    if (sedeEl) {
      sedeEl.innerHTML = refOptions("sedes", state.sedeFilter, dict().common.allBranchesFilter);
      sedeEl.value = state.sedeFilter;
    }
    if (tipoEl) {
      tipoEl.innerHTML = refOptions("tipos", state.tipoFilter, dict().common.allTypesFilter);
      tipoEl.value = state.tipoFilter;
    }
    drawInventory();
  } catch (error) {
    state.error = error.message;
    drawInventory();
  }
}

function stockLevel(item) {
  if ((item.stock ?? 0) <= 0) return "AGOTADO";
  if ((item.stock ?? 0) <= (item.stock_minimo ?? 5)) return "BAJO";
  return "DISPONIBLE";
}

function drawInventory() {
  const d = dict();
  const rows = (state.items || []).filter((item) => {
    const level = stockLevel(item);
    const text = `${item.codigo} ${item.nombre} ${refName("sedes", item.sede_id)} ${refName("tipos", item.tipo_producto_id)}`.toLowerCase();
    return (
      text.includes(state.filter) &&
      (!esAdmin() || !state.sedeFilter || String(item.sede_id) === state.sedeFilter) &&
      (!state.tipoFilter || String(item.tipo_producto_id) === state.tipoFilter) &&
      (!state.stockStateFilter || level === state.stockStateFilter)
    );
  });

  const totalRefs = rows.length;
  const totalUnits = rows.reduce((acc, r) => acc + Number(r.stock || 0), 0);
  const alerts = rows.filter((r) => stockLevel(r) !== "DISPONIBLE").length;

  const statsEl = document.getElementById("inv-stats");
  if (statsEl) {
    statsEl.innerHTML = `
      <div class="stat"><span>${esc(d.inventory.totalRefs)}</span><strong>${totalRefs}</strong></div>
      <div class="stat stat-ok"><span>${esc(d.inventory.totalUnits)}</span><strong>${totalUnits}</strong></div>
      <div class="stat ${alerts > 0 ? "stat-warn" : ""}"><span>${esc(d.inventory.lowStockAlerts)}</span><strong>${alerts}</strong></div>
    `;
  }

  const tableEl = document.getElementById("inv-table");
  if (!tableEl) return;

  if (state.error) {
    tableEl.innerHTML = `<p class="error">${esc(state.error)}</p>`;
    return;
  }
  if (!rows.length) {
    tableEl.innerHTML = `<div class="empty">${esc(d.common.noRecords)}</div>`;
    return;
  }

  tableEl.innerHTML = `<div class="table-wrap"><table><thead><tr>
    <th>${esc(d.fields.codigo)}</th>
    <th>${esc(d.fields.nombre)}</th>
    <th>${esc(d.fields.sede_id)}</th>
    <th>${esc(d.fields.tipo_producto_id)}</th>
    <th>${esc(d.fields.valor_venta)}</th>
    <th>${esc(d.inventory.stockCol)}</th>
    <th>${esc(d.inventory.minCol)}</th>
    <th>${esc(d.inventory.levelCol)}</th>
    <th>${esAdmin() ? esc(d.users.actionsCol) : ""}</th>
  </tr></thead><tbody>${rows
    .map((item) => {
      const level = stockLevel(item);
      const badgeClass =
        level === "DISPONIBLE" ? "active" : level === "BAJO" ? "warning" : "inactive";
      const badgeText =
        level === "DISPONIBLE"
          ? d.inventory.inStock
          : level === "BAJO"
            ? d.inventory.lowStock
            : d.inventory.outOfStock;
      const pct = Math.min(100, Math.round((Number(item.stock || 0) / 40) * 100));
      const fillClass = level === "DISPONIBLE" ? "ok" : level === "BAJO" ? "low" : "out";
      return `<tr>
        <td><strong>${esc(item.codigo)}</strong></td>
        <td>${esc(item.nombre)}</td>
        <td><span class="role-badge">${esc(refName("sedes", item.sede_id))}</span></td>
        <td>${esc(refName("tipos", item.tipo_producto_id))}</td>
        <td>$${Number(item.valor_venta).toLocaleString()}</td>
        <td><div class="stock-cell"><strong>${item.stock}</strong><div class="stock-bar-track"><div class="stock-bar-fill ${fillClass}" style="width:${pct}%"></div></div></div></td>
        <td>${item.stock_minimo}</td>
        <td><span class="badge ${badgeClass}">${esc(badgeText)}</span></td>
        <td>${esAdmin() ? `<button class="ghost adjust-stock btn-uniform" data-id="${item.id}">${esc(d.inventory.adjustBtn)}</button>` : ""}</td>
      </tr>`;
    })
    .join("")}</tbody></table></div>`;

  document.querySelectorAll(".adjust-stock").forEach((btn) =>
    btn.addEventListener("click", () => {
      const prod = state.items.find((i) => i.id === Number(btn.dataset.id));
      if (prod) openInventoryModal(prod);
    }),
  );
}

function openInventoryModal(prod) {
  const d = dict();
  document.body.insertAdjacentHTML(
    "beforeend",
    `<div class="modal-backdrop" id="modal"><section class="modal">
      <div class="topbar"><div><p class="eyebrow">${esc(prod.codigo)} · ${esc(refName("sedes", prod.sede_id))}</p><h2>${esc(d.inventory.modalTitle)}: ${esc(prod.nombre)}</h2></div><button class="ghost" id="close-modal">${esc(d.common.close)}</button></div>
      <form id="inv-form">
        <div class="form-grid">
          <label>${esc(d.inventory.moveType)}
            <select name="tipo" required>
              <option value="ENTRADA">${esc(d.inventory.typeEntry)}</option>
              <option value="SALIDA">${esc(d.inventory.typeExit)}</option>
              <option value="AJUSTE">${esc(d.inventory.typeSet)}</option>
            </select>
          </label>
          <label>${esc(d.inventory.qtyLabel)}
            <input name="cantidad" type="number" min="0" max="5000" value="12" required>
          </label>
          <label>${esc(d.inventory.minStockLabel)}
            <input name="stock_minimo" type="number" min="0" max="500" value="${prod.stock_minimo ?? 5}" required>
          </label>
          <label>${esc(d.inventory.reasonLabel)}
            <input name="motivo" maxlength="150" placeholder="${esc(d.inventory.reasonPlaceholder)}">
          </label>
        </div>
        <div id="form-error"></div>
        <div class="modal-actions">
          <button type="button" class="ghost" id="cancel-modal">${esc(d.common.cancel)}</button>
          <button class="primary">${esc(d.inventory.saveAdjust)}</button>
        </div>
      </form>
    </section></div>`,
  );
  const close = () => document.getElementById("modal")?.remove();
  document.getElementById("close-modal").addEventListener("click", close);
  document.getElementById("cancel-modal").addEventListener("click", close);
  document.getElementById("inv-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.target));
    const payload = {
      tipo: values.tipo,
      cantidad: Number(values.cantidad),
      stock_minimo: Number(values.stock_minimo),
      motivo: values.motivo || null,
    };
    try {
      try {
        const updated = await request(`/parametrizacion/inventario/${prod.id}/ajustar`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        saveLocalStock(prod.id, updated.stock, updated.stock_minimo);
      } catch {
        const cur = prod.stock ?? 24;
        let next = cur;
        if (payload.tipo === "ENTRADA") next = cur + payload.cantidad;
        else if (payload.tipo === "SALIDA") {
          if (payload.cantidad > cur) {
            throw Error(ERROR_MESSAGES[state.lang].STOCK_INSUFICIENTE);
          }
          next = cur - payload.cantidad;
        } else next = payload.cantidad;
        saveLocalStock(prod.id, next, payload.stock_minimo);
      }
      close();
      await loadInventory();
    } catch (error) {
      document.getElementById("form-error").innerHTML = `<p class="error">${esc(error.message)}</p>`;
    }
  });
}

// ====================================================== HU-013: MAPA DE MESAS DE LA SEDE (3xN Grid + Working Free Table + Equal Buttons)
const SVG_ATTRS = `class="icon-svg" width="14" height="14" style="width:14px;height:14px;min-width:14px;min-height:14px;flex-shrink:0;vertical-align:middle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"`;
const ICON_SVG = {
  grid: `<svg ${SVG_ATTRS}><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>`,
  list: `<svg ${SVG_ATTRS}><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/></svg>`,
  pin: `<svg ${SVG_ATTRS}><path d="M12 21s-6-5.33-6-11a6 6 0 1 1 12 0c0 5.67-6 11-6 11z"/><circle cx="12" cy="10" r="2.2"/></svg>`,
  users: `<svg ${SVG_ATTRS}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  note: `<svg ${SVG_ATTRS}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/></svg>`,
};

async function tablesMapView() {
  const d = dict();
  const sedeSelect = esAdmin()
    ? `<select id="mesa-sede-filter" aria-label="${esc(d.fields.sede_id)}"><option value="">${esc(d.common.allBranchesFilter)}</option></select>`
    : "";
  document.getElementById("view").innerHTML =
    `<div class="topbar">
      <div><p class="eyebrow">${esc(d.tables.eyebrow)}</p><h1>${esc(d.tables.title)}</h1></div>
      <div class="topbar-actions">
        <button type="button" role="switch" class="view-toggle-switch" id="view-switch-toggle" data-mode="${state.mesasView}" aria-checked="${state.mesasView === "table"}" aria-label="${esc(d.tables.title)}" title="${esc(state.mesasView === "map" ? d.tables.mapView : d.tables.tableView)}">
          <span class="switch-thumb" aria-hidden="true"></span>
          <span class="switch-side" data-target="map">${ICON_SVG.grid}</span>
          <span class="switch-side" data-target="table">${ICON_SVG.list}</span>
        </button>
        ${esAdmin() ? `<button class="primary" id="new-mesa-btn">${esc(d.tables.newTableBtn)}</button>` : ""}
      </div>
    </div>
    <div class="stats" id="mesas-stats"></div>
    <section class="panel">
      <div class="toolbar">
        <input id="mesa-search" placeholder="${esc(d.tables.searchTable)}" aria-label="${esc(d.tables.searchTable)}">
        ${sedeSelect}
        <select id="mesa-estado-filter">
          <option value="">${esc(d.tables.allStates)}</option>
          <option value="LIBRE">${esc(d.tables.free)}</option>
          <option value="OCUPADA">${esc(d.tables.occupied)}</option>
        </select>
        <button class="ghost" id="mesa-refresh">${esc(d.common.refresh)}</button>
      </div>
      <div id="mesas-container"></div>
    </section>`;

  const switchEl = document.getElementById("view-switch-toggle");
  switchEl.addEventListener("click", (e) => {
    const clickedSide = e.target.closest(".switch-side")?.dataset.target;
    if (clickedSide && clickedSide !== state.mesasView) {
      state.mesasView = clickedSide;
    } else {
      state.mesasView = state.mesasView === "map" ? "table" : "map";
    }
    switchEl.dataset.mode = state.mesasView;
    switchEl.setAttribute("aria-checked", String(state.mesasView === "table"));
    drawTablesMap();
  });
  document.getElementById("new-mesa-btn")?.addEventListener("click", () => form("mesas"));
  document.getElementById("mesa-search").addEventListener("input", (e) => {
    state.filter = e.target.value.toLowerCase();
    drawTablesMap();
  });
  document.getElementById("mesa-sede-filter")?.addEventListener("change", (e) => {
    state.sedeFilter = e.target.value;
    drawTablesMap();
  });
  document.getElementById("mesa-estado-filter").addEventListener("change", (e) => {
    state.mesaEstadoFilter = e.target.value;
    drawTablesMap();
  });
  document.getElementById("mesa-refresh").addEventListener("click", loadTablesMap);

  await loadTablesMap();
}

async function fetchOrdersList() {
  try {
    const apiOrders = await request("/parametrizacion/pedidos");
    return apiOrders;
  } catch {
    return readJson(LOCAL_ORDERS_KEY, localStorage) || [];
  }
}

async function loadTablesMap() {
  try {
    await loadCatalogs();
    const [rawMesas, orders] = await Promise.all([
      request("/parametrizacion/mesas"),
      fetchOrdersList(),
    ]);
    state.orders = orders;
    state.items = rawMesas.map(getEffectiveMesa);
    state.error = "";
    const sedeEl = document.getElementById("mesa-sede-filter");
    if (sedeEl) {
      sedeEl.innerHTML = refOptions("sedes", state.sedeFilter, dict().common.allBranchesFilter);
      sedeEl.value = state.sedeFilter;
    }
    const estEl = document.getElementById("mesa-estado-filter");
    if (estEl) estEl.value = state.mesaEstadoFilter;
    drawTablesMap();
  } catch (error) {
    state.error = error.message;
    drawTablesMap();
  }
}

function drawTablesMap() {
  const d = dict();
  const rows = (state.items || []).filter((m) => {
    const text = `#${m.numero} mesa ${m.numero} ${refName("sedes", m.sede_id)} ${m.estado}`.toLowerCase();
    return (
      text.includes(state.filter) &&
      (!esAdmin() || !state.sedeFilter || String(m.sede_id) === state.sedeFilter) &&
      (!state.mesaEstadoFilter || m.estado === state.mesaEstadoFilter)
    );
  });

  const activeRows = rows.filter((m) => m.activa !== false);
  const freeCount = activeRows.filter((m) => m.estado === "LIBRE").length;
  const occupiedCount = activeRows.filter((m) => m.estado === "OCUPADA").length;

  const statsEl = document.getElementById("mesas-stats");
  if (statsEl) {
    statsEl.innerHTML = `
      <div class="stat"><span>${esc(d.tables.totalTables)}</span><strong>${activeRows.length}</strong></div>
      <div class="stat stat-ok"><span>${esc(d.tables.freeTables)}</span><strong>${freeCount}</strong></div>
      <div class="stat ${occupiedCount > 0 ? "stat-warn" : ""}"><span>${esc(d.tables.occupiedTables)}</span><strong>${occupiedCount}</strong></div>
    `;
  }

  const container = document.getElementById("mesas-container");
  if (!container) return;
  if (state.error) {
    container.innerHTML = `<p class="error">${esc(state.error)}</p>`;
    return;
  }
  if (!rows.length) {
    container.innerHTML = `<div class="empty">${esc(d.common.noRecords)}</div>`;
    return;
  }

  if (state.mesasView === "table") {
    container.innerHTML = `<div class="table-wrap"><table><thead><tr>
      <th>${esc(d.fields.sede_id)}</th>
      <th>${esc(d.fields.numero)}</th>
      <th>${esc(d.fields.capacidad)}</th>
      <th>${esc(d.status)}</th>
      <th>${esc(d.users.actionsCol)}</th>
    </tr></thead><tbody>${rows
      .map(
        (m) => `<tr>
        <td>${esc(refName("sedes", m.sede_id))}</td>
        <td><strong>#${m.numero}</strong></td>
        <td>${m.capacidad} ${esc(d.tables.people)}</td>
        <td><span class="badge ${m.estado === "LIBRE" ? "active" : "warning"}">${esc(m.estado === "LIBRE" ? d.tables.free : d.tables.occupied)}</span></td>
        <td><div class="user-actions">
          <button class="primary go-order-mesa btn-uniform" data-id="${m.id}">${esc(m.estado === "LIBRE" ? d.tables.takeOrder : d.tables.viewOrder)}</button>
          <button class="ghost toggle-mesa-state btn-uniform" data-id="${m.id}" data-next="${m.estado === "LIBRE" ? "OCUPADA" : "LIBRE"}">${esc(m.estado === "LIBRE" ? d.tables.markOccupied : d.tables.markFree)}</button>
          ${esAdmin() ? `<button class="ghost edit-mesa btn-uniform" data-id="${m.id}">${esc(d.common.edit)}</button>` : ""}
        </div></td>
      </tr>`,
      )
      .join("")}</tbody></table></div>`;
  } else {
    container.innerHTML = `<div class="mesas-grid">${rows
      .map((m) => {
        const isFree = m.estado === "LIBRE";
        const cardClass = !m.activa ? "inactiva" : isFree ? "libre" : "ocupada";
        const activeOrder = isFree
          ? null
          : (state.orders || []).find(
              (o) =>
                o.mesa_id === m.id &&
                (o.estado === "ABIERTO" || o.estado === "ENTREGADO"),
            );
        const itemsCount = activeOrder
          ? (activeOrder.detalles || []).reduce((a, b) => a + Number(b.cantidad || 0), 0)
          : 0;
        const orderBadge = activeOrder
          ? `<div class="mesa-order-pill">${esc(
              d.tables.activeOrderBadge
                .replace("{id}", activeOrder.id)
                .replace("{total}", Number(activeOrder.total).toLocaleString())
                .replace("{items}", itemsCount),
            )}</div>`
          : "";
        return `<article class="mesa-card ${cardClass}">
          <div>
            <div class="mesa-card-header">
              <span class="mesa-number">Mesa #${m.numero}</span>
              <span class="badge ${!m.activa ? "inactive" : isFree ? "active" : "warning"}">${esc(!m.activa ? d.common.inactive : isFree ? d.tables.free : d.tables.occupied)}</span>
            </div>
            <div class="mesa-meta" style="margin-top:8px">
              <span>${ICON_SVG.pin} ${esc(refName("sedes", m.sede_id))}</span>
              <span>${ICON_SVG.users} ${esc(d.tables.capacity)}: <strong>${m.capacidad} ${esc(d.tables.people)}</strong></span>
            </div>
            ${orderBadge ? `<div style="margin-top:10px">${orderBadge}</div>` : ""}
          </div>
          <div class="mesa-card-actions">
            ${
              m.activa
                ? `<button type="button" class="primary go-order-mesa" data-id="${m.id}">${esc(isFree ? d.tables.takeOrder : d.tables.viewOrder)}</button>
                   <button type="button" class="ghost toggle-mesa-state" data-id="${m.id}" data-next="${isFree ? "OCUPADA" : "LIBRE"}">${esc(isFree ? d.tables.markOccupied : d.tables.markFree)}</button>`
                : ""
            }
            ${esAdmin() ? `<button type="button" class="ghost edit-mesa" data-id="${m.id}">${esc(d.common.edit)}</button>` : ""}
          </div>
        </article>`;
      })
      .join("")}</div>`;
  }

  document.querySelectorAll(".go-order-mesa").forEach((btn) =>
    btn.addEventListener("click", () => {
      state.selectedMesaId = String(btn.dataset.id);
      renderShell("pedidos");
    }),
  );
  document.querySelectorAll(".toggle-mesa-state").forEach((btn) =>
    btn.addEventListener("click", () =>
      changeMesaState(Number(btn.dataset.id), btn.dataset.next),
    ),
  );
  document.querySelectorAll(".edit-mesa").forEach((btn) =>
    btn.addEventListener("click", () =>
      form(
        "mesas",
        state.items.find((item) => item.id === Number(btn.dataset.id)),
      ),
    ),
  );
}

async function changeMesaState(mesaId, nuevoEstado) {
  try {
    let backendUpdated = false;
    try {
      await request(`/parametrizacion/mesas/${mesaId}/estado`, {
        method: "POST",
        body: JSON.stringify({ estado: nuevoEstado }),
      });
      backendUpdated = true;
    } catch {
      if (esAdmin()) {
        try {
          await request(`/parametrizacion/mesas/${mesaId}`, {
            method: "PATCH",
            body: JSON.stringify({ estado: nuevoEstado }),
          });
          backendUpdated = true;
        } catch {}
      }
    }

    if (nuevoEstado === "LIBRE") {
      const openOrders = (state.orders || []).filter(
        (o) =>
          o.mesa_id === mesaId &&
          (o.estado === "ABIERTO" || o.estado === "ENTREGADO"),
      );
      for (const ord of openOrders) {
        try {
          await request(`/parametrizacion/pedidos/${ord.id}/estado`, {
            method: "POST",
            body: JSON.stringify({ estado: "CERRADO" }),
          });
        } catch {}
      }
      const localOrders = readJson(LOCAL_ORDERS_KEY, localStorage) || [];
      localOrders.forEach((o) => {
        if (o.mesa_id === mesaId && (o.estado === "ABIERTO" || o.estado === "ENTREGADO")) {
          o.estado = "CERRADO";
        }
      });
      writeLocalMap(LOCAL_ORDERS_KEY, localOrders);
    }

    if (backendUpdated) {
      clearLocalMesaState(mesaId);
    } else {
      saveLocalMesaState(mesaId, nuevoEstado);
    }
    await loadTablesMap();
  } catch (error) {
    state.error = error.message;
    drawTablesMap();
  }
}

// ====================================================== HU-014: PANTALLA DE TOMA DE PEDIDO (List View)
async function ordersPosView() {
  const d = dict();
  document.getElementById("view").innerHTML =
    `<div class="topbar">
      <div><p class="eyebrow">${esc(d.orders.eyebrow)}</p><h1>${esc(d.orders.title)}</h1></div>
      <div class="topbar-actions">
        <button class="ghost" id="go-map-from-pos">← ${esc(d.nav.mesas)}</button>
        <button class="ghost" id="pos-refresh">${esc(d.common.refresh)}</button>
      </div>
    </div>
    <div id="pos-banner"></div>
    <div class="pos-layout">
      <section class="panel">
        <h2>${esc(d.orders.catalogTitle)}</h2>
        <div class="toolbar">
          <select id="pos-mesa-select" aria-label="${esc(d.orders.selectTableLabel)}" style="max-width:340px;font-weight:800"></select>
          <input id="pos-search" placeholder="${esc(d.orders.searchProdPlaceholder)}" aria-label="${esc(d.orders.searchProdPlaceholder)}">
          <select id="pos-tipo-filter"><option value="">${esc(d.common.allTypesFilter)}</option></select>
        </div>
        <div class="catalog-list-wrap" id="pos-catalog"></div>
      </section>
      <aside class="order-ticket">
        <h2>${esc(d.orders.ticketTitle)}</h2>
        <div id="pos-ticket-body"></div>
      </aside>
    </div>
    <section class="panel">
      <div class="topbar" style="margin-bottom:12px">
        <h2>${esc(d.orders.historyTitle)}</h2>
        <select id="pos-order-state-filter">
          <option value="">${esc(d.orders.allOrderStates)}</option>
          <option value="ABIERTO">${esc(d.orders.stateOpen)}</option>
          <option value="ENTREGADO">${esc(d.orders.stateDelivered)}</option>
          <option value="CERRADO">${esc(d.orders.stateClosed)}</option>
        </select>
      </div>
      <div id="pos-orders-table"></div>
    </section>`;

  document.getElementById("go-map-from-pos").addEventListener("click", () => renderShell("mesas"));
  document.getElementById("pos-refresh").addEventListener("click", loadOrdersPos);
  document.getElementById("pos-mesa-select").addEventListener("change", (e) => {
    const newMesaId = e.target.value;
    const prevMesa = (state.mesasList || []).find((m) => String(m.id) === String(state.selectedMesaId));
    const nextMesa = (state.mesasList || []).find((m) => String(m.id) === String(newMesaId));
    if (prevMesa && nextMesa && prevMesa.sede_id !== nextMesa.sede_id) {
      state.cart = [];
    }
    state.selectedMesaId = newMesaId;
    drawOrdersPos();
  });
  document.getElementById("pos-search").addEventListener("input", (e) => {
    state.filter = e.target.value.toLowerCase();
    drawOrdersPos();
  });
  document.getElementById("pos-tipo-filter").addEventListener("change", (e) => {
    state.tipoFilter = e.target.value;
    drawOrdersPos();
  });
  document.getElementById("pos-order-state-filter").addEventListener("change", (e) => {
    state.orderStateFilter = e.target.value;
    drawOrdersHistory();
  });

  await loadOrdersPos();
}

async function loadOrdersPos() {
  try {
    await loadCatalogs();
    let rawProducts = [];
    try {
      rawProducts = await request("/parametrizacion/inventario?solo_activos=true");
    } catch {
      rawProducts = await request("/parametrizacion/productos?solo_activos=true");
    }
    rawProducts = await ensureProductsInAllBranches(rawProducts);
    if (esAdmin() && !state.users.length) {
      try {
        state.users = await request("/auth/usuarios");
      } catch {}
    }
    const [rawMesas, orders] = await Promise.all([
      request("/parametrizacion/mesas"),
      fetchOrdersList(),
    ]);
    state.items = rawProducts.filter((p) => p.activo !== false).map(getEffectiveStock);
    state.mesasList = rawMesas.map(getEffectiveMesa).filter((m) => m.activa !== false);
    state.orders = orders;

    if (!state.selectedMesaId && state.mesasList.length) {
      state.selectedMesaId = String(state.mesasList[0].id);
    }

    const tipoEl = document.getElementById("pos-tipo-filter");
    if (tipoEl) {
      tipoEl.innerHTML = refOptions("tipos", state.tipoFilter, dict().common.allTypesFilter);
      tipoEl.value = state.tipoFilter;
    }

    drawOrdersPos();
    drawOrdersHistory();
  } catch (error) {
    state.error = error.message;
    drawOrdersPos();
  }
}

function drawOrdersPos() {
  const d = dict();
  const bannerEl = document.getElementById("pos-banner");
  if (bannerEl) {
    bannerEl.innerHTML = state.error
      ? `<p class="error">${esc(state.error)}</p>`
      : state.orderBanner
        ? `<p class="success-note">${esc(state.orderBanner)}</p>`
        : "";
  }

  const mesaSelect = document.getElementById("pos-mesa-select");
  const selectedMesa = (state.mesasList || []).find(
    (m) => String(m.id) === String(state.selectedMesaId),
  );
  if (mesaSelect) {
    mesaSelect.innerHTML =
      `<option value="">${esc(d.orders.selectTablePrompt)}</option>` +
      (state.mesasList || [])
        .map(
          (m) =>
            `<option value="${m.id}" ${String(m.id) === String(state.selectedMesaId) ? "selected" : ""}>Mesa #${m.numero} · ${esc(refName("sedes", m.sede_id))} (${m.estado === "LIBRE" ? d.tables.free : d.tables.occupied})</option>`,
        )
        .join("");
  }

  const targetSedeId = selectedMesa ? selectedMesa.sede_id : state.user?.sede_id;
  const catalog = (state.items || []).filter((p) => {
    const matchSede = !targetSedeId || p.sede_id === Number(targetSedeId);
    const matchTipo = !state.tipoFilter || String(p.tipo_producto_id) === state.tipoFilter;
    const matchText = `${p.codigo} ${p.nombre}`.toLowerCase().includes(state.filter);
    return matchSede && matchTipo && matchText;
  });

  // Render products as a clean List / Table (not a grid)
  const catalogEl = document.getElementById("pos-catalog");
  if (catalogEl) {
    catalogEl.innerHTML = catalog.length
      ? `<table><thead><tr>
          <th>${esc(d.fields.codigo)}</th>
          <th>${esc(d.fields.nombre)}</th>
          <th>${esc(d.fields.tipo_producto_id)}</th>
          <th>${esc(d.orders.availableLabel)}</th>
          <th>${esc(d.fields.valor_venta)}</th>
          <th></th>
        </tr></thead><tbody>${catalog
          .map((p) => {
            const inCart = state.cart.find((c) => c.producto_id === p.id)?.cantidad || 0;
            const remaining = Math.max(0, Number(p.stock || 0) - inCart);
            const isOut = remaining <= 0;
            return `<tr class="${isOut ? "out-of-stock" : ""}">
              <td><span class="role-badge">${esc(p.codigo)}</span></td>
              <td><strong>${esc(p.nombre)}</strong></td>
              <td>${esc(refName("tipos", p.tipo_producto_id))}</td>
              <td><span class="badge ${remaining > (p.stock_minimo ?? 5) ? "active" : remaining > 0 ? "warning" : "inactive"}">${remaining}</span></td>
              <td><strong>$${Number(p.valor_venta).toLocaleString()}</strong></td>
              <td style="text-align:right">
                <button type="button" class="primary add-to-cart btn-uniform" data-id="${p.id}" ${isOut ? "disabled" : ""}>${esc(isOut ? d.orders.outBtn : d.orders.addBtn)}</button>
              </td>
            </tr>`;
          })
          .join("")}</tbody></table>`
      : `<div class="empty">${esc(d.common.noRecords)}</div>`;

    document.querySelectorAll(".add-to-cart").forEach((btn) =>
      btn.addEventListener("click", () => addToCart(Number(btn.dataset.id))),
    );
  }

  const ticketEl = document.getElementById("pos-ticket-body");
  if (!ticketEl) return;

  if (!selectedMesa) {
    ticketEl.innerHTML = `<p class="subtle">${esc(d.orders.noTableSelected)}</p>`;
    return;
  }

  const total = state.cart.reduce(
    (sum, item) => sum + item.cantidad * Number(item.valor_venta),
    0,
  );

  ticketEl.innerHTML = `
    <div style="margin-bottom:10px;padding:10px 12px;border-radius:14px;background:var(--cream-surface);border:1px solid var(--cream-border)">
      <strong>Mesa #${selectedMesa.numero}</strong> · ${esc(refName("sedes", selectedMesa.sede_id))}
      <span class="badge ${selectedMesa.estado === "LIBRE" ? "active" : "warning"}" style="float:right">${esc(selectedMesa.estado === "LIBRE" ? d.tables.free : d.tables.occupied)}</span>
    </div>
    ${
      state.cart.length
        ? `<div class="cart-list">${state.cart
            .map(
              (c) => `<div class="cart-item">
                <div>
                  <strong>${esc(c.nombre)}</strong>
                  <div class="subtle" style="font-size:0.76rem">$${Number(c.valor_venta).toLocaleString()} × ${c.cantidad} = <strong>$${(c.cantidad * Number(c.valor_venta)).toLocaleString()}</strong></div>
                </div>
                <div class="qty-controls">
                  <button type="button" class="qty-btn cart-dec" data-id="${c.producto_id}">-</button>
                  <strong>${c.cantidad}</strong>
                  <button type="button" class="qty-btn cart-inc" data-id="${c.producto_id}">+</button>
                </div>
              </div>`,
            )
            .join("")}</div>`
        : `<p class="subtle" style="margin:18px 0">${esc(d.orders.emptyCart)}</p>`
    }
    <label style="display:grid;gap:6px;font-size:0.8rem;font-weight:700;margin-top:10px">
      ${esc(d.orders.notesLabel)}
      <input id="pos-order-note" value="${esc(state.orderNote)}" placeholder="${esc(d.orders.notesPlaceholder)}" style="padding:10px 14px;border-radius:14px;border:1px solid var(--cream-border);background:var(--cream-input)">
    </label>
    <div class="order-total-row">
      <span>${esc(d.orders.totalLabel)}</span>
      <span>$${total.toLocaleString()}</span>
    </div>
    <div style="display:flex;gap:8px;margin-top:14px">
      <button type="button" class="ghost" id="clear-cart-btn" ${!state.cart.length ? "disabled" : ""}>${esc(d.orders.clearCartBtn)}</button>
      <button type="button" class="primary" id="submit-order-btn" style="flex:1" ${!state.cart.length ? "disabled" : ""}>${esc(d.orders.confirmBtn)}</button>
    </div>
  `;

  document.getElementById("pos-order-note")?.addEventListener("input", (e) => {
    state.orderNote = e.target.value;
  });
  document.querySelectorAll(".cart-inc").forEach((btn) =>
    btn.addEventListener("click", () => addToCart(Number(btn.dataset.id))),
  );
  document.querySelectorAll(".cart-dec").forEach((btn) =>
    btn.addEventListener("click", () => decFromCart(Number(btn.dataset.id))),
  );
  document.getElementById("clear-cart-btn")?.addEventListener("click", () => {
    state.cart = [];
    state.error = "";
    drawOrdersPos();
  });
  document.getElementById("submit-order-btn")?.addEventListener("click", submitOrder);
}

function addToCart(productId) {
  const d = dict();
  const prod = (state.items || []).find((p) => p.id === productId);
  if (!prod) return;
  const existing = state.cart.find((c) => c.producto_id === productId);
  const currentQty = existing ? existing.cantidad : 0;
  if (currentQty + 1 > Number(prod.stock || 0)) {
    state.error = d.orders.stockLimitError
      .replace("{name}", prod.nombre)
      .replace("{stock}", prod.stock);
    drawOrdersPos();
    return;
  }
  state.error = "";
  state.orderBanner = "";
  if (existing) {
    existing.cantidad += 1;
  } else {
    state.cart.push({
      producto_id: prod.id,
      codigo: prod.codigo,
      nombre: prod.nombre,
      valor_venta: Number(prod.valor_venta),
      cantidad: 1,
    });
  }
  drawOrdersPos();
}

function decFromCart(productId) {
  const idx = state.cart.findIndex((c) => c.producto_id === productId);
  if (idx === -1) return;
  state.error = "";
  if (state.cart[idx].cantidad > 1) {
    state.cart[idx].cantidad -= 1;
  } else {
    state.cart.splice(idx, 1);
  }
  drawOrdersPos();
}

async function submitOrder() {
  const d = dict();
  if (!state.selectedMesaId) {
    state.error = d.orders.selectTableError;
    drawOrdersPos();
    return;
  }
  if (!state.cart.length) {
    state.error = d.orders.emptyCartError;
    drawOrdersPos();
    return;
  }
  const selectedMesa = (state.mesasList || []).find(
    (m) => String(m.id) === String(state.selectedMesaId),
  );
  const payload = {
    mesa_id: Number(state.selectedMesaId),
    mesero_nombre: state.user?.nombre || state.user?.usuario,
    observaciones: state.orderNote || null,
    items: state.cart.map((c) => ({
      producto_id: c.producto_id,
      cantidad: c.cantidad,
    })),
  };

  try {
    let createdOrder = null;
    try {
      createdOrder = await request("/parametrizacion/pedidos", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      state.cart.forEach((c) => {
        const prod = state.items.find((p) => p.id === c.producto_id);
        if (prod) {
          saveLocalStock(prod.id, Math.max(0, prod.stock - c.cantidad), prod.stock_minimo);
        }
      });
      clearLocalMesaState(payload.mesa_id);
    } catch (apiErr) {
      if (/No existe|404|Not Found/i.test(apiErr.message)) {
        const localOrders = readJson(LOCAL_ORDERS_KEY, localStorage) || [];
        const total = state.cart.reduce((s, c) => s + c.cantidad * c.valor_venta, 0);
        createdOrder = {
          id: (localOrders[0]?.id || 100) + 1,
          sede_id: selectedMesa?.sede_id || state.user?.sede_id || 1,
          mesa_id: payload.mesa_id,
          mesero: state.user?.nombre || state.user?.usuario || "Mesero",
          estado: "ABIERTO",
          observaciones: payload.observaciones,
          total,
          creado_en: new Date().toISOString(),
          detalles: state.cart.map((c, idx) => ({
            id: idx + 1,
            producto_id: c.producto_id,
            codigo_producto: c.codigo,
            nombre_producto: c.nombre,
            cantidad: c.cantidad,
            precio_unitario: c.valor_venta,
            subtotal: c.cantidad * c.valor_venta,
          })),
        };
        localOrders.unshift(createdOrder);
        writeLocalMap(LOCAL_ORDERS_KEY, localOrders);
        state.cart.forEach((c) => {
          const prod = state.items.find((p) => p.id === c.producto_id);
          if (prod) {
            saveLocalStock(prod.id, Math.max(0, prod.stock - c.cantidad), prod.stock_minimo);
          }
        });
        saveLocalMesaState(payload.mesa_id, "OCUPADA");
      } else {
        throw apiErr;
      }
    }

    state.cart = [];
    state.orderNote = "";
    state.error = "";
    state.orderBanner = d.orders.orderCreatedSuccess.replace("{id}", createdOrder.id);
    await loadOrdersPos();
  } catch (error) {
    state.error = error.message;
    drawOrdersPos();
  }
}

function drawOrdersHistory() {
  const d = dict();
  const tableEl = document.getElementById("pos-orders-table");
  if (!tableEl) return;

  const rows = (state.orders || []).filter(
    (o) => !state.orderStateFilter || o.estado === state.orderStateFilter,
  );

  if (!rows.length) {
    tableEl.innerHTML = `<div class="empty">${esc(d.common.noRecords)}</div>`;
    return;
  }

  const stateBadge = (st) => {
    if (st === "ABIERTO") return `<span class="badge warning">${esc(d.orders.stateOpen)}</span>`;
    if (st === "ENTREGADO") return `<span class="badge active">${esc(d.orders.stateDelivered)}</span>`;
    if (st === "CERRADO") return `<span class="role-badge">${esc(d.orders.stateClosed)}</span>`;
    return `<span class="badge inactive">${esc(d.orders.stateCancelled)}</span>`;
  };

  tableEl.innerHTML = `<div class="table-wrap"><table><thead><tr>
    <th>${esc(d.orders.colOrder)}</th>
    <th>${esc(d.orders.colTable)}</th>
    <th>${esc(d.fields.sede_id)}</th>
    <th>${esc(d.orders.colWaiter)}</th>
    <th>${esc(d.orders.colItems)}</th>
    <th>${esc(d.orders.colTotal)}</th>
    <th>${esc(d.orders.colState)}</th>
    <th>${esc(d.orders.colActions)}</th>
  </tr></thead><tbody>${rows
    .map((o) => {
      const mesaObj = (state.mesasList || []).find((m) => m.id === o.mesa_id);
      const mesaLabel = mesaObj ? `Mesa #${mesaObj.numero}` : `Mesa #${o.mesa_id}`;
      const summary = (o.detalles || [])
        .map((det) => `${det.cantidad}x ${det.nombre_producto}`)
        .join(", ");
      const canOperate = o.estado === "ABIERTO" || o.estado === "ENTREGADO";
      return `<tr>
        <td><strong>#${o.id}</strong></td>
        <td>${esc(mesaLabel)}</td>
        <td>${esc(refName("sedes", o.sede_id))}</td>
        <td><strong>${esc(resolveUserFullName(o.mesero))}</strong></td>
        <td>${esc(summary)}${o.observaciones ? `<div class="subtle" style="font-size:0.74rem;display:flex;align-items:center;gap:4px;margin-top:3px">${ICON_SVG.note} <span>${esc(o.observaciones)}</span></div>` : ""}</td>
        <td><strong>$${Number(o.total).toLocaleString()}</strong></td>
        <td>${stateBadge(o.estado)}</td>
        <td><div class="user-actions">
          ${o.estado === "ABIERTO" ? `<button class="ghost order-state-btn btn-uniform" data-id="${o.id}" data-state="ENTREGADO">${esc(d.orders.deliverBtn)}</button>` : ""}
          ${canOperate ? `<button class="ghost activate order-state-btn btn-uniform" data-id="${o.id}" data-state="CERRADO">${esc(d.orders.closeOrderBtn)}</button>` : ""}
        </div></td>
      </tr>`;
    })
    .join("")}</tbody></table></div>`;

  document.querySelectorAll(".order-state-btn").forEach((btn) =>
    btn.addEventListener("click", () =>
      updateOrderState(Number(btn.dataset.id), btn.dataset.state),
    ),
  );
}

async function updateOrderState(orderId, nextState) {
  try {
    const targetOrder = (state.orders || []).find((o) => o.id === orderId);
    try {
      await request(`/parametrizacion/pedidos/${orderId}/estado`, {
        method: "POST",
        body: JSON.stringify({ estado: nextState }),
      });
      if (targetOrder && (nextState === "CERRADO" || nextState === "CANCELADO")) {
        clearLocalMesaState(targetOrder.mesa_id);
      }
    } catch {
      const localOrders = readJson(LOCAL_ORDERS_KEY, localStorage) || [];
      const target = localOrders.find((o) => o.id === orderId);
      if (target) {
        if (nextState === "CANCELADO" && target.estado !== "CANCELADO") {
          (target.detalles || []).forEach((det) => {
            const prod = state.items.find((p) => p.id === det.producto_id);
            if (prod) {
              saveLocalStock(prod.id, (prod.stock || 0) + det.cantidad, prod.stock_minimo);
            }
          });
        }
        target.estado = nextState;
        if (nextState === "CERRADO" || nextState === "CANCELADO") {
          saveLocalMesaState(target.mesa_id, "LIBRE");
        }
        writeLocalMap(LOCAL_ORDERS_KEY, localOrders);
      }
    }
    await loadOrdersPos();
  } catch (error) {
    state.error = error.message;
    drawOrdersPos();
  }
}

// ====================================================== USUARIOS (Full CRUD + Full Names)
async function users() {
  const d = dict();
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">${esc(d.common.security)}</p><h1>${esc(d.users.title)}</h1></div><div class="topbar-actions"><button class="primary" id="new-user">${esc(d.users.newBtn)}</button></div></div><section class="panel"><div class="toolbar"><input id="user-search" placeholder="${esc(d.users.searchPlaceholder)}" aria-label="${esc(d.users.searchPlaceholder)}"><button class="ghost" id="refresh-users">${esc(d.common.refresh)}</button></div><div id="users-table"></div></section>`;
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
  const d = dict();
  const usersList = (state.users || []).filter((item) =>
    `${item.cedula} ${item.nombre} ${item.usuario} ${item.perfil}`
      .toLowerCase()
      .includes(state.filter),
  );
  document.getElementById("users-table").innerHTML = state.error
    ? `<p class="error">${esc(state.error)}</p>`
    : usersList.length
      ? `<div class="table-wrap"><table><thead><tr>
          <th>${esc(d.fullName)}</th>
          <th>${esc(d.fields.cedula)}</th>
          <th>${esc(d.fields.usuario)}</th>
          <th>${esc(d.fields.perfil)}</th>
          <th>${esc(d.fields.sede_id)}</th>
          <th>${esc(d.status)}</th>
          <th>${esc(d.users.accessCol)}</th>
          <th>${esc(d.users.actionsCol)}</th>
        </tr></thead><tbody>${usersList
          .map(
            (item) => `<tr>
            <td><strong>${esc(item.nombre)}</strong></td>
            <td>${esc(item.cedula)}</td>
            <td>${esc(item.usuario)}</td>
            <td><span class="role-badge">${esc(item.perfil)}</span></td>
            <td>${item.sede_id ? esc(refName("sedes", item.sede_id)) : esc(d.allBranches)}</td>
            <td><span class="badge ${item.estado === "ACTIVO" ? "active" : "inactive"}">${esc(item.estado)}</span></td>
            <td>${item.bloqueado ? `<span class="badge inactive">${esc(d.users.blocked)}</span>` : item.debe_cambiar_password ? esc(d.users.pendingPass) : esc(d.users.ready)}</td>
            <td><div class="user-actions user-actions-stack">
              <button class="ghost edit-user btn-uniform" data-id="${item.id}">${esc(d.common.edit)}</button>
              <button class="ghost toggle-user btn-uniform ${item.estado === "INACTIVO" ? "activate" : "deactivate"}" data-id="${item.id}" data-state="${item.estado}">${esc(item.estado === "INACTIVO" ? d.users.activate : d.users.deactivate)}</button>
              <button class="ghost reset-user btn-uniform" data-id="${item.id}">${esc(d.users.resetPass)}</button>
              ${item.bloqueado ? `<button class="ghost unlock-user btn-uniform" data-id="${item.id}">${esc(d.users.unlock)}</button>` : ""}
            </div></td>
          </tr>`,
          )
          .join("")}</tbody></table></div>`
      : `<div class="empty">${esc(d.common.noRecords)}</div>`;

  document
    .querySelectorAll(".edit-user")
    .forEach((button) =>
      button.addEventListener("click", () =>
        userForm(
          (state.users || []).find((u) => u.id === Number(button.dataset.id)),
        ),
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

function userForm(item = null) {
  const d = dict();
  const isEdit = Boolean(item);
  document.body.insertAdjacentHTML(
    "beforeend",
    `<div class="modal-backdrop" id="modal"><section class="modal">
      <div class="topbar">
        <div><p class="eyebrow">${esc(d.common.security)}</p><h2>${esc(isEdit ? d.users.editTitle : d.users.createTitle)}</h2></div>
        <button class="ghost" id="close-modal">${esc(d.common.close)}</button>
      </div>
      <p class="subtle">${esc(isEdit ? d.users.editHint : d.users.createHint)}</p>
      <form id="user-form">
        <div class="form-grid">
          <label>${esc(d.fields.cedula)}<input name="cedula" value="${esc(item?.cedula || "")}" minlength="5" maxlength="20" ${isEdit ? "disabled" : "required"}></label>
          <label>${esc(d.fullName)}<input name="nombre" value="${esc(item?.nombre || "")}" minlength="3" maxlength="120" required></label>
          <label>${esc(d.fields.usuario)}<input name="usuario" value="${esc(item?.usuario || "")}" minlength="4" maxlength="60" autocomplete="off" ${isEdit ? "disabled" : "required"}></label>
          ${
            isEdit
              ? `<label>${esc(d.status)}<select name="estado"><option value="ACTIVO" ${item?.estado === "ACTIVO" ? "selected" : ""}>ACTIVO</option><option value="INACTIVO" ${item?.estado === "INACTIVO" ? "selected" : ""}>INACTIVO</option></select></label>`
              : `<label>${esc(d.fields.password)}<input name="password" type="password" minlength="8" maxlength="72" autocomplete="new-password" required></label>`
          }
          <label>${esc(d.fields.perfil)}<select name="perfil" required>
            <option value="CAJERO" ${item?.perfil === "CAJERO" ? "selected" : ""}>CAJERO</option>
            <option value="MESERO" ${item?.perfil === "MESERO" ? "selected" : ""}>MESERO</option>
            <option value="ADMINISTRADOR" ${item?.perfil === "ADMINISTRADOR" ? "selected" : ""}>ADMINISTRADOR</option>
          </select></label>
          <label>${esc(d.fields.sede_id)}<select name="sede_id">${refOptions("sedes", item?.sede_id ?? "", d.users.allAdminOnly)}</select></label>
        </div>
        <p class="subtle">${esc(d.users.branchMandatoryHint)}</p>
        <div id="form-error"></div>
        <div class="modal-actions">
          <button type="button" class="ghost" id="cancel-modal">${esc(d.common.cancel)}</button>
          <button class="primary">${esc(isEdit ? d.common.save : d.users.createTitle)}</button>
        </div>
      </form>
    </section></div>`,
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
          `<p class="error">${esc(d.users.branchMandatoryError)}</p>`;
        return;
      }
      try {
        await request(isEdit ? `/auth/usuarios/${item.id}` : "/auth/usuarios", {
          method: isEdit ? "PATCH" : "POST",
          body: JSON.stringify(values),
        });
        if (isEdit && state.user && item.id === state.user.id) {
          state.user.nombre = values.nombre || state.user.nombre;
          sessionStorage.setItem(USER_KEY, JSON.stringify(state.user));
        }
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
  const password = window.prompt(dict().users.promptNewPass);
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
  const d = dict();
  const nextState = currentState === "ACTIVO" ? "INACTIVO" : "ACTIVO";
  const action =
    nextState === "INACTIVO"
      ? d.users.deactivate.toLowerCase()
      : d.users.activate.toLowerCase();
  if (!window.confirm(d.users.confirmToggle.replace("{action}", action))) return;
  try {
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

// ====================================================== GENERIC PARAMETRIZACION RESOURCES (M2: Sedes, Tipos, Proveedores, Productos Globales)
async function resource(key) {
  const d = dict();
  const productFilters =
    (hasSedeFilter(key)
      ? `<select id="sede-filter" aria-label="${esc(d.fields.sede_id)}"><option value="">${esc(d.common.allBranchesFilter)}</option></select>`
      : "") +
    (hasTipoFilter(key)
      ? `<select id="tipo-filter" aria-label="${esc(d.fields.tipo_producto_id)}"><option value="">${esc(d.common.allTypesFilter)}</option></select>`
      : "");
  document.getElementById("view").innerHTML =
    `<div class="topbar"><div><p class="eyebrow">${esc(d.common.parametrization)}</p><h1>${esc(navLabel(key))}</h1></div>${esAdmin() ? `<div class="topbar-actions"><button class="primary" id="new-item">${esc(d.common.newBtn)}</button></div>` : ""}</div><section class="panel"><div class="toolbar"><input id="search" placeholder="${esc(d.common.searchPlaceholder)}" aria-label="${esc(d.common.searchPlaceholder)}">${productFilters}<button class="ghost" id="refresh">${esc(d.common.refresh)}</button></div><div id="table"></div></section>`;
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
    const queryParam = key === "sedes" ? "solo_activas=false" : "solo_activos=false";
    let raw = await request(
      `/parametrizacion/${RESOURCES[key].endpoint}?${queryParam}`,
    );
    if (key === "productos") {
      raw = await ensureProductsInAllBranches(raw);
      state.rawProducts = raw;
      // Deduplicate by codigo so Products shows global catalog items once
      const seen = new Map();
      raw.forEach((p) => {
        if (!seen.has(p.codigo)) {
          seen.set(p.codigo, p);
        }
      });
      state.items = Array.from(seen.values());
    } else {
      state.items = raw;
    }
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
  const d = dict();
  const sede = document.getElementById("sede-filter"),
    tipo = document.getElementById("tipo-filter");
  if (sede) {
    sede.innerHTML = refOptions("sedes", state.sedeFilter, d.common.allBranchesFilter);
    sede.value = state.sedeFilter;
  }
  if (tipo) {
    tipo.innerHTML = refOptions("tipos", state.tipoFilter, d.common.allTypesFilter);
    tipo.value = state.tipoFilter;
  }
}

function table(key) {
  const d = dict();
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
  const extraScopeHeader = r.globalCatalog ? `<th>${esc(d.common.scopeCol)}</th>` : "";
  document.getElementById("table").innerHTML = state.error
    ? `<p class="error">${esc(state.error)}</p>`
    : rows.length
      ? `<div class="table-wrap"><table><thead><tr>${r.fields.map((f) => `<th>${esc(fieldLabel(f.key))}</th>`).join("")}${extraScopeHeader}<th>${esc(d.status)}</th><th>${esAdmin() ? esc(d.users.actionsCol) : ""}</th></tr></thead><tbody>${rows
          .map((item) => {
            const isActive = item[r.active] !== false;
            const scopeCell = r.globalCatalog
              ? `<td><span class="role-badge">${esc(d.common.allBranchesBadge)}</span></td>`
              : "";
            return `<tr>${r.fields.map((f) => `<td>${esc(cellValue(f, item))}</td>`).join("")}${scopeCell}<td><span class="badge ${isActive ? "active" : "inactive"}">${esc(isActive ? d.common.active : d.common.inactive)}</span></td><td>${
              esAdmin()
                ? `<div class="user-actions">
                    <button class="ghost edit" data-id="${item.id}">${esc(d.common.edit)}</button>
                    <button class="ghost toggle-res ${isActive ? "deactivate" : "activate"}" data-id="${item.id}" data-active="${isActive}">${esc(isActive ? d.common.deactivate : d.common.activate)}</button>
                  </div>`
                : ""
            }</td></tr>`;
          })
          .join("")}</tbody></table></div>`
      : `<div class="empty">${esc(d.common.noRecords)}</div>`;

  document.querySelectorAll(".edit").forEach((button) =>
    button.addEventListener("click", () =>
      form(
        key,
        state.items.find((item) => item.id === Number(button.dataset.id)),
      ),
    ),
  );
  document.querySelectorAll(".toggle-res").forEach((button) =>
    button.addEventListener("click", () =>
      toggleResourceActive(
        key,
        state.items.find((item) => item.id === Number(button.dataset.id)),
        button.dataset.active === "true",
      ),
    ),
  );
}

async function toggleResourceActive(key, item, currentlyActive) {
  if (!item) return;
  const r = RESOURCES[key];
  const nextActive = !currentlyActive;
  try {
    if (key === "productos") {
      const action = nextActive ? "activar" : "inactivar";
      try {
        await request(`/parametrizacion/productos/${item.id}/${action}?todas_las_sedes=true`, {
          method: "POST",
        });
      } catch {
        const siblings = (state.rawProducts || []).filter((p) => p.codigo === item.codigo);
        for (const sib of siblings.length ? siblings : [item]) {
          try {
            await request(`/parametrizacion/productos/${sib.id}/${action}`, { method: "POST" });
          } catch {}
        }
      }
    } else {
      await request(`/parametrizacion/${r.endpoint}/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({ [r.active]: nextActive }),
      });
    }
    await load(key);
  } catch (error) {
    state.error = error.message;
    table(key);
  }
}

function fieldHtml(f, item) {
  const locked = item && f.fixed ? "disabled" : "",
    required = f.required && !locked ? "required" : "",
    label = fieldLabel(f.key);
  if (f.ref)
    return `<label>${esc(label)}<select name="${f.key}" ${required} ${locked}>${refOptions(f.ref, item?.[f.key] ?? "")}</select></label>`;
  const defaultVal = item?.[f.key] !== undefined ? item[f.key] : "";
  return `<label>${esc(label)}<input name="${f.key}" type="${f.type || "text"}" value="${esc(defaultVal)}" ${required} ${locked}></label>`;
}

function form(key, item = null) {
  const d = dict();
  const r = RESOURCES[key];
  document.body.insertAdjacentHTML(
    "beforeend",
    `<div class="modal-backdrop" id="modal"><section class="modal"><div class="topbar"><div><p class="eyebrow">${esc(item ? d.common.editRecord : d.common.newRecord)}</p><h2>${esc(navLabel(key))}</h2></div><button class="ghost" id="close-modal">${esc(d.common.close)}</button></div>${r.globalCatalog ? `<p class="subtle">${esc(d.common.globalProductHint)}</p>` : ""}<form id="resource-form"><div class="form-grid">${r.fields.map((f) => fieldHtml(f, item)).join("")}</div>${item && r.fields.some((f) => f.fixed) ? `<p class="subtle">${esc(d.common.lockedFieldsHint)}</p>` : ""}<div id="form-error"></div><div class="modal-actions"><button type="button" class="ghost" id="cancel-modal">${esc(d.common.cancel)}</button><button class="primary">${esc(d.common.save)}</button></div></form></section></div>`,
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
        if (key === "productos") {
          if (item) {
            try {
              await request(`/parametrizacion/productos/${item.id}?todas_las_sedes=true`, {
                method: "PATCH",
                body: JSON.stringify(values),
              });
            } catch {
              const siblings = (state.rawProducts || []).filter((p) => p.codigo === item.codigo);
              for (const sib of siblings.length ? siblings : [item]) {
                await request(`/parametrizacion/productos/${sib.id}`, {
                  method: "PATCH",
                  body: JSON.stringify(values),
                });
              }
            }
          } else {
            try {
              await request("/parametrizacion/productos?todas_las_sedes=true", {
                method: "POST",
                body: JSON.stringify(values),
              });
            } catch {
              for (const s of state.cat.sedes || []) {
                await request("/parametrizacion/productos", {
                  method: "POST",
                  body: JSON.stringify({ ...values, sede_id: s.id }),
                });
              }
            }
          }
        } else if (key === "sedes" && !item) {
          await request("/parametrizacion/sedes?copiar_catalogo=true", {
            method: "POST",
            body: JSON.stringify(values),
          });
        } else {
          await request(
            `/parametrizacion/${r.endpoint}${item ? `/${item.id}` : ""}`,
            { method: item ? "PATCH" : "POST", body: JSON.stringify(values) },
          );
        }
        close();
        state.filter = "";
        if (state.route === "mesas") await loadTablesMap();
        else await load(key);
      } catch (error) {
        document.getElementById("form-error").innerHTML =
          `<p class="error">${esc(error.message)}</p>`;
      }
    });
}

// ====================================================== CUSTOM THEMED DROPDOWNS (Matches Cream & Blue Design)
const CHEVRON_SVG = `<svg class="custom-select-arrow" width="14" height="14" style="width:14px;height:14px;flex-shrink:0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>`;
const CHECK_SVG = `<svg width="13" height="13" style="width:13px;height:13px;flex-shrink:0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>`;

function syncCustomSelect(selectEl) {
  const wrap = selectEl._customWrap;
  if (!wrap) return;
  const labelEl = wrap.querySelector(".custom-select-label");
  const menuEl = wrap.querySelector(".custom-select-menu");
  const triggerBtn = wrap.querySelector(".custom-select-trigger");
  if (!labelEl || !menuEl || !triggerBtn) return;

  const options = Array.from(selectEl.options);
  const selectedOpt =
    options.find((o) => o.value === selectEl.value) ||
    options[selectEl.selectedIndex] ||
    options[0];
  const sig =
    `${Boolean(selectEl.disabled)}::${selectedOpt ? selectedOpt.value : ""}::` +
    options.map((o) => `${o.value}=${o.textContent}`).join("|");
  if (wrap._lastSig === sig) return;
  wrap._lastSig = sig;

  triggerBtn.disabled = Boolean(selectEl.disabled);
  labelEl.textContent = selectedOpt ? selectedOpt.textContent : "";

  menuEl.innerHTML = options
    .map((opt) => {
      const isSel = selectedOpt && opt.value === selectedOpt.value;
      return `<button type="button" class="custom-select-option ${isSel ? "selected" : ""}" data-val="${esc(opt.value)}"><span>${esc(opt.textContent)}</span>${isSel ? CHECK_SVG : ""}</button>`;
    })
    .join("");

  menuEl.querySelectorAll(".custom-select-option").forEach((optBtn) => {
    optBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const newVal = optBtn.dataset.val;
      if (selectEl.value !== newVal) {
        selectEl.value = newVal;
        selectEl.dispatchEvent(new Event("change", { bubbles: true }));
      }
      syncCustomSelect(selectEl);
      wrap.classList.remove("open");
    });
  });
}

function enhanceSelect(selectEl) {
  if (!selectEl || selectEl._customWrap) {
    if (selectEl?._customWrap) syncCustomSelect(selectEl);
    return;
  }
  const wrap = document.createElement("div");
  wrap.className = "custom-select-wrap";
  if (selectEl.style.maxWidth) {
    wrap.style.maxWidth = selectEl.style.maxWidth;
  }
  selectEl.parentNode.insertBefore(wrap, selectEl);
  wrap.appendChild(selectEl);
  selectEl.classList.add("custom-select-native");

  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "custom-select-trigger";
  trigger.innerHTML = `<span class="custom-select-label"></span>${CHEVRON_SVG}`;

  const menu = document.createElement("div");
  menu.className = "custom-select-menu";

  wrap.appendChild(trigger);
  wrap.appendChild(menu);
  selectEl._customWrap = wrap;

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    if (selectEl.disabled) return;
    const wasOpen = wrap.classList.contains("open");
    document
      .querySelectorAll(".custom-select-wrap.open")
      .forEach((w) => w.classList.remove("open"));
    if (!wasOpen) {
      syncCustomSelect(selectEl);
      wrap.classList.add("open");
    }
  });

  selectEl.addEventListener("change", () => syncCustomSelect(selectEl));

  const optObserver = new MutationObserver(() => syncCustomSelect(selectEl));
  optObserver.observe(selectEl, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["disabled", "value"],
  });

  syncCustomSelect(selectEl);
}

function enhanceAllSelects() {
  document.querySelectorAll("select").forEach(enhanceSelect);
}

document.addEventListener("click", () => {
  document
    .querySelectorAll(".custom-select-wrap.open")
    .forEach((w) => w.classList.remove("open"));
});

const domSelectObserver = new MutationObserver(() => enhanceAllSelects());
domSelectObserver.observe(document.body, { childList: true, subtree: true });

document.documentElement.lang = state.lang;
if (state.token && state.user) {
  idle();
  state.user.debe_cambiar_password ? renderPasswordChange() : renderShell();
} else renderLogin();
enhanceAllSelects();
