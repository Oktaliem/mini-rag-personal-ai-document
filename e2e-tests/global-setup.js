const { chromium } = require('@playwright/test');

/**
 * Global setup for E2E tests
 * This runs once before all tests
 */
async function globalSetup(config) {
  console.log('🚀 Starting E2E test global setup...');
  
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Wait for the application to be ready with exponential backoff
    console.log('⏳ Waiting for application to be ready...');

    const maxRetries = 12;
    let retries = 0;
    let delay = 2500; // start with 2.5s

    while (retries < maxRetries) {
      try {
        const response = await page.goto('http://localhost:8000/health', {
          timeout: 10000,
          waitUntil: 'load'
        });

        if (response && response.ok()) {
          console.log('✅ Application is ready!');
          break;
        }
      } catch (error) {
        console.log(`⏳ Attempt ${retries + 1}/${maxRetries}: Not ready (${error.message}). Retrying in ${Math.round(delay/1000)}s...`);
        await page.waitForTimeout(delay);
        delay = Math.min(delay * 1.5, 15000); // cap at 15s
        retries++;
      }
    }

    if (retries >= maxRetries) {
      throw new Error('❌ Application failed to start within timeout period');
    }
    
    // Verify all key endpoints are accessible
    console.log('🔍 Verifying key endpoints...');
    
    const endpoints = [
      { url: 'http://localhost:8000/health', name: 'Health' },
      { url: 'http://localhost:8000/api-info', name: 'API Info' },
      { url: 'http://localhost:8000/models', name: 'Models' },
      { url: 'http://localhost:8000/', name: 'Home Page' },
      { url: 'http://localhost:8000/login', name: 'Login Page' }
    ];
    
    for (const endpoint of endpoints) {
      try {
        const response = await page.goto(endpoint.url, { 
          timeout: 10000,
          waitUntil: 'networkidle'
        });
        
        if (response && response.ok()) {
          console.log(`✅ ${endpoint.name} endpoint is accessible`);
        } else {
          console.log(`⚠️ ${endpoint.name} endpoint returned status: ${response?.status()}`);
        }
      } catch (error) {
        console.log(`❌ ${endpoint.name} endpoint failed: ${error.message}`);
      }
    }
    
    // Set up test data if needed
    console.log('📝 Setting up test data...');
    
    // Create a test user if needed (this would depend on your auth setup)
    // For now, we'll just verify the login page is accessible
    await page.goto('http://localhost:8000/login');
    await page.waitForLoadState('networkidle');
    
    console.log('✅ Global setup completed successfully!');
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

module.exports = globalSetup;
