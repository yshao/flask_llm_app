// Chat Vue Component
const ChatComponent = {
  template: `
    <div id="chat-app" class="h-full flex flex-col">  
      <!-- AI Message Counter -->
      <div class="bg-gray-100 border-b border-gray-200 px-4 py-2 text-sm text-gray-600 flex justify-between items-center">
        <span>Messages sent to AI: <span class="font-semibold text-blue-600">{{ aiMessageCount }}</span></span>
        <button 
          @click="clearChat" 
          class="text-xs bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded transition-colors duration-200"
          title="Clear chat history"
        >
          Clear Chat
        </button>
      </div>
      
      <!-- Chat Messages Container -->
      <div 
        id="chat-messages" 
        class="flex-1 overflow-y-auto p-4 space-y-4 chat-messages-container"
        ref="messagesContainer"
      >
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          :class="[
            'mb-4',
            message.role === 'user' ? 'text-right' : 'text-left'
          ]"
        >
          <div 
            :class="[
              'inline-block max-w-md px-4 py-2 rounded-lg',
              message.role === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white text-gray-800 border border-gray-200'
            ]"
            :style="message.customStyle"
          >
            <span v-if="message.isTyping" class="animate-pulse">...</span>
            <span v-else>{{ message.content }}</span>
          </div>
        </div>
      </div>

      <!-- Chat Input -->
      <div class="border-t border-gray-200 p-4">
        <div class="flex space-x-2">
          <input
            id="chat-input"
            v-model="inputMessage"
            @keydown.enter.prevent="submitMessage"
            @keydown.shift.enter=""
            type="text"
            placeholder="Type your message..."
            class="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            @click="submitMessage"
            class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  `,

  setup() {

    // Core reactive state 
    const messages = Vue.ref(ChatStore.messages);  // Array of messages (both user and AI) - now from global store
    const inputMessage = Vue.ref('');              // Message the user is typing into the chat
    const isConnected = Vue.ref(ChatStore.isConnected); // Tracks the socketio connection status - now from global store
    const socket = Vue.ref(null);                  // SocketIO instance  
    const messagesContainer = Vue.ref(null);       // References the DOM elements that contain the chat messages.
    const aiMessageCount = Vue.ref(ChatStore.aiMessageCount); // Count of messages sent to AI - now from global store

    // Configuration
    const CHAT_CONFIG = {ROOM_NAME: 'main',  TYPING_DELAY: 100, SOCKET_NAMESPACE: '/chat'};

    // ============================================================================
    // Core message handling functions - modify these for your AI agent features (if needed)
    // ============================================================================
    const submitMessage = () => {   
      const message = inputMessage.value.trim(); // Get the message the user is typing into the chat
      if (!message) return;                     // If the message is empty, do nothing
      inputMessage.value = '';                  // Clear the input field

      // Send user message to the chat history window via SocketIO (this is so that other users can see the message, in case you want mulit-user chat)
      if (socket.value && isConnected.value) {socket.value.emit('text', {msg:  message,room: CHAT_CONFIG.ROOM_NAME});}

      // Capture the current page content
      const pageContent = {                   // Capture the current page content
        title: document.title,                // The title of the page
        url: window.location.href,            // The URL of the page
        content: document.body.innerHTML || '', // Send HTML content for backend cleaning
        html: document.body.innerHTML || ''    // The HTML content of the page
      };
      
      // Log the captured page content for debugging
      console.log('Page content captured:', pageContent);

      // Show typing indicator and send to AI
      setTimeout(() => {
        showTypingIndicator();                // Show the typing indicator
        ChatStore.incrementAICount();         // Increment AI message counter in global store
        aiMessageCount.value = ChatStore.aiMessageCount; // Update local reactive state
        sendMessageToAI(message, pageContent); // Send the message to the AI  
      }, CHAT_CONFIG.TYPING_DELAY);           // The delay before showing the typing indicator
    };

    const handleAIResponse = (data) => {
      console.log('Handling AI response:', data);
      // Then render the chat message
      removeTypingIndicator();
      const role = data.role || 'user';
      addMessage(role, data.msg, false, data.style);  // Add the AI response to the chat history window
      
      // ============================================================================
      // ADD YOUR POST-RESPONSE ACTIONS HERE
      // ============================================================================
      
      // Example: Log the response for debugging
      console.log('AI Response received:', data);
      
      // Example: Track response statistics
      console.log(`Total AI interactions: ${aiMessageCount.value} messages sent, response received`);

      // ============================================================================
      // HOMEWORK 1: POST-RESPONSE ACTIONS FOR REAL-TIME UPDATES
      // ============================================================================

      // If this was a database operation, trigger resume data reload
      if (data.expert_results && data.expert_results.length > 0) {
        const hasDatabaseOperation = data.expert_results.some(result =>
          result.role === 'Database Read Expert' || result.role === 'Database Write Expert'
        );

        if (hasDatabaseOperation) {
          console.log('Database operation detected, reloading resume data...');

          // Trigger resume data reload after a short delay to ensure database is updated
          setTimeout(() => {
            // Call resume data reload (this function should be available globally)
            if (typeof loadResumeData === 'function') {
              loadResumeData();
              console.log('Resume data reloaded after database operation');
            } else {
              console.warn('loadResumeData function not available');
            }
          }, 1000); // 1 second delay
        }
      }

      // Log orchestrator execution details
      if (data.orchestrator_calls) {
        console.log(`Orchestrator coordinated ${data.orchestrator_calls} expert calls`);
      }

      // Log expert execution results
      if (data.expert_results) {
        console.log('Expert execution results:', data.expert_results);
      }

// Global function to reload resume data after database operations
window.loadResumeData = function() {
  console.log('Global resume reload triggered');

  // Trigger a resume data refresh by calling the API
  fetch('/api/resume')
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        console.log('Resume data refreshed:', data.data);

        // If Vue app is available, update its data
        if (typeof VueAppFactory !== 'undefined' && VueAppFactory.apps) {
          // Find the resume Vue app and update its data
          const resumeApp = VueAppFactory.apps.find(app => app.pageType === 'resume');
          if (resumeApp && resumeApp.app && resumeApp.app.resumeData) {
            resumeApp.app.resumeData = data.data;
            console.log('Resume Vue app updated with fresh data');
          }
        }

        // Also refresh any resume displays on current page
        refreshResumeDisplays();
      } else {
        console.error('Failed to refresh resume data');
      }
    })
    .catch(error => {
      console.error('Error refreshing resume data:', error);
    });
};

