from urllib.parse import urljoin


def safe_attribute(locator, name):
    try:
        return locator.get_attribute(name)
    except Exception:
        return None


def inspect_page(page, current_url):
    """Inspección pasiva del DOM. No hace clic ni envía formularios."""
    data = {
        "url": current_url,
        "final_url": page.url,
        "title": page.title(),
        "links": [],
        "fields": [],
        "buttons": [],
        "forms": [],
        "tables": [],
        "scripts": [],
        "resources": [],
        "iframes": [],
        "storage": {},
        "cookies": []
    }

    # Enlaces
    for item in page.locator("a[href]").all():
        href = safe_attribute(item, "href")
        text = ""
        try:
            text = item.inner_text().strip()
        except Exception:
            pass
        if href:
            data["links"].append({
                "text": text,
                "href": href,
                "resolved_url": urljoin(page.url, href)
            })

    # Campos y listas desplegables; no se capturan valores escritos por usuarios.
    for item in page.locator("input, select, textarea").all():
        tag = item.evaluate("(e) => e.tagName")
        field = {
            "tag": tag,
            "type": safe_attribute(item, "type"),
            "id": safe_attribute(item, "id"),
            "name": safe_attribute(item, "name"),
            "placeholder": safe_attribute(item, "placeholder"),
            "aria_label": safe_attribute(item, "aria-label"),
            "disabled": item.is_disabled()
        }
        if tag == "SELECT":
            field["options"] = []
            for option in item.locator("option").all():
                field["options"].append({
                    "text": option.inner_text().strip(),
                    "value": safe_attribute(option, "value")
                })
        data["fields"].append(field)

    # Botones: descripción solamente; no se ejecutan.
    for item in page.locator(
        "button, input[type=button], input[type=submit], [role=button]"
    ).all():
        text = ""
        try:
            text = item.inner_text().strip()
        except Exception:
            text = safe_attribute(item, "value") or ""
        data["buttons"].append({
            "tag": item.evaluate("(e) => e.tagName"),
            "text": text,
            "id": safe_attribute(item, "id"),
            "type": safe_attribute(item, "type"),
            "name": safe_attribute(item, "name"),
            "disabled": item.is_disabled()
        })

    # Formularios: solo estructura y método; no se envían.
    for form in page.locator("form").all():
        data["forms"].append({
            "action": safe_attribute(form, "action"),
            "method": safe_attribute(form, "method") or "GET",
            "id": safe_attribute(form, "id"),
            "name": safe_attribute(form, "name")
        })

    # Tablas: encabezados y conteos. No se copian filas de datos sensibles.
    for index, table in enumerate(page.locator("table").all(), 1):
        headers = table.locator("th").all_inner_texts()
        row_count = table.locator("tr").count()
        data["tables"].append({
            "index": index,
            "headers": headers,
            "row_count": row_count,
            "id": safe_attribute(table, "id"),
            "class": safe_attribute(table, "class")
        })

    # Scripts
    for script in page.locator("script[src]").all():
        src = safe_attribute(script, "src")
        if src:
            data["scripts"].append(urljoin(page.url, src))

    # Recursos referenciados por elementos comunes.
    resource_selectors = {
        "img": "src",
        "link": "href",
        "source": "src",
        "iframe": "src"
    }
    for tag, attribute in resource_selectors.items():
        for item in page.locator(f"{tag}[{attribute}]").all():
            value = safe_attribute(item, attribute)
            if value:
                data["resources"].append({
                    "tag": tag,
                    "url": urljoin(page.url, value),
                    "rel": safe_attribute(item, "rel"),
                    "type": safe_attribute(item, "type")
                })

    for frame in page.locator("iframe").all():
        data["iframes"].append({
            "src": safe_attribute(frame, "src"),
            "title": safe_attribute(frame, "title"),
            "name": safe_attribute(frame, "name")
        })

    # Solo nombres de claves de almacenamiento, nunca sus valores.
    try:
        data["storage"] = page.evaluate("""() => ({
            local_storage_keys: Object.keys(localStorage),
            session_storage_keys: Object.keys(sessionStorage)
        })""")
    except Exception:
        data["storage"] = {"available": False}

    # Solo nombres y metadatos básicos de cookies, nunca valores.
    try:
        cookies = page.context.cookies()
        data["cookies"] = [
            {
                "name": c.get("name"),
                "domain": c.get("domain"),
                "path": c.get("path"),
                "httpOnly": c.get("httpOnly"),
                "secure": c.get("secure"),
                "sameSite": c.get("sameSite")
            }
            for c in cookies
        ]
    except Exception:
        pass

    return data
