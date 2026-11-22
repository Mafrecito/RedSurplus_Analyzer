import json
import csv
from pathlib import Path
from datetime import datetime


class ReportWriter:
    def __init__(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("resultados") / f"analisis_{timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pages_file = self.output_dir / "paginas.jsonl"
        self.network_file = self.output_dir / "red.jsonl"
        self.errors_file = self.output_dir / "errores.jsonl"
        self.state_file = self.output_dir / "estado_rastreo.json"
        self.summary_file = self.output_dir / "resumen.json"
        self.routes_file = self.output_dir / "rutas.csv"

    def _append_jsonl(self, path, value):
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(value, ensure_ascii=False) + "\n")

    def write_page(self, record):
        self._append_jsonl(self.pages_file, record)

    def write_network(self, events):
        for event in events:
            self._append_jsonl(self.network_file, event)

    def write_error(self, url, error):
        self._append_jsonl(self.errors_file, {"url": url, "error": error})

    def write_page_errors(self, errors):
        for error in errors:
            self._append_jsonl(self.errors_file, {"type": "javascript_page_error", "error": error})

    def write_crawl_state(self, state):
        self.state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        with self.routes_file.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["url"])
            for url in state.get("visited_urls", []):
                writer.writerow([url])

    def finalize(self, summary):
        self.summary_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
