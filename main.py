from getpass import getpass
from urllib.parse import urlparse
from core.browser import BrowserSession
from core.analyzer import SiteAnalyzer
from core.reporter import ReportWriter
from config import BASE_URL


def select_office(page):
    selector = page.locator("#MainContent_drpPlaces")
    if selector.count() == 0:
        print("No se encontró el selector de oficina. Continuaré con la página actual.")
        return

    options = selector.locator("option").all()
    offices = []
    for option in options:
        label = option.inner_text().strip()
        value = option.get_attribute("value")
        if value and value != "00000000-0000-0000-0000-000000000000":
            offices.append(label)

    print("\nOFICINAS DISPONIBLES")
    for i, office in enumerate(offices, 1):
        print(f"{i}. {office}")

    while True:
        choice = input("Selecciona una oficina: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(offices):
            selected = offices[int(choice) - 1]
            selector.select_option(label=selected)
            print(f"Oficina seleccionada: {selected}")
            return
        print("Selección no válida.")


def login(page):
    if page.locator("#MainContent_password").count() == 0:
        print("No se detectó el formulario de inicio de sesión.")
        return True

    print("\nINICIO DE SESIÓN")
    username = input("DNI/usuario: ").strip()
    password = getpass("Contraseña (no se mostrará): ")

    if not username or not password:
        print("Usuario y contraseña son obligatorios.")
        return False

    page.locator("#MainContent_user").fill(username)
    page.locator("#MainContent_password").fill(password)
    page.locator("#MainContent_btnAceptar").click()
    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)

    if page.locator("#MainContent_password").count() > 0:
        print("No se pudo confirmar el inicio de sesión. Revisa el acceso.")
        return False

    print("Inicio de sesión aparentemente correcto.")
    return True


def main():
    print("=" * 62)
    print("              RED SURPLUS ANALYZER")
    print("=" * 62)
    print("Este programa inspecciona páginas y recursos del mismo sitio.")
    print("No envía formularios de negocio ni pulsa botones operativos.")
    print("Presiona Ctrl+C para detener el análisis en cualquier momento.\n")

    base = input(f"URL del sistema [{BASE_URL}]: ").strip() or BASE_URL
    parsed = urlparse(base)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        print("URL no válida.")
        return

    if parsed.scheme == "http":
        print("\nADVERTENCIA: el sitio usa HTTP. Las credenciales y la sesión")
        print("podrían viajar sin cifrado. Evita redes públicas y solicita HTTPS")
        print("al administrador del sistema.\n")

    with BrowserSession(base) as session:
        page = session.page
        print("Abriendo:", base)
        page.goto(base, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1200)

        select_office(page)
        if not login(page):
            return

        print("\nElige el tipo de análisis:")
        print("1. Analizar todo el sitio (rutas internas descubiertas)")
        print("2. Analizar solamente la página actual")
        print("3. Salir")

        choice = input("Opción: ").strip()
        if choice == "3":
            return

        writer = ReportWriter()
        analyzer = SiteAnalyzer(
            page=page,
            base_url=base,
            writer=writer
        )

        try:
            if choice == "1":
                analyzer.crawl()
            elif choice == "2":
                analyzer.inspect_current_page()
            else:
                print("Opción no válida.")
                return
        except KeyboardInterrupt:
            print("\nAnálisis detenido por el usuario.")
        finally:
            writer.finalize(analyzer.summary())
            print("\nANÁLISIS FINALIZADO")
            print("Carpeta de resultados:", writer.output_dir)
            print("Páginas inspeccionadas:", len(analyzer.visited))
            print("Revisa el informe resumen y los archivos JSON/CSV.")


if __name__ == "__main__":
    main()
