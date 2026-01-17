// ============================================================================
// CLIENT ERROR LOGGING UTILITIES
// ============================================================================

/**
 * Log a client-side error to the server for server-side logging
 * @param {string} type - Error type: 'error', 'warning', 'network'
 * @param {string} source - Error source: 'fetch', 'socket', 'general'
 * @param {string} message - Error message
 * @param {string} stack - Error stack trace (optional)
 * @param {object} details - Additional error details (optional)
 */
function logClientError(type, source, message, stack = '', details = {}) {
  const errorData = {
    type: type,
    source: source,
    message: message,
    url: window.location.href,
    stack: stack,
    details: details,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent
  };

  // Send to server asynchronously (don't wait for response)
  fetch('/api/log/error', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(errorData)
  }).catch(err => {
    // Silent fail - we don't want to create infinite error loops
    console.warn('[LOG] Failed to send error to server:', err);
  });
}

/**
 * Log network request details to the server
 * @param {string} url - Request URL
 * @param {string} method - HTTP method
 * @param {number} duration_ms - Request duration in milliseconds
 * @param {number} status - HTTP status code
 * @param {boolean} success - Whether the request succeeded
 * @param {string} error - Error message (if failed)
 */
function logNetworkRequest(url, method, duration_ms, status, success, error = '') {
  const networkData = {
    url: url,
    method: method,
    duration_ms: duration_ms,
    status: status,
    success: success,
    error: error,
    timestamp: new Date().toISOString()
  };

  fetch('/api/log/network', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(networkData)
  }).catch(err => {
    console.warn('[LOG] Failed to send network log to server:', err);
  });
}