// Helper function to refresh resume displays on current page
function refreshResumeDisplays() {
  // Look for common resume display elements and refresh them
  const resumeElements = document.querySelectorAll('[data-resume-section]');

  resumeElements.forEach(element => {
    // Trigger Vue reactivity or just refresh the content
    if (element.__vue__) {
      // Element is managed by Vue
      element.__vue__.$forceUpdate();
    } else {
      // For non-Vue elements, trigger a refresh
      element.dispatchEvent(new Event('refresh'));
    }
  });
};
    };
    // ============================================================================
    // Helper functions follow (you probably don't need to modify these)
    // ============================================================================
    const sendMessageToAI = (message, pageContent) => {
      const requestBody = { 
        message: message,
        pageContent: pageContent
      };

      fetch('/chat/ai', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })
      .then(response => response.json())
      .then(data => {
        if (!data.success) {
          removeTypingIndicator();
          addMessage('assistant', 'AI service error. Please try again.');
          return;
        }
        // Note: UI highlighting functionality has been removed
      })
      .catch(error => {
        removeTypingIndicator();
        addMessage('assistant', 'AI service error. Please try again.');
        console.error('AI service error:', error);
      });
    };


    const initializeSocketIO = () => {
      try {
        socket.value = io(CHAT_CONFIG.SOCKET_NAMESPACE);
        setupSocketEventHandlers();
        console.log('SocketIO connection initialized');
      } catch (error) {
        console.error('Failed to initialize SocketIO:', error);
        addMessage('assistant', 'Failed to connect to chat server');
      }
    };

    const setupSocketEventHandlers = () => {
      if (!socket.value) return;

      socket.value.on('connect', () => {
        ChatStore.setConnectionStatus(true);
        isConnected.value = true;
        console.log('Connected to chat room:', CHAT_CONFIG.ROOM_NAME);
        
        socket.value.emit('joined', { 
          room: CHAT_CONFIG.ROOM_NAME 
        });
      });

      socket.value.on('message', (data) => {
        removeTypingIndicator();
        handleAIResponse(data);
      });

      socket.value.on('connect_error', (error) => {
        ChatStore.setConnectionStatus(false);
        isConnected.value = false;
        console.error('SocketIO connection error:', error);
        addMessage('assistant', 'Connection error. Trying to reconnect...');
      });

      socket.value.on('disconnect', () => {
        ChatStore.setConnectionStatus(false);
        isConnected.value = false;
        console.log('Disconnected from chat room');
        // Removed disconnect message to avoid showing it when switching tabs
      });
    };

    const addMessage = (role, content, isTyping = false, customStyle = null) => {
      // Add message to global store
      const message = ChatStore.addMessage(role, content, isTyping, customStyle);
      
      // Update local reactive state by creating a new array reference
      messages.value = [...ChatStore.messages];
      
      // Scroll to bottom
      Vue.nextTick(() => {
        if (messagesContainer.value) {
          messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
        }
      });
    };

    const showTypingIndicator = () => {
      console.log('Showing typing indicator...');
      addMessage('assistant', '...', true);
      console.log('Typing indicator added, messages:', messages.value);
    };

    const removeTypingIndicator = () => {
      console.log('Removing typing indicator...');
      console.log('Messages before removal:', messages.value);
      ChatStore.removeTypingIndicator();
      // Update local reactive state by creating a new array reference
      messages.value = [...ChatStore.messages];
      console.log('Messages after removal:', messages.value);
    };

    // Sync local state with global store on mount
    const syncWithStore = () => {
      messages.value = [...ChatStore.messages];
      aiMessageCount.value = ChatStore.aiMessageCount;
      isConnected.value = ChatStore.isConnected;
    };

    // Clear chat history
    const clearChat = () => {
      ChatStore.clearChat();
      syncWithStore(); // Update local state
    };

    // Initialize on mount using shared utilities
    VueLifecycle.onMountedWithFocus('chat-input', () => {
      syncWithStore(); // Sync state first
      initializeSocketIO(); // Then initialize socket
    });
    
    // Cleanup on unmount using shared utilities
    VueLifecycle.onUnmountedWithSocketCleanup(socket);

    return {
      messages,
      inputMessage,
      isConnected,
      messagesContainer,
      aiMessageCount,
      
      submitMessage,
      sendMessageToAI,
      handleAIResponse,
      clearChat,
      
      addMessage,
      showTypingIndicator,
      removeTypingIndicator
    };
  }
};

// Use the shared Vue utilities for initialization
VueAppFactory.createApp(ChatComponent, 'chat-container', 'Chat App');
