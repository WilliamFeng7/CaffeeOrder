import asyncio
import random
import string
from playwright.async_api import async_playwright, expect

# Config
BASE_URL_STUDENT = "http://localhost"
BASE_URL_ADMIN = "http://localhost:8080"
ITERATIONS = 20

# Credentials
STUDENT_USER = "student_test"
STUDENT_PASS = "StudentPass123!@#"
ADMIN_USER = "admin_test"
ADMIN_PASS = "AdminPass123!@#"

async def run_stress_test():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)

        print(f"Starting Stress Test for {ITERATIONS} iterations...")

        for i in range(1, ITERATIONS + 1):
            print(f"\n--- Iteration {i}/{ITERATIONS} ---")
            # Create fresh context for each iteration
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # --- Student Flow ---
                print("Step 1: Student Login & Order")
                
                await page.goto(f"{BASE_URL_STUDENT}/login")
                await page.fill("input[type='text']", STUDENT_USER)
                await page.fill("input[type='password']", STUDENT_PASS)
                await page.click("button >> text=Sign In") 
                
                # Wait for home
                await expect(page.get_by_text("Good Morning")).to_be_visible(timeout=10000)
                
                # Add product: Find "Trending Now" section or just first available product card
                # We target the card by data-testid="product-card"
                product_cards = page.get_by_test_id("product-card")
                
                # Wait for at least one card
                await expect(product_cards.first).to_be_visible(timeout=5000)
                count = await product_cards.count()
                
                if count > 0:
                    # Pick a random one or first
                    await product_cards.first.click(force=True)
                    
                    # Wait for Modal "Add to Cart" button (data-testid="add-to-cart-btn")
                    add_btn = page.get_by_test_id("add-to-cart-btn")
                    await expect(add_btn).to_be_visible()
                    await add_btn.click()
                    
                    # Wait for toast or wait a bit
                    await page.wait_for_timeout(1000)
                    
                    # Click "Checkout" floating bar (data-testid="checkout-bar")
                    checkout_bar = page.get_by_test_id("checkout-bar")
                    await expect(checkout_bar).to_be_visible()
                    await checkout_bar.click()
                    
                    # Wait for Checkout View "Pay" button
                    pay_btn = page.get_by_role("button", name="Pay")
                    await expect(pay_btn).to_be_visible()
                    await pay_btn.click()
                    
                    # Expect Success Toast "Order placed successfully" (or CN counterpart)
                    # We can check for the success toast appearance
                    success_toast = page.locator("text=Order placed successfully")
                    await expect(success_toast).to_be_visible(timeout=10000)
                    
                    # Wait for redirection to Pickup tab
                    await page.wait_for_timeout(2000)

                else:
                    print("Warning: No products found to buy.")

                # Logout Student
                await page.goto(f"{BASE_URL_STUDENT}/settings") 
                logout_btn = page.get_by_text("Sign Out")
                if await logout_btn.is_visible():
                     await logout_btn.click()
                
                
                # --- Admin Flow ---
                print("Step 2: Admin Login & Access Dashboard")
                await context.clear_cookies()
                await page.evaluate("sessionStorage.clear(); localStorage.clear();")

                await page.goto(f"{BASE_URL_ADMIN}/login")
                await page.fill("input[type='text']", ADMIN_USER)
                await page.fill("input[type='password']", ADMIN_PASS)
                # Admin login button text is Chinese "登录"
                await page.click("button >> text=登录") 
                
                # Wait for dashboard
                await expect(page.get_by_role("heading", name="运营概览 Dashboard")).to_be_visible(timeout=10000)
                
                # Create User validation (just visit page)
                await page.goto(f"{BASE_URL_ADMIN}/users")
                await expect(page.get_by_role("heading", name="用户管理", level=1)).to_be_visible()
                
                print(f"Iteration {i} SUCCESS")
                
            except Exception as e:
                print(f"Iteration {i} FAILED: {e}")
                await page.screenshot(path=f"failure_iteration_{i}.png")
                # Don't break, keep going to see if it recovers
            finally:
                await context.close()
        
        await browser.close()
        print("\nStress Test Completed.")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
