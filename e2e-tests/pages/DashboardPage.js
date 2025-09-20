const TestConfig = require('../config/TestConfig');
const { WaitUtils } = require('../components/WaitUtils');

/**
 * Dashboard Page Object Model
 * Handles main dashboard interactions and navigation
 */
class DashboardPage {
  constructor(page) {
    this.page = page;
    this.selectors = TestConfig.selectors;
  }

  // Locators
  get uploadTab() {
    return this.page.locator(this.selectors.tabs.upload);
  }

  get indexTab() {
    return this.page.locator(this.selectors.tabs.index);
  }

  get askTab() {
    return this.page.locator(this.selectors.tabs.ask);
  }

  get docCount() {
    return this.page.locator(this.selectors.index.docCount);
  }

  get chunkCount() {
    return this.page.locator(this.selectors.index.chunkCount);
  }

  get clearButton() {
    return this.page.locator(this.selectors.index.clearButton);
  }

  get loadSampleButton() {
    // Use the robust selector strategy from the original script
    return this.page.locator('text=/load sample data/i').first();
  }

  // Actions
  async goto() {
    await this.page.goto(TestConfig.baseURL);
    await WaitUtils.waitForNetworkIdle(this.page, 15000);
  }

  async switchToUploadTab() {
    await this.uploadTab.click();
    await this.page.waitForTimeout(1000);
  }

  async switchToIndexTab() {
    await this.indexTab.click();
    await this.page.waitForTimeout(1000);
  }

  async switchToAskTab() {
    // Ask Questions section is always visible, no tab to click
    // Just ensure we're on the main page
    await WaitUtils.waitForNetworkIdle(this.page, 10000);
  }

  async clearIndex() {
    await this.switchToIndexTab();
    
    // Set up dialog handler to automatically click OK on confirmation popup
    this.page.on('dialog', async dialog => {
      console.log(`Dialog appeared: ${dialog.message()}`);
      await dialog.accept(); // Click OK
    });
    
    await this.clearButton.click();
    console.log('✅ Step 3: Clear Index button clicked and confirmation accepted');
    
    // Step 4: Ensure "✅ All data cleared" message is displayed
    // The message appears and disappears quickly, so we need to poll for it
    let successMessage = null;
    let attempts = 0;
    const maxAttempts = 10;
    const pollInterval = 300; // 300ms
    
    console.log('Polling for success message...');
    
    while (!successMessage && attempts < maxAttempts) {
      attempts++;
      console.log(`Attempt ${attempts}/${maxAttempts} - Looking for success message...`);
      
      const messageElement = this.page.locator('div.status.success').first();
      if (await messageElement.isVisible({ timeout: 100 })) {
        const messageText = await messageElement.textContent();
        if (messageText && messageText.includes('All data cleared')) {
          successMessage = messageElement;
          break;
        }
      }
      
      if (attempts < maxAttempts) {
        await this.page.waitForTimeout(pollInterval);
      }
    }
    
    if (successMessage) {
      console.log('✅ Step 4: Success message "All data cleared" displayed');
    } else {
      console.log('⚠️ Step 4: Success message not found within polling attempts');
    }
    
    // Wait a bit to see the message before it disappears
    await this.page.waitForTimeout(2000);
  }