// ============================================================================
// Chat Vue Component
// ============================================================================

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

      // Add user's message to chat display immediately
      addMessage('user', message);

      // Note: Removed SocketIO emit - user messages are already added locally above
      // SocketIO echo was being treated as AI response, causing confusion

      // Capture the current page content
      const pageContent = {                   // Capture the current page content
        title: document.title,                // The title of the page
        url: window.location.href,            // The URL of the page
        content: document.body.innerHTML || '', // Send HTML content for backend cleaning
        html: document.body.innerHTML || ''    // The HTML content of the page
      };
      
      // Log the captured page content for debugging
      console.log('[SEND] Message:', message);
      console.log('[SEND] Page URL:', pageContent.url);
      console.log('[SEND] Page Title:', pageContent.title);
      console.log('[SEND] Content length:', pageContent.content.length);

      // Show typing indicator and send to AI
      setTimeout(() => {
        showTypingIndicator();                // Show the typing indicator
        ChatStore.incrementAICount();         // Increment AI message counter in global store
        aiMessageCount.value = ChatStore.aiMessageCount; // Update local reactive state
        sendMessageToAI(message, pageContent); // Send the message to the AI
      }, CHAT_CONFIG.TYPING_DELAY);           // The delay before showing the typing indicator
    };

    const handleAIResponse = (data) => {
      console.log('[RESPONSE] Received response:', data);
      console.log('[RESPONSE] Success:', data.success);
      console.log('[RESPONSE] Has response:', !!data.response);
      console.log('[RESPONSE] Has error:', data.error);
      console.log('[RESPONSE] Full data:', JSON.stringify(data));

      // Then render the chat message
      removeTypingIndicator();

      // Handle error response
      // Note: SocketIO messages don't have a 'success' field - they're only for successful AI responses
      // Fetch responses have 'success' field and can be errors
      if (data.success === false) {
        const errorMsg = data.response || data.error || 'Unknown error';
        console.error('[RESPONSE] AI request failed:', errorMsg);
        addMessage('assistant', `Error: ${errorMsg}`);
        return;
      }

      // For both SocketIO (no success field) and successful fetch (success: true)
      // render the response
      const role = data.role || 'user';
      addMessage(role, data.msg || data.response, false, data.style);  // Add the AI response to the chat history window

      // ============================================================================
      // ADD YOUR POST-RESPONSE ACTIONS HERE
      // ============================================================================

      // Log successful response
      console.log('[RESPONSE] AI Response received:', data);
      console.log(`[RESPONSE] Total AI interactions: ${aiMessageCount.value} messages sent, response received`);

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

      console.log('[FETCH] Sending request to /chat/ai');
      console.log('[FETCH] Request body:', {
        messageLength: message.length,
        pageUrl: pageContent.url,
        pageTitle: pageContent.title
      });

      const startTime = Date.now();

      fetch('/chat/ai', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })
      .then(response => {
        const elapsedTime = Date.now() - startTime;
        console.log(`[FETCH] Response received in ${elapsedTime}ms`);
        console.log('[FETCH] Response status:', response.status, response.statusText);

        // Log network request to server
        logNetworkRequest('/chat/ai', 'POST', elapsedTime, response.status, response.ok);

        // Check if response is ok (status 200-299)
        if (!response.ok) {
          const errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
          console.error('[FETCH] HTTP Error:', response.status, response.statusText);

          // Log error to server
          logClientError('error', 'fetch', errorMsg, '', {
            status: response.status,
            statusText: response.statusText,
            url: '/chat/ai',
            method: 'POST'
          });

          removeTypingIndicator();
          addMessage('assistant', `HTTP Error ${response.status}: ${response.statusText}. Please try again.`);
          return null;
        }

        return response.json();
      })
      .then(data => {
        if (!data) {
          // Already handled by response.ok check above
          return;
        }

        console.log('[FETCH] Parsed JSON response:', data);

        if (!data.success) {
          const errorMsg = data.error || data.response || 'Unknown error';
          console.error('[FETCH] API Error:', errorMsg);
          console.error('[FETCH] Full error data:', JSON.stringify(data));

          // Log error to server
          logClientError('error', 'api', errorMsg, '', {
            fullResponse: data,
            url: '/chat/ai',
            method: 'POST'
          });

          removeTypingIndicator();
          addMessage('assistant', `Error: ${errorMsg}`);
          return;
        }

        // Success - note: UI highlighting functionality has been removed
        console.log('[FETCH] Request successful');
      })
      .catch(error => {
        const elapsedTime = Date.now() - startTime;
        console.error(`[FETCH] Network error after ${elapsedTime}ms:`, error);
        console.error('[FETCH] Error name:', error.name);
        console.error('[FETCH] Error message:', error.message);
        console.error('[FETCH] Error stack:', error.stack);

        // Log error to server
        logClientError('error', 'fetch', error.message, error.stack, {
          errorName: error.name,
          duration_ms: elapsedTime,
          url: '/chat/ai',
          method: 'POST'
        });

        removeTypingIndicator();

        // Provide more specific error messages based on error type
        let errorMessage = 'AI service error. Please try again.';

        if (error.name === 'TypeError' && error.message.includes('fetch')) {
          errorMessage = 'Network error: Unable to reach the server. Please check your connection.';
        } else if (error.name === 'AbortError') {
          errorMessage = 'Request timed out. Please try again.';
        }

        addMessage('assistant', errorMessage);
      });
    };


    const initializeSocketIO = () => {
      try {
        console.log('[SOCKET] Initializing SocketIO connection...');
        console.log('[SOCKET] Namespace:', CHAT_CONFIG.SOCKET_NAMESPACE);
        socket.value = io(CHAT_CONFIG.SOCKET_NAMESPACE);
        setupSocketEventHandlers();
        console.log('[SOCKET] SocketIO connection initialized successfully');
      } catch (error) {
        console.error('[SOCKET] Failed to initialize SocketIO:', error);
        console.error('[SOCKET] Error name:', error.name);
        console.error('[SOCKET] Error message:', error.message);

        // Log to server
        logClientError('error', 'socket', error.message, error.stack, {
          errorName: error.name,
          phase: 'initialization'
        });

        addMessage('assistant', 'Failed to connect to chat server. Please refresh the page.');
      }
    };

    const setupSocketEventHandlers = () => {
      if (!socket.value) {
        console.error('[SOCKET] No socket instance available');
        return;
      }

      socket.value.on('connect', () => {
        console.log('[SOCKET] Connected successfully');
        console.log('[SOCKET] Socket ID:', socket.value.id);
        ChatStore.setConnectionStatus(true);
        isConnected.value = true;
        console.log('[SOCKET] Joining room:', CHAT_CONFIG.ROOM_NAME);

        socket.value.emit('joined', {
          room: CHAT_CONFIG.ROOM_NAME
        });
      });

      socket.value.on('message', (data) => {
        console.log('[SOCKET] Message received:', data);
        console.log('[SOCKET] Message type:', data.role || 'unknown');
        console.log('[SOCKET] Message content length:', data.msg?.length || 0);
        removeTypingIndicator();
        handleAIResponse(data);
      });

      socket.value.on('connect_error', (error) => {
        console.error('[SOCKET] Connection error:', error);
        console.error('[SOCKET] Error description:', error.description);
        console.error('[SOCKET] Error context:', error.context);

        // Log to server
        logClientError('error', 'socket', error.description || error.message || 'Socket connection error', '', {
          errorType: 'connect_error',
          description: error.description,
          context: error.context
        });

        ChatStore.setConnectionStatus(false);
        isConnected.value = false;
        addMessage('assistant', 'Connection error. Trying to reconnect...');
      });

      socket.value.on('disconnect', (reason) => {
        console.log('[SOCKET] Disconnected. Reason:', reason);
        ChatStore.setConnectionStatus(false);
        isConnected.value = false;
        // Removed disconnect message to avoid showing it when switching tabs
      });

      socket.value.on('reconnect', (attemptNumber) => {
        console.log(`[SOCKET] Reconnected after ${attemptNumber} attempts`);
        ChatStore.setConnectionStatus(true);
        isConnected.value = true;
      });

      socket.value.on('reconnect_attempt', (attemptNumber) => {
        console.log(`[SOCKET] Reconnection attempt ${attemptNumber}`);
      });

      socket.value.on('reconnect_failed', () => {
        console.error('[SOCKET] Reconnection failed');

        // Log to server
        logClientError('error', 'socket', 'Failed to reconnect after multiple attempts', '', {
          errorType: 'reconnect_failed'
        });

        addMessage('assistant', 'Failed to reconnect to server. Please refresh the page.');
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

// ============================================================================
// GLOBAL ERROR HANDLERS
// ============================================================================

/**
 * Global error handler for unhandled JavaScript errors
 */
window.addEventListener('error', (event) => {
  console.error('[GLOBAL ERROR]', event.error);

  // Log to server
  logClientError('error', 'global', event.error?.message || 'Unknown error', event.error?.stack || '', {
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno
  });
});

/**
 * Global handler for unhandled promise rejections
 */
window.addEventListener('unhandledrejection', (event) => {
  console.error('[UNHANDLED REJECTION]', event.reason);

  // Log to server
  logClientError('error', 'promise', event.reason?.message || 'Unhandled promise rejection', event.reason?.stack || '', {
    reason: String(event.reason)
  });
});
