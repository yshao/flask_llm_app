// Agents Vue Component
const AgentsComponent = {
  template: `
    <div id="agents-app" class="max-w-6xl mx-auto">
      <div class="text-center mb-12">
      </div>

      <div class="space-y-12">
        <!-- Resume Chat Agent -->
        <div class="bg-white rounded-lg shadow-lg overflow-hidden">
          <div class="flex">
            <div class="w-1/3 p-8 flex items-center justify-center bg-gray-200">
              <img src="/static/images/resume-project-icon.png" alt="Resume Chat Agent" class="w-48 h-48 rounded-full object-cover shadow-lg">
            </div>
            <div class="w-2/3 p-8">
              <h2 class="text-2xl font-bold text-gray-900 mb-4">Resume Chat Agent</h2>
              <p class="text-gray-700 leading-relaxed mb-6">
                I've developed an AI agent that allows you to chat with my resume. This agent can answer questions about my background, experience, and skills.
              </p>
              <a href="/agents/resume" class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors duration-200 shadow-lg hover:shadow-xl">
                View Resume
                <svg class="ml-2 -mr-1 w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
              </a>
            </div>
          </div>
        </div>

        <!-- Coming Soon Section -->
        <div class="text-center py-12">
          <div class="bg-gray-200 rounded-lg p-8">
            <h3 class="text-2xl font-bold text-gray-900 mb-4">More AI Agents Coming Soon!</h3>
            <p class="text-gray-600 mb-6">Students will develop additional AI agents as part of their coursework.</p>
          </div>
        </div>
      </div>
    </div>
  `,

  setup() {
    // Add your reactive state and methods for AI agent features here
    
    return {
      // Return any reactive variables or methods you add
    };
  }
};

// Use the shared Vue utilities for initialization
VueAppFactory.createApp(AgentsComponent, 'agents-container', 'Agents App');
