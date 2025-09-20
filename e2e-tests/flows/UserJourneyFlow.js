const LoginPage = require('../pages/LoginPage');
const DashboardPage = require('../pages/DashboardPage');
const UploadPage = require('../pages/UploadPage');
const ChatComponent = require('../components/ChatComponent');
const FileUploadComponent = require('../components/FileUploadComponent');
const TestDataBuilder = require('../builders/TestDataBuilder');
const TestConfig = require('../config/TestConfig');

/**
 * User Journey Flow - Fluent Interface Pattern
 * Provides a fluent interface for common user journeys
 */
class UserJourneyFlow {
  constructor(page) {
    this.page = page;
    this.loginPage = new LoginPage(page);
    this.dashboardPage = new DashboardPage(page);
    this.uploadPage = new UploadPage(page);
    this.chatComponent = new ChatComponent(page);
    this.fileUploadComponent = new FileUploadComponent(page);
  }

  // Login Flow
  async loginAs(user) {
    await this.loginPage.goto();
    await this.loginPage.login(user.username, user.password);
    await this.loginPage.waitForLoginSuccess();
    return this;
  }

  async loginAsAdmin() {
    const adminUser = TestDataBuilder.createAdminUser();
    return await this.loginAs(adminUser);
  }

  async loginAsDefault() {
    await this.loginPage.goto();
    await this.loginPage.loginWithDefaultUser();
    await this.loginPage.waitForLoginSuccess();
    // Wait for main page to be ready after login with timeout
    try {
      await this.page.waitForLoadState('networkidle', { timeout: 60000 });
    } catch (error) {
      console.log('⚠️ Network idle timeout, continuing with page load...');
      await this.page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    }
    return this;
  }

  // Dashboard Navigation
  async goToUpload() {
    await this.dashboardPage.switchToUploadTab();
    return this;
  }

  async goToIndex() {
    await this.dashboardPage.switchToIndexTab();
    return this;
  }

  async goToAsk() {
    await this.dashboardPage.switchToAskTab();
    return this;
  }

  // Index Management
  async clearIndex() {
    await this.dashboardPage.clearIndex();
    return this;
  }

  async loadSampleData() {
    await this.dashboardPage.loadSampleData();
    return this;
  }

  async waitForIndexingComplete() {
    await this.dashboardPage.waitForNonZeroDocumentCount();
    await this.dashboardPage.waitForNonZeroChunkCount();
    return this;
  }

  // File Upload Flow
  async uploadFile(filePath) {
    await this.goToUpload();
    await this.fileUploadComponent.uploadFile(filePath);
    await this.fileUploadComponent.waitForUploadComplete();
    return this;
  }

  async uploadTestFiles() {
    const filePaths = await TestDataBuilder.createTestFiles();
    await this.goToUpload();
    await this.fileUploadComponent.uploadMultipleFiles(filePaths);
    await this.fileUploadComponent.waitForUploadComplete();
    return { filePaths };
  }

  // Chat Flow
  async askQuestion(question) {
    const clicked = await this.chatComponent.askQuestion(question);
    if (!clicked) {
      console.log('⚠️ Could not ask question - ask button was disabled');
    }
    return this;
  }

  async askQuestionAndWaitForResponse(question) {
    const clicked = await this.chatComponent.askQuestion(question);
    if (!clicked) {
      console.log('⚠️ Could not ask question - ask button was disabled');
      return { question, response: null, clicked: false };
    }
    const response = await this.chatComponent.waitForResponse();
    return { question, response, clicked: true };
  }

  // Complete User Journeys
  async completeLoginAndUploadJourney(user, filePath) {
    return await this
      .loginAs(user)
      .uploadFile(filePath)
      .waitForIndexingComplete();
  }

  async completeLoginAndAskJourney(user, question) {
    return await this
      .loginAs(user)
      .loadSampleData()
      .waitForIndexingComplete()
      .askQuestionAndWaitForResponse(question);
  }

  async completeFullUserJourney(user, filePath, question) {
    return await this
      .loginAs(user)
      .clearIndex()
      .uploadFile(filePath)
      .waitForIndexingComplete()
      .askQuestionAndWaitForResponse(question);
  }

  // Error Scenario Testing
  async testErrorScenarios() {
    await this.clearIndex();
    
    // Test with no documents
    await this.askQuestion('What is the main topic?');
    
    // Test with very long question
    const longQuestion = 'What is the main topic? '.repeat(100);
    await this.askQuestion(longQuestion);
    
    // Test with special characters
    const specialQuestion = 'What about @#$%^&*()_+{}|:"<>?[]\\;\',./ symbols?';
    await this.askQuestion(specialQuestion);
    
    // Test with empty question
    await this.chatComponent.clearQuestion();
    await this.chatComponent.clickAskButton();
    
    return this;
  }

  // Session Management Testing
  async testSessionPersistence() {
    // Perform actions to establish session
    await this.askQuestion('Test session persistence');
    
    // Test page refresh
    await this.page.reload();
    await this.page.waitForLoadState('networkidle');
    
    // Test tab navigation
    await this.goToUpload();
    await this.goToIndex();
    await this.goToAsk();
    
    return this;
  }

  // Model Selection Testing
  async testAllModelSelections() {
    const modelSelector = this.page.locator(TestConfig.selectors.model.selector);
    const models = await modelSelector.locator('option').all();
    
    const results = [];
    for (let i = 0; i < models.length; i++) {
      const model = models[i];
      const value = await model.getAttribute('value');
      const text = await model.textContent();
      
      if (value && value.trim() !== '') {
        await modelSelector.selectOption(value);
        await this.page.waitForTimeout(500);
        
        // Check for confirmation message
        const confirmationMessage = this.page.locator(`text=/✓ Model changed to ${value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}/`);
        const messageFound = await confirmationMessage.isVisible({ timeout: 1000 });
        
        results.push({
          model: value,
          text: text.trim(),
          success: messageFound
        });
      }
    }
    
    return results;
  }

  // Utility Methods
  async takeScreenshot(name) {
    await this.page.screenshot({ 
      path: `e2e-reports/test-artifacts/${name}.png`, 
      fullPage: true 
    });
    return this;
  }

  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
    return this;
  }

  async refreshPage() {
    await this.page.reload();
    await this.page.waitForLoadState('networkidle');
    return this;
  }
}

module.exports = UserJourneyFlow;
