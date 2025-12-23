// Login Vue Component
const LoginComponent = {
  template: `
    <div id="login-app" class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-6">
      <div class="max-w-md w-full space-y-8">
        <div>
          <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p class="mt-2 text-center text-sm text-gray-600">
            Welcome back! Please sign in to continue.
          </p>
        </div>
        
        <form class="mt-8 space-y-6" @submit.prevent="checkCredentials">
          <div class="rounded-md shadow-sm -space-y-px">
            <div>
              <label for="authemail" class="sr-only">Email address</label>
              <input 
                id="authemail" 
                v-model="email"
                name="email" 
                type="email" 
                autocomplete="email" 
                required 
                class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 text-sm" 
                placeholder="Email address"
                :disabled="loading"
              >
            </div>
            <div>
              <label for="authpassword" class="sr-only">Password</label>
              <input 
                id="authpassword" 
                v-model="password"
                name="password" 
                type="password" 
                autocomplete="current-password" 
                required 
                class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 text-sm" 
                placeholder="Password"
                :disabled="loading"
              >
            </div>
          </div>

          <div>
            <button 
              type="submit" 
              class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="loading || !email || !password"
            >
              <span class="absolute left-0 inset-y-0 flex items-center pl-3">
                <svg class="h-5 w-5 text-blue-500 group-hover:text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
                </svg>
              </span>
              <span v-if="loading">Signing in...</span>
              <span v-else>Sign in</span>
            </button>
          </div>

          <!-- Status Message -->
          <div 
            v-if="statusMessage" 
            :class="[
              'text-center text-sm',
              statusType === 'error' ? 'text-red-600' : 'text-green-600'
            ]"
          >
            {{ statusMessage }}
          </div>
        </form>
      </div>
    </div>
  `,

  setup() {
    // Reactive state
    const email = Vue.ref('');
    const password = Vue.ref('');
    const loading = Vue.ref(false);
    const statusMessage = Vue.ref('');
    const statusType = Vue.ref('error');

    // Check credentials
    const checkCredentials = async () => {
      if (!email.value || !password.value) {
        setStatus('Please enter both email and password', 'error');
        return;
      }

      loading.value = true;
      setStatus('', '');

      try {
        // Package data in a JSON object
        const data = { 
          email: email.value, 
          password: password.value
        };

        // Send data to server via fetch
        const response = await fetch("/processlogin", {
          method: "POST",
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data)
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log(result);

        if (result.success == 1) {
          // Success - redirect to home
          setStatus('Login successful! Redirecting...', 'success');
          
          // Redirect after a short delay
          setTimeout(() => {
            window.location.href = "/";
          }, 1000);
        } else {
          // Authentication failure
          setStatus('Authentication failed. Please try again.', 'error');
        }
      } catch (error) {
        console.error('Error:', error);
        setStatus('Network error occurred. Please try again.', 'error');
      } finally {
        loading.value = false;
      }
    };

    // Set status message
    const setStatus = (message, type) => {
      statusMessage.value = message;
      statusType.value = type;
    };

    return {
      email,
      password,
      loading,
      statusMessage,
      statusType,
      checkCredentials
    };
  }
};

// Use the shared Vue utilities for initialization
VueAppFactory.createApp(LoginComponent, 'login-container', 'Login App');
