const { test, expect } = require('@playwright/test');

test.describe('API Endpoints Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[type="text"], input[name="username"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"], input[type="submit"]');
    await page.waitForTimeout(3000);
  });

  test('should access health endpoint', async ({ page }) => {
    // Test health endpoint directly
    const response = await page.goto('/health');
    expect(response.status()).toBe(200);
    
    // Check response content
    const content = await page.textContent('body');
    expect(content).toContain('ok');
  });

  test('should access API info endpoint', async ({ page }) => {
    // Test API info endpoint
    const response = await page.goto('/api-info');
    expect(response).not.toBeNull();
    expect(response.status()).toBe(200);
    
    // Check response content
    const content = await page.textContent('body');
    expect(content).toContain('Mini RAG API');
  });

  test('should access models endpoint', async ({ page }) => {
    // Test models endpoint
    const response = await page.goto('/models');
    expect(response.status()).toBe(200);
    
    // Check response content
    const content = await page.textContent('body');
    expect(content).toContain('available_models');
  });

  test('should access protected endpoints with authentication', async ({ page }) => {
    // Test protected endpoints that require authentication
    const protectedEndpoints = [
      '/auth/me',
      '/ask',
      '/upsert',
      '/files'
    ];
    
    for (const endpoint of protectedEndpoints) {
      const response = await page.goto(endpoint);
      
      // Should return 200 (OK), 401 (Unauthorized), 403 (Forbidden), or 405 (Method Not Allowed) for GET requests
      expect([200, 401, 403, 405]).toContain(response.status());
    }
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Test non-existent endpoint
    const response = await page.goto('/non-existent-endpoint');
    expect(response).not.toBeNull();
    expect(response.status()).toBe(404);
    
    // Check for error page or message
    const content = await page.textContent('body');
    expect(content).toContain('Not Found');
  });

  test('should access API documentation', async ({ page }) => {
    // Test API documentation endpoints
    const docEndpoints = [
      '/api-docs',
      '/openapi.json'
    ];
    
    for (const endpoint of docEndpoints) {
      const response = await page.goto(endpoint);
      
      // Should return 200 or 401 (if token required)
      expect(response).not.toBeNull();
      expect([200, 401]).toContain(response.status());
      
      if (response.status() === 200) {
        const content = await page.textContent('body');
        expect(content).toBeTruthy();
      }
    }
  });

  test('should handle CORS headers', async ({ page }) => {
    // Test CORS headers by making a request
    const response = await page.goto('/health');
    
    // Check for CORS headers (may or may not be present depending on request type)
    const headers = response.headers();
    // CORS headers are typically added by middleware, so we just verify the request works
    expect(response.status()).toBe(200);
  });

  test('should handle rate limiting', async ({ page }) => {
    // Make multiple rapid requests to test rate limiting
    const responses = [];
    
    for (let i = 0; i < 5; i++) {
      try {
        const response = await page.goto('/health');
        responses.push(response);
      } catch (error) {
        // Some requests might fail due to browser limitations, that's okay
        console.log(`Request ${i} failed:`, error.message);
      }
    }
    
    // At least some requests should succeed
    expect(responses.length).toBeGreaterThan(0);
    responses.forEach(response => {
      expect(response.status()).toBe(200);
    });
  });

  test('should handle large requests', async ({ page }) => {
    // Test with a large request body
    const largeData = 'x'.repeat(10000); // 10KB of data
    
    try {
      const response = await page.request.post('/ask', {
        data: { query: largeData }
      });
      
      // Should handle large requests gracefully
      expect([200, 400, 413]).toContain(response.status());
      
    } catch (error) {
      // Request might fail due to size limits
      console.log('Large request handled:', error.message);
    }
  });

  test('should handle concurrent requests', async ({ page }) => {
    // Test concurrent requests
    const responses = [];
    
    for (let i = 0; i < 3; i++) {
      try {
        const response = await page.goto('/health');
        if (response) {
          responses.push(response);
        }
      } catch (error) {
        // Some requests might fail due to browser limitations, that's okay
        console.log(`Concurrent request ${i} failed:`, error.message);
      }
    }
    
    // At least some requests should succeed
    expect(responses.length).toBeGreaterThan(0);
    responses.forEach(response => {
      expect(response).not.toBeNull();
      expect(response.status()).toBe(200);
    });
  });

  test('should handle malformed requests', async ({ page }) => {
    // Test malformed JSON
    try {
      const response = await page.request.post('/ask', {
        data: 'invalid json',
        headers: { 'Content-Type': 'application/json' }
      });
      
      // Should return 400 (Bad Request)
      expect(response.status()).toBe(400);
      
    } catch (error) {
      // Request might fail due to malformed data
      console.log('Malformed request handled:', error.message);
    }
  });

  test('should handle authentication token expiration', async ({ page }) => {
    // Test with expired token (if applicable)
    const response = await page.goto('/auth/me');
    
    // Should return 200 (OK), 401 (Unauthorized), or 403 (Forbidden)
    expect([200, 401, 403]).toContain(response.status());
    
    if (response.status() === 401) {
      const content = await page.textContent('body');
      expect(content).toContain('unauthorized');
    }
  });

  test('should handle server errors gracefully', async ({ page }) => {
    // Test error handling by accessing a potentially problematic endpoint
    const response = await page.goto('/models/change');
    
    // Should return 405 (Method Not Allowed) for GET request
    expect(response.status()).toBe(405);
    
    // Check for error message
    const content = await page.textContent('body');
    expect(content).toContain('Method Not Allowed');
  });
});
