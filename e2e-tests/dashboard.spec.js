const { test, expect } = require('@playwright/test');

test.describe('Dashboard and Main UI', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[type="text"], input[name="username"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"], input[type="submit"]');
    await page.waitForTimeout(3000);
  });

  test('should display main dashboard elements', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check for main header elements
    await expect(page.locator('.header')).toBeVisible();
    
    // Check for main content area
    await expect(page.locator('.container')).toBeVisible();
    
    // Check for common dashboard elements
    const dashboardElements = [
      'text=/Mini RAG/i',
      'text=/AI Document Assistant/i',
      'text=/Upload Files/i',
      'text=/Index Documents/i'
    ];
    
    for (const element of dashboardElements) {
      await expect(page.locator(element).first()).toBeVisible();
    }
  });

  test('should display navigation menu correctly', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check for navigation tabs
    const navLinks = [
      'text=/Upload Files/i',
      'text=/Index Documents/i'
    ];
    
    for (const link of navLinks) {
      await expect(page.locator(link).first()).toBeVisible();
    }
  });

  test('should navigate between different sections', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Test navigation to upload tab
    const uploadTab = page.locator('text=/Upload Files/i').first();
    if (await uploadTab.isVisible()) {
      await uploadTab.click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('text=/Upload Documents/i').first()).toBeVisible();
    }
    
    // Test navigation to index tab
    const indexTab = page.locator('text=/Index Documents/i').first();
    if (await indexTab.isVisible()) {
      await indexTab.click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('text=/Index Documents from Folder/i').first()).toBeVisible();
    }
  });

  test('should display user information', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check for user info display
    // Check for user info elements (may be hidden initially)
    const userInfoElements = [
      '#userInfo',
      '#userWelcome',
      '#userRole'
    ];
    
    // User info might be hidden initially, so we check if elements exist
    for (const element of userInfoElements) {
      await expect(page.locator(element)).toBeAttached();
    }
  });

  test('should handle responsive design', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check if header is visible on desktop
    await expect(page.locator('.header')).toBeVisible();
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Check if mobile navigation works (hamburger menu, etc.)
    const mobileNav = page.locator('button[aria-label*="menu"], .hamburger, .mobile-menu');
    if (await mobileNav.isVisible()) {
      await mobileNav.click();
      await expect(page.locator('nav, .navbar, .navigation')).toBeVisible();
    }
  });

  test('should display system status information', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check for system status indicators
    // Check for status elements that actually exist
    const statusElements = [
      'text=/API Status/i',
      'text=/Documents Indexed/i'
    ];
    
    for (const element of statusElements) {
      await expect(page.locator(element).first()).toBeVisible();
    }
  });
});
