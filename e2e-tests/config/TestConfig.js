/**
 * Test Configuration for Mini RAG E2E Tests
 * Centralized configuration management
 */
class TestConfig {
  static get baseURL() {
    return process.env.BASE_URL || 'http://localhost:8000';
  }

  static get timeout() {
    return process.env.TIMEOUT || 30000;
  }

  static get headless() {
    return process.env.E2E_HEADLESS === '1';
  }

  static get defaultUser() {
    return {
      username: 'admin',
      password: 'admin123'
    };
  }

  static get testTimeouts() {
    return {
      short: 10000,
      medium: 30000,
      long: 120000,  // Back to 120s for normal model testing
      veryLong: 180000  // 180s for very long operations only
    };
  }

  static get selectors() {
    return {
      login: {
        usernameInput: 'input[type="text"], input[name="username"]',
        passwordInput: 'input[type="password"]',
        submitButton: 'button[type="submit"], input[type="submit"]'
      },
      tabs: {
        upload: 'div.tab[onclick="switchTab(\'upload\')"]',
        index: 'div.tab[onclick="switchTab(\'index\')"]',
        ask: 'div.tab:has-text("Ask Questions")'
      },
      upload: {
        fileInput: 'input[type="file"]',
        uploadButton: 'button#uploadBtn'
      },
      chat: {
        questionInput: '#questionInput',
        askButton: '#askBtn',
        chatContainer: '#chatContainer'
      },
      index: {
        clearButton: 'button[onclick="clearIndex()"]',
        loadSampleButton: 'text=/load sample data/i',
        docCount: '#docCount',
        chunkCount: '#chunkCount'
      },
      model: {
        selector: 'select#modelSelect, .model-selector, select[name="model"], select[id="model"]'
      }
    };
  }
}

module.exports = TestConfig;
