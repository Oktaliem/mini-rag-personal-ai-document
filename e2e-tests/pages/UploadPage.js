const TestConfig = require('../config/TestConfig');

/**
 * Upload Page Object Model
 * Handles file upload interactions
 */
class UploadPage {
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

  // Actions
  async goto() {
    await this.page.goto(TestConfig.baseURL);
    await this.page.waitForLoadState('networkidle');
  }

  async selectFiles(filePaths) {
    await this.fileInput.setInputFiles(filePaths);
  }

  async uploadFiles(filePaths) {
    await this.selectFiles(filePaths);
    await this.uploadButton.click();
  }

  async waitForUploadSuccess(timeout = TestConfig.testTimeouts.medium) {
    const uploadSuccess = this.page.locator('text=/uploaded|success|indexing/i');
    await uploadSuccess.waitFor({ state: 'visible', timeout });
  }

  // Assertions
  async isUploadButtonEnabled() {
    return await this.uploadButton.isEnabled();
  }

  async isFileInputVisible() {
    return await this.fileInput.isVisible();
  }
}

module.exports = UploadPage;
