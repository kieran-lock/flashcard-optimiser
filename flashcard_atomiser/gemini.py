from typing import Iterator, Self
from dataclasses import dataclass
from contextlib import contextmanager
import time
import re

from playwright.sync_api import sync_playwright, Page, Locator


@dataclass(slots=True)
class Gemini:
    GEMINI_URL = "https://gemini.google.com/app"
    TIMEOUT_MS = 40_000
    WRITING_TIMEOUT_MS = 180_000
    DEFAULT_PORT = 9222

    _page: Page
    _response: str = ""

    @classmethod
    @contextmanager
    def web(cls, *, port: int = DEFAULT_PORT) -> Iterator[Self]:
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(f"http://localhost:{port}")
            page = browser.contexts[0].new_page()
            page.goto(cls.GEMINI_URL, timeout=cls.TIMEOUT_MS)
            gemini = cls(page)
            gemini.wait_for_page_load()
            yield gemini
            browser.close()
    
    @classmethod
    @contextmanager
    def gem(cls, gem_name: str, *, port: int = DEFAULT_PORT) -> Iterator[Self]:
        with cls.web(port=port) as gemini:
            yield gemini.select_gem(gem_name)
    
    def wait_for_page_load(self) -> None:
        self._page.wait_for_load_state("domcontentloaded", timeout=self.TIMEOUT_MS)

    def select_gem(self, gem_name: str) -> Self:
        gem_button = self.get_gem_button_locator(gem_name)
        gem_button.click()
        self._page.locator("#chat-history").filter(has_text=gem_name).wait_for(timeout=self.TIMEOUT_MS)
        self.wait_for_page_load()
        return self
    
    def select_model(self, model_name: str) -> Self:
        model_item = self.get_model_dropdown_item_locator(model_name)
        model_item.click()
        self.wait_for_page_load()
        return self
    
    def get_model_dropdown_locator(self) -> Locator:
        locator = self._page.locator("[data-test-id='bard-mode-menu-button']").locator("button").first
        locator.wait_for(timeout=self.TIMEOUT_MS)
        return locator
    
    def get_model_dropdown_item_locator(self, model_name: str) -> Locator:
        dropdown = self.get_model_dropdown_locator()
        dropdown.click()
        locator = self._page.get_by_role("menuitemradio", name=re.compile(re.escape(model_name), re.IGNORECASE)).first
        locator.wait_for(timeout=self.TIMEOUT_MS)
        return locator

    def get_recent_chat_button_locator(self, idx: int = 0) -> Locator:
        locator = self._page.locator("[data-test-id='conversation']").nth(idx)
        locator.wait_for(timeout=self.TIMEOUT_MS)
        return locator
    
    def get_gem_button_locator(self, gem_name: str) -> Locator:
        locator = self._page.get_by_role("button", name=gem_name).first
        locator.wait_for(timeout=self.TIMEOUT_MS)
        return locator
    
    def get_input_box_locator(self) -> Locator:
        locator = self._page.get_by_role("textbox")
        locator.wait_for(timeout=self.TIMEOUT_MS)
        return locator
    
    def get_send_button_locator(self) -> Locator:
        locator = self._page.get_by_role("button", name="Send")
        locator.wait_for(timeout=self.TIMEOUT_MS)
        return locator
    
    def get_latest_response_locator(self) -> Locator:
        locator = self._page.locator("message-content").last
        locator.wait_for(timeout=self.WRITING_TIMEOUT_MS)
        return locator
    
    def get_recent_chat_menu_locator(self, idx: int = 0) -> Locator:
        recent_chat_container = self.get_recent_chat_button_locator(idx).locator("..")
        locator = recent_chat_container.locator("[data-test-id='actions-menu-button']")
        locator.wait_for(timeout=self.TIMEOUT_MS, state="attached")
        return locator
    
    def get_recent_chat_delete_button_locator(self, idx: int = 0) -> Locator:
        self.get_recent_chat_menu_locator(idx).click(force=True)
        locator = self._page.locator("button[data-test-id='delete-button']")
        locator.wait_for(timeout=self.TIMEOUT_MS)
        return locator
    
    def delete_recent_chat(self, idx: int = 0) -> Self:
        delete_button = self.get_recent_chat_delete_button_locator(idx)
        delete_button.click()
        confirmation_dialog = self._page.locator("mat-dialog-container")
        confirmation_dialog.wait_for(timeout=self.TIMEOUT_MS)
        confirm_btn = confirmation_dialog.locator("button[data-test-id='confirm-button']")
        confirm_btn.click()
        confirmation_dialog.wait_for(timeout=self.TIMEOUT_MS, state="hidden")
        return self
    
    def await_response(self) -> str:
        self.wait_for_page_load()
        started_waiting_at = time.time()
        latest_response = self.get_latest_response_locator()
        while True:
            elapsed_ms = (time.time() - started_waiting_at) * 1000
            if elapsed_ms > self.WRITING_TIMEOUT_MS:
                raise TimeoutError("Timed out waiting for text stability.")
            _response = latest_response.inner_text(timeout=self.WRITING_TIMEOUT_MS - elapsed_ms)
            if _response == self._response and len(_response):
                return _response.strip()
            self._response = _response
            time.sleep(1.0)
    
    def ask(self, prompt: str) -> str:
        input_box = self.get_input_box_locator()
        input_box.click()
        input_box.fill(prompt)
        self._page.keyboard.press("Enter")
        return self.await_response()
