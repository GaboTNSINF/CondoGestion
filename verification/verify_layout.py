from playwright.sync_api import sync_playwright

def verify_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080}) # Wide screen to see the effect
        try:
            page.goto("http://localhost:8000/verification_layout/")
            page.wait_for_selector("h1")

            # Take a screenshot
            page.screenshot(path="verification/layout_page.png")
            print("Screenshot taken: verification/layout_page.png")

            # Verify the container class exists in the rendered HTML
            content_div = page.locator(".container.py-4")
            if content_div.count() > 0:
                print("Success: '.container.py-4' found.")
            else:
                print("Failure: '.container.py-4' NOT found.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_layout()
