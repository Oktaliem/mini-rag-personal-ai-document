const TestConfig = require('../config/TestConfig');
const { WaitUtils } = require('../components/WaitUtils');

/**
 * Login Page Object Model
 * Handles all login-related interactions
 */
class LoginPage {
  constructor(page) {
    this.page = page;
    this.selectors = TestConfig.selectors.login;
  }

  // Locators
  get usernameInput() {
    return this.page.locator(this.selectors.usernameInput);
  }

  get passwordInput() {
    return this.page.locator(this.selectors.passwordInput);
  }

  get submitButton() {
    return this.page.locator(this.selectors.submitButton);
  }

  // Actions
  async goto() {
    await this.page.goto(`${TestConfig.baseURL}/login`);
    await WaitUtils.waitForNetworkIdle(this.page, 15000);
  }

  async fillUsername(username) {
    await this.usernameInput.fill(username);
  }

  async fillPassword(password) {
    await this.passwordInput.fill(password);
  }

  async clickSubmit() {
    await this.submitButton.click();
  }

  async login(username, password) {
    await this.fillUsername(username);
    await this.fillPassword(password);
    await this.clickSubmit();
    await WaitUtils.waitForNetworkIdle(this.page, 15000);
  }

  async loginWithDefaultUser() {
    try {
      await this.page.goto('/login', { timeout: 60000 });
      await this.page.fill('input[type="text"], input[name="username"]', 'admin');
      await this.page.fill('input[type="password"]', 'admin123');
      await this.page.click('button[type="submit"], input[type="submit"]');
      await this.page.waitForTimeout(1500);
      await this.waitForLoginSuccess();
    } catch (error) {
      console.log('⚠️ Login error, retrying...');
      await this.page.waitForTimeout(2000);
      await this.page.goto('/login', { timeout: 60000 });
      await this.page.fill('input[type="text"], input[name="username"]', 'admin');
      await this.page.fill('input[type="password"]', 'admin123');
      await this.page.click('button[type="submit"], input[type="submit"]');
      await this.page.waitForTimeout(1500);
      await this.waitForLoginSuccess();
    }
  }

  // Assertions
  async isLoginPage() {
    return await this.page.url().includes('/login');
  }

  async isLoggedIn() {
    return !(await this.isLoginPage());
  }

  async waitForLoginSuccess() {
    await this.page.waitForURL(url => !url.toString().includes('/login'), { timeout: 60000 });
  }
}

module.exports = LoginPage;
