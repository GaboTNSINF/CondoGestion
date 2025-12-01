from playwright.sync_api import sync_playwright

def verify_login_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("http://localhost:8000/auth/login/")
            page.wait_for_selector(".login-card", timeout=10000)

            # Take a screenshot of the whole page to see the centering and background
            page.screenshot(path="verification/login_page.png")

            print("Screenshot taken: verification/login_page.png")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_login_page()