  async loadSampleData() {
    await this.switchToIndexTab();
    
    // Try multiple strategies to find the load sample data button
    let loadSampleDataButton = null;
    
    // Strategy 1: Look for exact text matches
    const exactMatches = [
      'text=/load sample data/i',
      'text=/sample data/i', 
      'text=/load sample/i',
      'text=/load.*sample/i'
    ];
    
    for (const selector of exactMatches) {
      const button = this.page.locator(selector).first();
      if (await button.isVisible()) {
        loadSampleDataButton = button;
        break;
      }
    }
    
    // Strategy 2: Look for buttons with sample/load related text
    if (!loadSampleDataButton) {
      const buttonSelectors = [
        'button:has-text("Load")',
        'button:has-text("Sample")', 
        'button:has-text("Data")',
        '[data-testid*="sample"]',
        '[data-testid*="load"]',
        '[class*="sample"]',
        '[class*="load"]'
      ];
      
      for (const selector of buttonSelectors) {
        const button = this.page.locator(selector).first();
        if (await button.isVisible()) {
          const buttonText = await button.textContent();
          if (buttonText && /sample|load|data/i.test(buttonText)) {
            loadSampleDataButton = button;
            break;
          }
        }
      }
    }
    
    // Strategy 3: Look for any clickable element with sample data related text
    if (!loadSampleDataButton) {
      const clickableElements = this.page.locator('button, a, [role="button"], [onclick]').filter({ hasText: /sample|load|data/i });
      if (await clickableElements.count() > 0) {
        loadSampleDataButton = clickableElements.first();
      }
    }
    
    // If still not found, throw an error with helpful information
    if (!loadSampleDataButton) {
      throw new Error('Load Sample Data button not found. Check if the button exists on the page.');
    }
    
    // Click the button
    await loadSampleDataButton.click();
    console.log('Clicked Load Sample Data button');
    
    // Step 3: Ensure popup message "Indexing documents..." is displayed
    // Wait for any indexing/processing message to appear
    const indexingMessageSelectors = [
      'text=/indexing documents/i',
      'text=/processing documents/i', 
      'text=/loading documents/i',
      'text=/indexing/i',
      'text=/processing/i',
      'text=/loading/i',
      '[class*="loading"]',
      '[class*="processing"]',
      '[class*="indexing"]'
    ];
    
    let indexingMessage = null;
    for (const selector of indexingMessageSelectors) {
      const element = this.page.locator(selector).first();
      if (await element.isVisible({ timeout: 5000 })) {
        indexingMessage = element;
        break;
      }
    }
    
    if (!indexingMessage) {
      // Wait a bit more and try again
      await this.page.waitForTimeout(2000);
      for (const selector of indexingMessageSelectors) {
        const element = this.page.locator(selector).first();
        if (await element.isVisible({ timeout: 3000 })) {
          indexingMessage = element;
          break;
        }
      }
    }
    
    // Verify the indexing message is visible
    if (indexingMessage) {
      console.log('Indexing message is visible');
    }
    
    // Step 4: Wait for the popup message to disappear (indicating completion)
    if (indexingMessage) {
      await indexingMessage.waitFor({ state: 'hidden', timeout: 60000 }); // Allow up to 60 seconds for indexing
      console.log('Indexing completed - message disappeared');
    }
  }

  // Data retrieval methods
  async getDocumentCount() {
    const text = await this.docCount.textContent();
    return parseInt(text) || 0;
  }

  async getChunkCount() {
    const text = await this.chunkCount.textContent();
    return parseInt(text) || 0;
  }

  // Wait methods with retry logic
  async waitForDocumentCount(expectedCount, maxAttempts = 10, waitTime = 2000) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const currentCount = await this.getDocumentCount();
      
      if (currentCount === expectedCount) {
        return currentCount;
      }
      
