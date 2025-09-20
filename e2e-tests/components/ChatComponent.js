const TestConfig = require('../config/TestConfig');

/**
 * Chat Component Object Model
 * Handles chat interface interactions
 */
class ChatComponent {
  constructor(page) {
    this.page = page;
    this.selectors = TestConfig.selectors.chat;
  }

  // Locators
  get questionInput() {
    return this.page.locator(this.selectors.questionInput);
  }

  get askButton() {
    return this.page.locator(this.selectors.askButton);
  }

  get chatContainer() {
    return this.page.locator(this.selectors.chatContainer);
  }

  // Actions
  async fillQuestion(question) {
    await this.questionInput.fill(question);
  }

  async clearQuestion() {
    await this.questionInput.clear();
  }

  async clickAskButton() {
    // Check if button is enabled before clicking
    const isEnabled = await this.askButton.isEnabled();
    if (!isEnabled) {
      console.log('⚠️ Ask button is disabled - cannot click');
      return false;
    }
    await this.askButton.click();
    return true;
  }

  async askQuestion(question) {
    // Wait for the page to be fully loaded
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForTimeout(2000);
    
    await this.fillQuestion(question);
    const clicked = await this.clickAskButton();
    return clicked;
  }

  async waitForResponse(timeout = TestConfig.testTimeouts.long) {
    // Wait for chat container to have content
    await this.chatContainer.waitFor({ state: 'visible', timeout });
    
    // Try multiple selectors for assistant answer (using .first() to avoid strict mode violations)
    const assistantAnswerSelectors = [
      '.assistant p:first-of-type',
      '.message.assistant p:first-of-type',
      '.bubble.assistant p:first-of-type',
      'div[class*="assistant"] p:first-of-type',
      'text=/Hello|Hi|I can|I am|I\'m/'
    ];
    
    // Retry logic for up to 1 minute (60 seconds)
    const maxAttempts = 20; // 20 attempts * 3 seconds = 60 seconds
    const waitTime = 3000; // 3 seconds between attempts
    let answerFound = false;
    let answerText = '';
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        // Try each selector
        for (const selector of assistantAnswerSelectors) {
          const element = this.page.locator(selector).first();
          if (await element.isVisible()) {
            answerText = await element.textContent();
            if (answerText && answerText.trim().length > 0) {
              console.log(`✅ Assistant answer found on attempt ${attempt} with selector "${selector}": "${answerText.substring(0, 50)}..."`);
              answerFound = true;
              break;
            }
          }
        }
        
        if (answerFound) break;
        
        console.log(`Attempt ${attempt}/${maxAttempts}: Assistant answer not ready yet, waiting ${waitTime/1000} seconds...`);
        if (attempt < maxAttempts) {
          await this.page.waitForTimeout(waitTime);
        }
      } catch (error) {
        console.log(`Attempt ${attempt}/${maxAttempts}: Error checking for answer: ${error.message}`);
        if (attempt < maxAttempts) {
          await this.page.waitForTimeout(waitTime);
        }
      }
    }
    
    if (!answerFound) {
      throw new Error('Assistant answer not found after 1 minute of waiting');
    }
    
    return answerText;
  }

  // Chat element verification methods
  async getUserAvatar() {
    return this.page.locator('div[class*="message user"] div[class*="avatar"]');
  }

  async getUserText() {
    return this.page.locator('div.message-meta:has-text("You")');
  }

  async getUserMessage(message) {
    return this.page.locator(`.message.user .message-content:has-text("${message}")`);
  }

  async getAssistantEmoji() {
    // Try multiple selectors for assistant emoji
    const selectors = [
      '.message.assistant .avatar:has-text("🤖")',
      '.message.assistant .avatar',
      '.avatar:has-text("🤖")',
      '.message.assistant .avatar[text*="🤖"]'
    ];
    
    for (const selector of selectors) {
      const element = this.page.locator(selector);
      if (await element.count() > 0) {
        return element.first();
      }
    }
    
    // Fallback to the original selector
    return this.page.locator('.message.assistant .avatar:has-text("🤖")');
  }

  async getAssistantText() {
    return this.page.locator('.message.assistant .message-meta:has-text("Assistant")');
  }

  async getAssistantAnswer() {
    const selectors = [
      '.assistant p:first-of-type',
      '.message.assistant p:first-of-type',
      '.bubble.assistant p:first-of-type'
    ];

    for (const selector of selectors) {
      try {
        const element = this.page.locator(selector).first();
        if (await element.isVisible()) {
          return element;
        }
      } catch (error) {
        // Continue to next selector
      }
    }
    return null;
  }

  // Assertions
  async isQuestionInputVisible() {
    return await this.questionInput.isVisible();
  }

  async isAskButtonEnabled() {
    return await this.askButton.isEnabled();
  }

  async isChatContainerEmpty() {
    const content = await this.chatContainer.textContent();
    return !content || content.trim() === '';
  }

  async hasUserMessage(message) {
    const userMessage = await this.getUserMessage(message);
    return await userMessage.isVisible();
  }

  async hasAssistantResponse() {
    const answer = await this.getAssistantAnswer();
    return answer !== null && await answer.isVisible();
  }
}

module.exports = ChatComponent;
