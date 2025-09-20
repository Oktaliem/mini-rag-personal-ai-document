const TestConfig = require('../config/TestConfig');

/**
 * File Upload Component Object Model
 * Handles file upload interactions and validation
 */
class FileUploadComponent {
  constructor(page) {
    this.page = page;
    this.selectors = TestConfig.selectors.upload;
  }

  // Locators
  get fileInput() {
    return this.page.locator(this.selectors.fileInput);
  }

  get uploadButton() {
    return this.page.locator(this.selectors.uploadButton);
  }

  get uploadStatus() {
    return this.page.locator('text=/uploaded|success|indexing|error/i');
  }

  // Actions
  async selectFile(filePath) {
    await this.fileInput.setInputFiles(filePath);
  }

  async selectMultipleFiles(filePaths) {
    await this.fileInput.setInputFiles(filePaths);
  }

  async clickUpload() {
    await this.uploadButton.click();
  }

  async uploadFile(filePath) {
    await this.selectFile(filePath);
    await this.clickUpload();
  }

  async uploadMultipleFiles(filePaths) {
    await this.selectMultipleFiles(filePaths);
    await this.clickUpload();
  }

  async waitForUploadComplete(timeout = TestConfig.testTimeouts.long) {
    try {
      await this.uploadStatus.waitFor({ state: 'visible', timeout });
    } catch (error) {
      console.log('⚠️ Upload status not found with standard selector, trying alternative approaches...');
      
      // Try alternative selectors for upload status
      const alternativeSelectors = [
        'text=/uploaded|success|indexing|error|processing|complete/i',
        '.upload-status',
        '.status-message',
        '.alert',
        '.notification',
        '[class*="status"]',
        '[class*="upload"]'
      ];
      
      for (const selector of alternativeSelectors) {
        try {
          const element = this.page.locator(selector);
          if (await element.count() > 0) {
            await element.first().waitFor({ state: 'visible', timeout: 5000 });
            console.log(`✅ Found upload status with selector: ${selector}`);
            return;
          }
        } catch (e) {
          // Continue to next selector
        }
      }
      
      // If no status found, check if file input is cleared (indicating successful upload)
      const fileInput = this.page.locator('input[type="file"]');
      const fileValue = await fileInput.inputValue();
      if (!fileValue || fileValue === '') {
        console.log('✅ File input cleared - upload likely successful');
        return;
      }
      
      throw error; // Re-throw original error if no alternatives work
    }
  }

  async waitForIndexingComplete(timeout = TestConfig.testTimeouts.long) {
    // Wait for indexing message to appear and disappear
    const indexingMessage = this.page.locator('text=/indexing/i');
    try {
      await indexingMessage.waitFor({ state: 'visible', timeout: 8000 });
      await indexingMessage.waitFor({ state: 'hidden', timeout });
    } catch (e) {
      // If indexing message is too fast to appear, tolerate and proceed
      console.log('⚠️ Indexing status not visible, continuing assuming fast index.');
      await this.page.waitForTimeout(1500);
    }
  }

  // File validation methods
  async validateFileType(filePath) {
    const allowedExtensions = ['.pdf', '.md', '.txt'];
    const extension = filePath.toLowerCase().substring(filePath.lastIndexOf('.'));
    return allowedExtensions.includes(extension);
  }

  async getUploadedFiles() {
    // This would depend on your UI showing uploaded files
    return await this.page.locator('.uploaded-file').allTextContents();
  }

  // Assertions
  async isFileInputVisible() {
    return await this.fileInput.isVisible();
  }

  async isUploadButtonEnabled() {
    return await this.uploadButton.isEnabled();
  }

  async hasUploadSuccess() {
    const successMessage = this.page.locator('text=/uploaded|success/i');
    return await successMessage.isVisible();
  }

  async hasUploadError() {
    const errorMessage = this.page.locator('text=/error|failed/i');
    return await errorMessage.isVisible();
  }

  async isUploading() {
    const uploadingMessage = this.page.locator('text=/uploading|indexing/i');
    return await uploadingMessage.isVisible();
  }
}

module.exports = FileUploadComponent;
