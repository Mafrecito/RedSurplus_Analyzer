from playwright.sync_api import sync_playwright
from config import NAVIGATION_TIMEOUT_MS


class BrowserSession:
    def __init__(self, base_url):
        self.base_url = base_url
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context(
            viewport={"width": 1440, "height": 900},
            accept_downloads=False
        )
        self.page = self.context.new_page()
        self.page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        self.page.set_default_timeout(15000)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.context:
                self.context.close()
        finally:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