      if (attempt < maxAttempts) {
        await this.page.waitForTimeout(waitTime);
        await this.page.reload();
        await this.page.waitForLoadState('networkidle', { timeout: 60000 });
      }
    }
    
    throw new Error(`Document count did not reach ${expectedCount} after ${maxAttempts} attempts`);
  }

  async waitForNonZeroDocumentCount(maxAttempts = 40, waitTime = 3000) {
    // Wait up to 120 seconds for document count to be non-zero, refreshing page if needed
    let documentCountValue = "0";
    let indexedCountNum = 0;
    let attempts = 0;

    console.log('Checking document count - waiting for non-zero value...');

    while (indexedCountNum === 0 && attempts < maxAttempts) {
      attempts++;
      console.log(`Attempt ${attempts}/${maxAttempts} - Checking document count...`);

      // Look for the document count element by ID
      const documentCountElement = this.page.locator('#docCount').first();

      if (await documentCountElement.isVisible()) {
        documentCountValue = await documentCountElement.textContent();
        indexedCountNum = parseInt(documentCountValue);
        console.log(`Found document count: "${documentCountValue}" (parsed: ${indexedCountNum})`);
      } else {
        // Try alternative selectors if ID not found
        const documentIndexedText = this.page.locator('text=/Documents Indexed/i').first();
        if (await documentIndexedText.isVisible()) {
          const parent = documentIndexedText.locator('..');
          const numbers = parent.locator('text=/\\d+/');
          if (await numbers.count() > 0) {
            documentCountValue = await numbers.first().textContent();
            indexedCountNum = parseInt(documentCountValue);
            console.log(`Found document count via text: "${documentCountValue}" (parsed: ${indexedCountNum})`);
          }
        }
      }

      // If count is still 0 and we haven't reached max attempts, wait and refresh
      if (indexedCountNum === 0 && attempts < maxAttempts) {
        console.log(`Document count is still 0, waiting ${waitTime/1000} seconds before refresh...`);
        await this.page.waitForTimeout(waitTime);

        // Refresh the page to get updated counts
        console.log('Refreshing page to get updated document count...');
        await this.page.reload({ timeout: 60000 }); // Increased reload timeout
        await this.page.waitForLoadState('networkidle', { timeout: 60000 });
      }
    }

    // Log the final result
    console.log(`Final document count after ${attempts} attempts: "${documentCountValue}" (parsed: ${indexedCountNum})`);

    // Assert that we found a non-zero document count
    if (indexedCountNum === 0) {
      throw new Error(`Document count did not become non-zero after ${maxAttempts} attempts`);
    }

    console.log(`✅ Document Indexed count: ${indexedCountNum} (verified after ${attempts} attempts)`);
    return indexedCountNum;
  }

  async waitForNonZeroChunkCount(maxAttempts = 30, waitTime = 3000) {
    // Wait up to 90 seconds for chunks count to be non-zero, refreshing page if needed
    let chunksCountValue = "0";
    let chunksCountNum = 0;
    let chunksAttempts = 0;

    console.log('Checking chunks count - waiting for non-zero value...');

    while (chunksCountNum === 0 && chunksAttempts < maxAttempts) {
      chunksAttempts++;
      console.log(`Chunks attempt ${chunksAttempts}/${maxAttempts} - Checking chunks count...`);

      // Look for the chunks count element by ID
      const chunksCountElement = this.page.locator('#chunkCount').first();

      if (await chunksCountElement.isVisible()) {
        chunksCountValue = await chunksCountElement.textContent();
        chunksCountNum = parseInt(chunksCountValue);
        console.log(`Found chunks count: "${chunksCountValue}" (parsed: ${chunksCountNum})`);
      } else {
        // Try alternative selectors if ID not found
        const textChunksText = this.page.locator('text=/Text Chunks/i').first();
        if (await textChunksText.isVisible()) {
          const parent = textChunksText.locator('..');
          const numbers = parent.locator('text=/\\d+/');
          if (await numbers.count() > 0) {
            chunksCountValue = await numbers.first().textContent();
            chunksCountNum = parseInt(chunksCountValue);
            console.log(`Found chunks count via text: "${chunksCountValue}" (parsed: ${chunksCountNum})`);
          }
        }
      }

      // If count is still 0 and we haven't reached max attempts, wait and refresh
      if (chunksCountNum === 0 && chunksAttempts < maxAttempts) {
        console.log(`Chunks count is still 0, waiting ${waitTime/1000} seconds before refresh...`);
        await this.page.waitForTimeout(waitTime);

        // Refresh the page to get updated counts
        console.log('Refreshing page to get updated chunks count...');
        await this.page.reload();
        await this.page.waitForLoadState('networkidle', { timeout: 60000 });
      }
    }

    // Log the final result
    console.log(`Final chunks count after ${chunksAttempts} attempts: "${chunksCountValue}" (parsed: ${chunksCountNum})`);

    // Assert that we found a non-zero chunks count
    if (chunksCountNum === 0) {
      throw new Error(`Chunk count did not become non-zero after ${maxAttempts} attempts`);
    }

    console.log(`✅ Text chunks count: ${chunksCountNum} (verified after ${chunksAttempts} attempts)`);
    return chunksCountNum;
  }

  // Assertions
  async isOnDashboard() {
    return !(await this.page.url().includes('/login'));
  }

  async hasDocumentCount(count) {
    const currentCount = await this.getDocumentCount();
    return currentCount === count;
  }

  async hasChunkCount(count) {
    const currentCount = await this.getChunkCount();
    return currentCount === count;
  }
}

module.exports = DashboardPage;
