// API Wrapper

const API = {
    BASE_URL: '/api/v1',
    apiKey: null,

    setApiKey: (key) => {
        API.apiKey = key;
    },

    headers: () => {
        const h = {
            'Content-Type': 'application/json'
        };
        if (API.apiKey) {
            h['x-api-key'] = API.apiKey;
        }
        return h;
    },

    // Generic request handler
    request: async (endpoint, method, body = null, isFormData = false) => {
        const url = `${API.BASE_URL}${endpoint}`;
        const options = {
            method,
            headers: isFormData ? {} : API.headers()
        };

        if (isFormData) {
            if (API.apiKey) {
                options.headers['x-api-key'] = API.apiKey;
            }
            options.body = body;
        } else if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'API Request Failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // Endpoints
    voiceDesign: (text, instruct, language) => {
        return API.request('/voice-design', 'POST', {
            text: [text],
            instruct: [instruct],
            language: [language]
        });
    },

    customVoice: (text, speaker, language, instruct) => {
        return API.request('/custom-voice', 'POST', {
            text: [text],
            speaker: [speaker],
            language: language,
            instruct: instruct || null
        });
    },

    voiceCloneFile: (text, file, refText, language) => {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('ref_audio', file);
        if (refText) formData.append('ref_text', refText);
        // Ensure language is passed as expected by the backend
        // Backend handles "Auto" string or enum value.
        formData.append('language', language);

        return API.request('/voice-clone-file', 'POST', formData, true);
    }
};
