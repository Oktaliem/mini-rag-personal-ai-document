const fs = require('fs');
const path = require('path');

/**
 * Test Data Builder for creating test files and users
 * Implements Builder Pattern for flexible test data creation
 */
class TestDataBuilder {
  constructor() {
    this.testDir = path.join(__dirname, '../test-files');
    this.files = [];
    this.user = {
      username: 'admin',
      password: 'admin123',
      role: 'admin'
    };
  }

  // User Builder Methods
  withUsername(username) {
    this.user.username = username;
    return this;
  }

  withPassword(password) {
    this.user.password = password;
    return this;
  }

  withRole(role) {
    this.user.role = role;
    return this;
  }

  // File Builder Methods
  withTextFile(filename = 'test-document.txt', content = 'This is a test text document for E2E testing.') {
    this.files.push({
      name: filename,
      content: content,
      type: 'txt'
    });
    return this;
  }

  withMarkdownFile(filename = 'test-guide.md', content = '# Test Guide\n\nThis is a markdown document for testing.\n\n## Features\n- File upload\n- Document indexing\n- Text processing') {
    this.files.push({
      name: filename,
      content: content,
      type: 'md'
    });
    return this;
  }

  withCustomFile(filename, content, type) {
    this.files.push({
      name: filename,
      content: content,
      type: type
    });
    return this;
  }

  // Build Methods
  buildUser() {
    return { ...this.user };
  }

  async buildFiles() {
    // Create test directory if it doesn't exist
    if (!fs.existsSync(this.testDir)) {
      fs.mkdirSync(this.testDir, { recursive: true });
    }

    const filePaths = [];
    for (const file of this.files) {
      const filePath = path.join(this.testDir, file.name);
      fs.writeFileSync(filePath, file.content);
      filePaths.push(filePath);
    }
    return filePaths;
  }

  async cleanupFiles() {
    // Clean up test files
    for (const file of this.files) {
      const filePath = path.join(this.testDir, file.name);
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    }
    
    // Remove test directory if empty
    if (fs.existsSync(this.testDir) && fs.readdirSync(this.testDir).length === 0) {
      fs.rmdirSync(this.testDir);
    }
  }

  static async cleanupFiles() {
    const testDir = path.join(__dirname, '../test-files');
    if (fs.existsSync(testDir)) {
      const files = fs.readdirSync(testDir);
      for (const file of files) {
        fs.unlinkSync(path.join(testDir, file));
      }
      fs.rmdirSync(testDir);
    }
  }

  // Static factory methods for common scenarios
  static createAdminUser() {
    return new TestDataBuilder()
      .withUsername('admin')
      .withPassword('admin123')
      .withRole('admin')
      .buildUser();
  }

  static createTestUser() {
    return new TestDataBuilder()
      .withUsername('testuser')
      .withPassword('testpass123')
      .withRole('user')
      .buildUser();
  }

  static async createTestFiles() {
    return await new TestDataBuilder()
      .withTextFile('test-document.txt', 'This is a test text document for E2E testing. It contains sample content to verify file upload functionality.')
      .withMarkdownFile('test-guide.md', '# Test Guide\n\nThis is a markdown document for testing.\n\n## Features\n- File upload\n- Document indexing\n- Text processing')
      .buildFiles();
  }

  static async createLongContentFile() {
    return await new TestDataBuilder()
      .withTextFile('long-content.txt', 'This is a very long document. '.repeat(1000))
      .buildFiles();
  }
}

module.exports = TestDataBuilder;
