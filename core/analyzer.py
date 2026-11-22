from collections import deque
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from config import (
    PAGE_SETTLE_MS,
    SENSITIVE_QUERY_KEYS,
    BLOCKED_PATH_PARTS
)
from core.inspector import inspect_page


def canonical_url(url):
    """Normaliza fragmentos y orden de parámetros para evitar duplicados."""
    parsed = urlparse(url)
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path or "/",
        parsed.params,
        query,
        ""
    ))


def redact_url(url):
    parsed = urlparse(url)
    safe_pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS:
            value = "[REDACTADO]"
        safe_pairs.append((key, value))
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        urlencode(safe_pairs),
        ""
    ))


class SiteAnalyzer:
    def __init__(self, page, base_url, writer):
        self.page = page
        self.base_url = base_url
        self.origin = (urlparse(base_url).scheme, urlparse(base_url).netloc)
        self.writer = writer
        self.queue = deque([canonical_url(base_url)])
        self.visited = set()
        self.network_events = []
        self.page_errors = []
        self._listeners_attached = False

    def _same_origin(self, url):
        parsed = urlparse(url)
        return (parsed.scheme, parsed.netloc) == self.origin

    def _allowed_url(self, url):
        parsed = urlparse(url)
        if not self._same_origin(url):
            return False
        if parsed.scheme not in ("http", "https"):
            return False
        path = parsed.path.lower()
        if any(part in path for part in BLOCKED_PATH_PARTS):
            return False
        return True

    def _on_request(self, request):
        self.network_events.append({
            "event": "request",
            "url": redact_url(request.url),
            "method": request.method,
            "resource_type": request.resource_type
        })

    def _on_response(self, response):
        request = response.request
        self.network_events.append({
            "event": "response",
            "url": redact_url(response.url),
            "method": request.method,
            "resource_type": request.resource_type,
            "status": response.status,
            "content_type": response.headers.get("content-type")
        })

    def _on_page_error(self, error):
        self.page_errors.append(str(error))

    def _attach_listeners(self):
        if self._listeners_attached:
            return
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)
        self.page.on("pageerror", self._on_page_error)
        self._listeners_attached = True

    def _detach_listeners(self):
        if not self._listeners_attached:
            return
        self.page.remove_listener("request", self._on_request)
        self.page.remove_listener("response", self._on_response)
        self.page.remove_listener("pageerror", self._on_page_error)
        self._listeners_attached = False

    def inspect_current_page(self):
        self._attach_listeners()
        record = self._inspect(self.page.url)
        if record:
            self.writer.write_page(record)
        self._detach_listeners()

    def _inspect(self, url):
        print("\n" + "-" * 70)
        print("INSPECCIONANDO:", redact_url(url))
        print("-" * 70)

        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
            self.page.wait_for_timeout(PAGE_SETTLE_MS)
        except PlaywrightTimeoutError:
            print("Tiempo de navegación agotado; se inspeccionará lo que haya cargado.")
        except Exception as exc:
            print("No se pudo abrir:", exc)
            self.writer.write_error(url, str(exc))
            return None

        # Detectar pérdida de sesión conocida por el formulario del sitio.
        if self.page.locator("#MainContent_password").count() > 0:
            self.writer.write_error(url, "La página parece requerir iniciar sesión.")
            print("La sesión parece haber expirado. Se detiene el rastreo.")
            return {"session_lost": True, "url": redact_url(url)}

        record = inspect_page(self.page, redact_url(url))
        record["url"] = redact_url(url)

        print("Título:", record["title"])
        print("Campos:", len(record["fields"]))
        print("Botones:", len(record["buttons"]))
        print("Formularios:", len(record["forms"]))
        print("Tablas:", len(record["tables"]))
        print("Enlaces:", len(record["links"]))
        print("Scripts:", len(record["scripts"]))

        return record

    def crawl(self):
        self._attach_listeners()
        session_lost = False

        try:
            while self.queue:
                url = self.queue.popleft()
                key = canonical_url(url)

                if key in self.visited:
                    continue
                if not self._allowed_url(key):
                    continue

                self.visited.add(key)
                record = self._inspect(key)

                if not record:
                    continue
                if record.get("session_lost"):
                    session_lost = True
                    break

                self.writer.write_page(record)

                for link in record.get("links", []):
                    target = canonical_url(link["resolved_url"])
                    if self._allowed_url(target) and target not in self.visited:
                        if target not in self.queue:
                            self.queue.append(target)

                # También descubrir iframes del mismo origen.
                for iframe in record.get("iframes", []):
                    src = iframe.get("src")
                    if src:
                        target = canonical_url(urljoin(self.page.url, src))
                        if self._allowed_url(target) and target not in self.visited:
                            if target not in self.queue:
                                self.queue.append(target)

        finally:
            self._detach_listeners()

        self.writer.write_network(self.network_events)
        self.writer.write_page_errors(self.page_errors)
        self.writer.write_crawl_state({
            "visited_count": len(self.visited),
            "pending_count": len(self.queue),
            "session_lost": session_lost,
            "visited_urls": sorted(redact_url(u) for u in self.visited),
            "pending_urls": sorted(redact_url(u) for u in self.queue)
        })

    def summary(self):
        return {
            "pages_visited": len(self.visited),
            "network_events": len(self.network_events),
            "page_errors": len(self.page_errors),
            "pending_routes": len(self.queue)
        }
