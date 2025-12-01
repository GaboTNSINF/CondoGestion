from playwright.sync_api import sync_playwright

def verify_login_ux():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("http://localhost:8000/auth/login/")
            page.wait_for_selector(".login-card", timeout=10000)

            # 1. Verify 'Remember Me' Checkbox
            remember_me = page.locator("input[name='remember_me']")
            if remember_me.is_visible():
                print("Success: 'Remember Me' checkbox found.")
            else:
                print("Failure: 'Remember Me' checkbox NOT found.")

            # 2. Verify 'Show Password' Toggle
            # Check for the eye icon button
            toggle_btn = page.locator(".password-toggle-btn")
            if toggle_btn.is_visible():
                print("Success: Password toggle button found.")

                # Test functionality
                password_input = page.locator("input[name='password']")
                print(f"Initial type: {password_input.get_attribute('type')}")

                toggle_btn.click()
                print(f"Type after click: {password_input.get_attribute('type')}")

                if password_input.get_attribute('type') == 'text':
                    print("Success: Password visibility toggled to text.")
                else:
                    print("Failure: Password visibility toggle failed.")

            else:
                print("Failure: Password toggle button NOT found.")

            # 3. Verify 'Forgot Password' Link
            forgot_link = page.get_by_text("¿Olvidaste tu contraseña?")
            if forgot_link.is_visible():
                print("Success: 'Forgot Password' link found.")
            else:
                 print("Failure: 'Forgot Password' link NOT found.")

            # 4. Verify Footer Links
            terms = page.get_by_text("Términos y Condiciones")
            privacy = page.get_by_text("Política de Privacidad")

            if terms.is_visible() and privacy.is_visible():
                print("Success: Footer links found.")
            else:
                print("Failure: Footer links NOT found.")

            # Take a screenshot
            page.screenshot(path="verification/login_ux_page.png")
            print("Screenshot taken: verification/login_ux_page.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_login_ux()
