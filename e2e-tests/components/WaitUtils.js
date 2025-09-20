class WaitUtils {
  static async waitForSelectorSafe(page, selector, timeout = 10000) {
    try {
      return await page.waitForSelector(selector, { timeout });
    } catch (e) {
      return null;
    }
  }

  static async waitForNetworkIdle(page, timeout = 10000) {
    try {
      await page.waitForLoadState('networkidle', { timeout });
      return true;
    } catch (e) {
      return false;
    }
  }
}

module.exports = { WaitUtils };

