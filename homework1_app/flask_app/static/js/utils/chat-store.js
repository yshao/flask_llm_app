/**
 * Global Chat Store
 * Maintains chat state across route changes
 */

// Global chat store
const ChatStore = {
  // Chat state
  messages: [],
  aiMessageCount: 0,
  isConnected: false,
  
  // Initialize store
  init() {
    // Load from localStorage if available
    this.loadFromStorage();
    
    // Save to localStorage whenever state changes
    this.setupAutoSave();
  },
  
  // Add message to chat
  addMessage(role, content, isTyping = false, customStyle = null) {
    const message = {
      role,
      content,
      isTyping,
      customStyle,
      id: Date.now() + Math.random(),
      timestamp: new Date().toISOString()
    };
    
    this.messages.push(message);
    this.saveToStorage();
    return message;
  },
  
  // Remove typing indicator
  removeTypingIndicator() {
    const typingIndex = this.messages.findIndex(msg => msg.isTyping);
    console.log('ChatStore: Looking for typing indicator, found at index:', typingIndex);
    if (typingIndex !== -1) {
      this.messages.splice(typingIndex, 1);
      this.saveToStorage();
      console.log('ChatStore: Typing indicator removed, messages count:', this.messages.length);
    } else {
      console.log('ChatStore: No typing indicator found to remove');
    }
  },
  
  // Increment AI message count
  incrementAICount() {
    this.aiMessageCount++;
    this.saveToStorage();
  },
  
  // Set connection status
  setConnectionStatus(status) {
    this.isConnected = status;
    this.saveToStorage();
  },
  
  // Clear chat history
  clearChat() {
    this.messages = [];
    this.aiMessageCount = 0;
    this.saveToStorage();
  },
  
  // Save to localStorage
  saveToStorage() {
    try {
      localStorage.setItem('chat-store', JSON.stringify({
        messages: this.messages,
        aiMessageCount: this.aiMessageCount,
        isConnected: this.isConnected
      }));
    } catch (error) {
      console.warn('Failed to save chat state to localStorage:', error);
    }
  },
  
  // Load from localStorage
  loadFromStorage() {
    try {
      const stored = localStorage.getItem('chat-store');
      if (stored) {
        const data = JSON.parse(stored);
        this.messages = data.messages || [];
        this.aiMessageCount = data.aiMessageCount || 0;
        this.isConnected = data.isConnected || false;
      }
    } catch (error) {
      console.warn('Failed to load chat state from localStorage:', error);
    }
  },
  
  // Setup auto-save
  setupAutoSave() {
    // Save every 5 seconds as backup
    setInterval(() => {
      this.saveToStorage();
    }, 5000);
  }
};

// Initialize store
ChatStore.init();

// Export to global scope
window.ChatStore = ChatStore;
