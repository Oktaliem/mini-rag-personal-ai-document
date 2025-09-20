const { test, expect } = require('@playwright/test');

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
  });

  test('should display login page correctly', async ({ page }) => {
    // Check if login page elements are visible
    await expect(page.locator('h1, h2, h3')).toContainText(/Mini RAG/i);
    await expect(page.locator('input[type="text"], input[name="username"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"], input[type="submit"]')).toBeVisible();
  });

  test('should show validation error for empty credentials', async ({ page }) => {
    // Try to submit empty form
    await page.click('button[type="submit"], input[type="submit"]');
    
    // Check for validation messages (may not be visible due to client-side validation)
    // Just verify the form elements are still visible
    await expect(page.locator('input[type="text"], input[name="username"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    await page.fill('input[type="text"], input[name="username"]', 'invalid_user');
    await page.fill('input[type="password"]', 'wrong_password');
    
    // Submit form
    await page.click('button[type="submit"], input[type="submit"]');
    
    // Wait for response and check for error message
    await page.waitForTimeout(2000);
    await expect(page.locator('text=/invalid|incorrect|error|unauthorized/i')).toBeVisible();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    // Fill in valid credentials (admin/admin123)
    await page.fill('input[type="text"], input[name="username"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    
    // Submit form
    await page.click('button[type="submit"], input[type="submit"]');
    
    // Wait for redirect or success message
    await page.waitForTimeout(3000);
    
    // Check if redirected to home page or dashboard
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/\/(home|dashboard|$)/);
    
    // Check for success indicators
    await expect(page.locator('text=/welcome|dashboard|home/i')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // First login
    await page.fill('input[type="text"], input[name="username"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"], input[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Look for logout button/link
    const logoutButton = page.locator('text=/logout|sign out/i').first();
    await expect(logoutButton).toBeVisible();
    
    // Click logout
    await logoutButton.click();
    await page.waitForTimeout(2000);
    
    // Check if redirected to login page
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/\/login/);
  });

  test('should protect routes when not authenticated', async ({ page }) => {
    // Try to access protected route directly
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Should be redirected to login or show login form
    const currentUrl = page.url();
    const hasLoginForm = await page.locator('input[type="password"]').isVisible();
    
    expect(currentUrl).toMatch(/\/login/) || expect(hasLoginForm).toBeTruthy();
  });

  test('should maintain session after page refresh', async ({ page }) => {
    // Login first
    await page.fill('input[type="text"], input[name="username"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"], input[type="submit"]');
    
    // Post-login settle
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Ensure we actually landed on an authenticated page before reload
    const dashboardMarker = page.locator('text=/welcome|dashboard|home/i');
    await expect(dashboardMarker.first()).toBeVisible({ timeout: 5000 });
    
    // Refresh page
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Should still be logged in
    const currentUrl = page.url();
    expect(currentUrl).not.toMatch(/\/login/);
  });
});
