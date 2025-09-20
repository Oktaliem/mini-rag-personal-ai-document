// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Custom Playwright configuration for User Journey Tests
 * This configuration captures videos and screenshots for ALL tests (passed and failed)
 */
module.exports = defineConfig({
  testDir: './e2e-tests/specs',
  testMatch: '**/specs/user-journey.spec.js',
  
  /* Run tests in files in parallel */
  fullyParallel: false, // Run user journey tests sequentially for better video capture
  
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 1 : 0,
  
  /* Use single worker for user journey tests - CRITICAL for sequential execution */
  workers: 1,
  
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { outputFolder: 'e2e-reports/user-journey-html' }],
    ['json', { outputFile: 'e2e-reports/user-journey-results.json' }],
    ['junit', { outputFile: 'e2e-reports/user-journey-results.xml' }],
    ['list']
  ],
  
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:8000',

    /* Headless mode controlled via env var E2E_HEADLESS (default false) */
    headless: process.env.E2E_HEADLESS === '1',

    /* Collect trace for all tests */
    trace: 'on',
    
    /* Take screenshot for all tests */
    screenshot: 'on',
    
    /* Record video for all tests (both passed and failed) */
    video: 'on',
    
    /* Global timeout for each action */
    actionTimeout: 15000,
    
    /* Global timeout for navigation */
    navigationTimeout: 30000,
  },

  /* Output directory for test artifacts */
  outputDir: 'e2e-reports/test-artifacts',

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Custom viewport size
        viewport: { width: 1000, height: 1100 },
        // Additional video settings for better quality - record ALL tests
        video: {
          mode: 'on', // Record all tests, not just failures
          size: { width: 1000, height: 1100 }
        }
      },
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'docker-compose up -d',
    url: 'http://localhost:8000/health',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000, // 2 minutes
  },

  /* Global setup and teardown */
  globalSetup: require.resolve('./e2e-tests/global-setup.js'),
  globalTeardown: require.resolve('./e2e-tests/global-teardown.js'),

  /* Test timeout - longer for user journey tests */
  timeout: 120000, // 2 minutes
  
  /* Expect timeout */
  expect: {
    timeout: 15000,
  },
});
