/**
 * Global teardown for E2E tests
 * This runs once after all tests are completed
 */
async function globalTeardown(config) {
  console.log('🧹 Starting E2E test global teardown...');
  
  try {
    // Clean up any test data
    console.log('🗑️ Cleaning up test data...');
    
    // Stop Docker containers if running in CI
    if (process.env.CI) {
      console.log('🐳 Stopping Docker containers...');
      const { execSync } = require('child_process');
      
      try {
        execSync('docker-compose down', { 
          stdio: 'inherit',
          timeout: 30000 // 30 seconds timeout
        });
        console.log('✅ Docker containers stopped successfully');
      } catch (error) {
        console.log('⚠️ Warning: Failed to stop Docker containers:', error.message);
      }
    }
    
    // Clean up any temporary files
    console.log('🧽 Cleaning up temporary files...');
    
    // Remove any test files that might have been created
    const fs = require('fs');
    const path = require('path');
    
    const testDirs = ['test-reports', 'e2e-reports'];
    
    for (const dir of testDirs) {
      if (fs.existsSync(dir)) {
        try {
          // Keep the directory but clean up old files
          const files = fs.readdirSync(dir);
          const now = Date.now();
          const maxAge = 24 * 60 * 60 * 1000; // 24 hours
          
          for (const file of files) {
            const filePath = path.join(dir, file);
            const stats = fs.statSync(filePath);
            
            if (now - stats.mtime.getTime() > maxAge) {
              if (stats.isDirectory()) {
                fs.rmSync(filePath, { recursive: true, force: true });
              } else {
                fs.unlinkSync(filePath);
              }
              console.log(`🗑️ Cleaned up old file: ${filePath}`);
            }
          }
        } catch (error) {
          console.log(`⚠️ Warning: Failed to clean up ${dir}:`, error.message);
        }
      }
    }
    
    console.log('✅ Global teardown completed successfully!');
    
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw error in teardown to avoid masking test failures
  }
}

module.exports = globalTeardown;
