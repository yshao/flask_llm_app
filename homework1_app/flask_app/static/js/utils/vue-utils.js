/**
 * Vue.js Utility Functions
 * Shared utilities for Vue component initialization and mounting
 */

// Vue App Factory - creates and mounts Vue apps with common patterns
const VueAppFactory = {
  /**
   * Create a complete Vue app with automatic initialization
   * @param {Object} component - Vue component definition
   * @param {string} containerId - ID of the DOM element to mount to
   * @param {string} appName - Name for the app (used in logging)
   */
  createApp(component, containerId, appName = 'Vue App') {
    const createAppFunction = () => {
      const { createApp } = Vue;
      const app = createApp(component);
      
      // Mount to the specified container
      const container = document.getElementById(containerId);
      if (container) {
        app.mount(container);
        console.log(`${appName} mounted successfully to #${containerId}`);
        return app;
      } else {
        console.error(`Container #${containerId} not found for ${appName}`);
        return null;
      }
    };
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        console.log(`Initializing ${appName} on DOMContentLoaded`);
        createAppFunction();
      });
    } else {
      console.log(`Initializing ${appName} immediately (DOM already ready)`);
      createAppFunction();
    }
  }
};

// Vue Lifecycle Utilities
const VueLifecycle = {
  /**
   * Common onMounted logic for focusing elements
   * @param {string} elementId - ID of the element to focus
   * @param {Function} callback - Additional callback to run on mount
   */
  onMountedWithFocus(elementId, callback = null) {
    Vue.onMounted(() => {
      // Focus on specified element
      Vue.nextTick(() => {
        const element = document.getElementById(elementId);
        if (element) {
          element.focus();
        }
      });
      
      // Run additional callback if provided
      if (callback) {
        callback();
      }
    });
  },

  /**
   * Common cleanup logic for SocketIO connections
   * @param {Object} socket - SocketIO instance to disconnect
   */
  onUnmountedWithSocketCleanup(socket) {
    Vue.onUnmounted(() => {
      if (socket && socket.value) {
        socket.value.disconnect();
        console.log('SocketIO connection cleaned up');
      }
    });
  }
};

// Export utilities to global scope for use in other files
window.VueAppFactory = VueAppFactory;
window.VueLifecycle = VueLifecycle;
