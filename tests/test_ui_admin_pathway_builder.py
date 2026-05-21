from playwright.sync_api import sync_playwright

TARGET_URL = "https://academicadvisor.streamlit.app/"


def test_admin_pathway_builder_recommends_matching_field():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(TARGET_URL, timeout=60000)

        page.wait_for_selector('iframe[title="streamlitApp"]', timeout=60000)
        app_frame = page.frame(url="https://academicadvisor.streamlit.app/~/+/")
        assert app_frame is not None

        app_frame.wait_for_selector('text="Admin"', timeout=60000)
        app_frame.click('text="Admin"')

        app_frame.wait_for_selector('text="🎯 Pathway Advisor Configuration"', timeout=60000)

        app_frame.click('text="Engineering / Computer Science"')
        app_frame.wait_for_selector('text="Medical / Life Sciences"', timeout=60000)
        app_frame.click('text="Medical / Life Sciences"')

        app_frame.wait_for_selector('button:has-text("Build Complete Pathway")', timeout=60000)
        app_frame.click('button:has-text("Build Complete Pathway")')
        page.wait_for_timeout(3000)

        app_frame.wait_for_selector('text=/Recommended Pathways/', timeout=60000)

        assert app_frame.locator(r'text=/Medical \/ Life Sciences — Complete Pathway/').count() == 1

        browser.close()


def test_admin_pathway_builder_humanities_field_works():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(TARGET_URL, timeout=60000)

        page.wait_for_selector('iframe[title="streamlitApp"]', timeout=60000)
        app_frame = page.frame(url="https://academicadvisor.streamlit.app/~/+/")
        assert app_frame is not None

        app_frame.wait_for_selector('text="Admin"', timeout=60000)
        app_frame.click('text="Admin"')

        app_frame.wait_for_selector('text="🎯 Pathway Advisor Configuration"', timeout=60000)

        app_frame.click('text="Engineering / Computer Science"')
        app_frame.wait_for_selector('text="Humanities / Psychology / Public Policy"', timeout=60000)
        app_frame.click('text="Humanities / Psychology / Public Policy"')

        app_frame.wait_for_selector('button:has-text("Build Complete Pathway")', timeout=60000)
        app_frame.click('button:has-text("Build Complete Pathway")')
        page.wait_for_timeout(3000)

        app_frame.wait_for_selector('text=/Recommended Pathways/', timeout=60000)

        assert app_frame.locator(r'text=/Humanities \/ Psychology \/ Public Policy — Complete Pathway/').count() == 1

        browser.close()
