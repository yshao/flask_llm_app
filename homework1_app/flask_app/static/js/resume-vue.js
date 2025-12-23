// Resume Vue Component
const ResumeComponent = {
  template: `
    <div id="resume-app" class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="text-center mb-12">
        <h1 class="text-4xl font-bold text-gray-900 mb-4">Resume, with AI Agent Support</h1>
        <p class="text-xl text-gray-600">View my resume below, or ask my AI agent any questions you might have using the chat.</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-gray-600">Loading resume...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-12">
        <div class="text-red-600 text-6xl mb-4">ERROR:</div>
        <p class="text-xl text-gray-800 mb-2">Failed to load resume</p>
        <p class="text-gray-600">{{ error }}</p>
        <button @click="loadResumeData" class="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">
          Try Again
        </button>
      </div>

      <!-- Resume Content -->
      <div v-else-if="resumeData" class="space-y-8">
        <!-- For each institution -->
        <div 
          v-for="(inst, instId) in resumeData" 
          :key="instId"
          class="bg-white rounded-lg shadow-lg overflow-hidden"
        >
          <!-- Institution Header -->
          <div class="bg-gray-700 text-white p-6">
            <div class="flex justify-between items-start">
              <div class="w-2/3">
                <h2 
                  :id="'inst-' + instId"
                  class="text-2xl font-bold mb-2"
                > 
                  {{ inst.name }} 
                </h2>
                <p class="text-gray-100">
                  <span v-if="inst.department && inst.department !== 'NULL'">{{ inst.department }},</span>
                  <span v-if="inst.address && inst.address !== 'NULL'">{{ inst.address }},</span>
                  <span v-if="inst.city && inst.city !== 'NULL'">{{ inst.city }},</span>
                  <span v-if="inst.state && inst.state !== 'NULL'">{{ inst.state }},</span>
                  <span v-if="inst.zip && inst.zip !== 'NULL'">{{ inst.zip }}</span>
                </p>
              </div>
            </div>
          </div>

          <!-- Positions -->
          <div v-if="inst.positions && Object.keys(inst.positions).length > 0">
            <div 
              v-for="(pos, posId) in inst.positions" 
              :key="posId"
              class="p-6 border-b border-gray-200 last:border-b-0"
            >
              <!-- Position Header -->
              <div class="flex justify-between items-start mb-4">
                <div class="w-2/3">
                  <h3 
                    :id="'pos-' + posId"
                    class="text-xl font-semibold text-gray-900 mb-2"
                  > 
                    {{ pos.title }}
                  </h3>
                  <p class="text-gray-600">
                    {{ pos.start_date && pos.start_date !== 'NULL' ? pos.start_date : '' }}
                    <span v-if="pos.start_date && pos.start_date !== 'NULL' && pos.end_date && pos.end_date !== '0000-00-00'">-</span>
                    {{ pos.end_date && pos.end_date !== '0000-00-00' ? pos.end_date : 'current' }}
                  </p>
                </div>
              </div>

              <!-- Responsibilities -->
              <p class="text-gray-700 mb-4">{{ pos.responsibilities }}</p>
              
              <!-- Experiences -->
              <div v-if="pos.experiences && Object.keys(pos.experiences).length > 0" class="space-y-4">
                <h4 class="font-semibold text-gray-900">Key Experiences:</h4>
                <ul class="space-y-3">
                  <li 
                    v-for="(exp, expId) in pos.experiences" 
                    :key="expId"
                    class="bg-gray-50 rounded-lg p-4"
                  >
                    <p class="text-gray-700 mb-2"> 
                      <a 
                        v-if="exp.hyperlink && exp.hyperlink !== 'NULL'"
                        :href="exp.hyperlink" 
                        class="text-blue-600 hover:text-blue-800 font-semibold underline decoration-blue-300 hover:decoration-blue-600 transition-colors duration-200"
                        :id="'exp-' + expId"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {{ exp.name }}:
                      </a>
                      <span 
                        v-else 
                        class="font-medium"
                        :id="'exp-' + expId"
                      >
                        {{ exp.name }}:
                      </span>
                      {{ exp.description }}
                    </p>
                    
                    <!-- Skills -->
                    <div v-if="exp.skills && Object.keys(exp.skills).length > 0" class="mt-3">
                      <p class="text-sm text-gray-600 mb-2">Skills used:</p>
                      <div class="flex flex-wrap gap-2">
                        <span 
                          v-for="(skill, skillId) in exp.skills" 
                          :key="skillId"
                          class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                          :id="'skill-' + skillId"
                        >
                          {{ skill.name }}
                        </span>
                      </div>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,

  setup() {
    const resumeData = Vue.ref(null);
    const loading = Vue.ref(true);
    const error = Vue.ref(null);

    const loadResumeData = async () => {
      try {
        loading.value = true;
        error.value = null;
        const response = await fetch('/api/resume');
        const result   = await response.json();
        if (!result.success) {
          throw new Error(result.error || 'Unknown error');
        }
        resumeData.value = result.data;
      } catch (e) {
        error.value = e.message || String(e);
      } finally {
        loading.value = false;
      }
    };

    Vue.onMounted(() => {
      loadResumeData();
    });

    return {
      resumeData,
      loading,
      error,
      loadResumeData
    };
  }
};

// Use the shared Vue utilities for initialization
VueAppFactory.createApp(ResumeComponent, 'resume-container', 'Resume App');
