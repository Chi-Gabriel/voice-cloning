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
    voiceDesign: (text, instruct, language, temperature = 0.3) => {
        return API.request('/voice-design', 'POST', {
            text: Array.isArray(text) ? text : [text],
            instruct: Array.isArray(instruct) ? instruct : [instruct],
            language: language,
            temperature: temperature
        });
    },

    customVoice: (text, speaker, language, instruct, temperature = 0.3) => {
        return API.request('/custom-voice', 'POST', {
            text: Array.isArray(text) ? text : [text],
            speaker: Array.isArray(speaker) ? speaker : [speaker],
            language: language,
            instruct: instruct || null,
            temperature: temperature
        });
    },

    uploadFile: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return API.request('/files/upload', 'POST', formData, true);
    },

    voiceClone: (text, refAudio, refText, language, temperature = 0.3) => {
        // refAudio can be a URL/Path string OR a file_id string
        return API.request('/voice-clone', 'POST', {
            text: Array.isArray(text) ? text : [text],
            ref_audio: refAudio,
            ref_text: refText,
            language: language,
            temperature: temperature
        });
    },

    voiceCloneFile: (text, file, refText, language, temperature = 0.3) => {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('ref_audio', file);
        if (refText) formData.append('ref_text', refText);
        formData.append('language', language);
        formData.append('temperature', temperature);

        return API.request('/voice-clone-file', 'POST', formData, true);
    }
};
