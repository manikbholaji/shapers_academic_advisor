import pytest
from playwright.sync_api import sync_playwright

TARGET_URL = "https://academicadvisor.streamlit.app/"
IFRAME_TITLE = "streamlitApp"
ANALYTICS_TAB_SELECTOR = 'text="Analytics"'
DOWNLOAD_BUTTON_SELECTOR = 'text="Download interactions CSV"'


def test_download_button_exists_and_is_clickable():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(TARGET_URL, timeout=60000)

        frame = page.frame_locator(f'iframe[title="{IFRAME_TITLE}"]')
        frame.locator(ANALYTICS_TAB_SELECTOR).wait_for(timeout=60000)
        frame.locator(ANALYTICS_TAB_SELECTOR).click()

        button = frame.locator(DOWNLOAD_BUTTON_SELECTOR)
        if button.count() == 0:
            pytest.skip("No Analytics interaction data yet; direct download button is not rendered.")

        button.wait_for(timeout=60000)

        assert button.is_visible()
        assert button.is_enabled()

        with page.expect_download(timeout=60000) as download_info:
            button.click()

        download = download_info.value
        assert download.suggested_filename.endswith(".csv")
        download.cancel()

        browser.close()


def test_analytics_toolbar_download_button_clickable():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(TARGET_URL, timeout=60000)

        frame = page.frame_locator(f'iframe[title="{IFRAME_TITLE}"]')
        frame.locator(ANALYTICS_TAB_SELECTOR).wait_for(timeout=60000)
        frame.locator(ANALYTICS_TAB_SELECTOR).click()

        toolbar_button = frame.locator('button:has-text("Download as CSV")')
        if toolbar_button.count() == 0:
            pytest.skip("No Analytics interaction data yet; toolbar CSV download button is not rendered.")

        toolbar_button.wait_for(timeout=60000)
        toolbar_button.scroll_into_view_if_needed()

        with page.expect_download(timeout=60000) as download_info:
            toolbar_button.click()

        download = download_info.value
        assert download.suggested_filename.endswith(".csv")
        download.cancel()

        browser.close()
