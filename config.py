BASE_URL = "http://aqp.redsurplus.com/"

# No se establece un máximo artificial de páginas.
# El rastreo se detiene cuando ya no quedan rutas internas nuevas,
# cuando el usuario pulsa Ctrl+C o cuando el sitio deja de responder.
NAVIGATION_TIMEOUT_MS = 45000
PAGE_SETTLE_MS = 1200

# Claves de URL que no deben guardarse literalmente en los informes.
SENSITIVE_QUERY_KEYS = {
    "password", "passwd", "pwd", "token", "access_token",
    "refresh_token", "authorization", "cookie", "session",
    "sessionid", "sid", "dni", "documento"
}

# Patrones de rutas que no se deben visitar automáticamente.
# Se excluyen cierres de sesión y acciones claramente destructivas.
BLOCKED_PATH_PARTS = (
    "logout", "logoff", "signout", "cerrar-sesion",
    "delete", "eliminar", "remove", "borrar"
)
