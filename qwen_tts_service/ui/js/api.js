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
                let msg = 'API Request Failed';
                if (data.detail) {
                    msg = typeof data.detail === 'string'
                        ? data.detail
                        : JSON.stringify(data.detail, null, 2);
                }
                throw new Error(msg);
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

    voiceClone: (text, refAudio, refText, language, temperature = 0.3, enhanced = false) => {
        // refAudio can be a URL/Path string OR a file_id string
        const endpoint = enhanced ? '/voice-clone-enhanced' : '/voice-clone';
        return API.request(endpoint, 'POST', {
            text: Array.isArray(text) ? text : [text],
            ref_audio: refAudio,
            ref_text: refText,
            language: language,
            temperature: temperature
        });
    },

    voiceCloneFile: (text, file, refText, language, temperature = 0.3, enhanced = false) => {
        const endpoint = enhanced ? '/voice-clone-enhanced-file' : '/voice-clone-file';
        const formData = new FormData();
        formData.append('text', text);
        formData.append('ref_audio', file);
        if (refText) formData.append('ref_text', refText);
        formData.append('language', language);
        formData.append('temperature', temperature);

        return API.request(endpoint, 'POST', formData, true);
    },

    // ASR Endpoints
    transcribeBatch: (items, language, returnTimestamps = false) => {
        // items is array of { file_id: "...", custom_id: "..." }
        return API.request('/transcribe', 'POST', {
            files: items,
            language: language,
            return_timestamps: returnTimestamps
        });
    },

    transcribeFile: (file, language, returnTimestamps = false) => {
        const formData = new FormData();
        formData.append('audio', file);
        formData.append('language', language);
        formData.append('return_timestamps', returnTimestamps);
        return API.request('/transcribe/file', 'POST', formData, true);
    },

    // Diarization Endpoints
    diarizeBatch: (items, numSpeakers = null, minSpeakers = null, maxSpeakers = null) => {
        // items is array of { file_id: "...", custom_id: "..." }
        const payload = { files: items };
        // We assume batch params apply to all if provided, but our backend handles per-file
        // In this simple UI, we'll apply them individually to each item.
        if (numSpeakers) items.forEach(i => i.num_speakers = numSpeakers);
        if (minSpeakers) items.forEach(i => i.min_speakers = minSpeakers);
        if (maxSpeakers) items.forEach(i => i.max_speakers = maxSpeakers);
        return API.request('/diarize', 'POST', payload);
    },

    diarizeFile: (file, numSpeakers = null, minSpeakers = null, maxSpeakers = null) => {
        const formData = new FormData();
        formData.append('audio', file);
        if (numSpeakers) formData.append('num_speakers', numSpeakers);
        if (minSpeakers) formData.append('min_speakers', minSpeakers);
        if (maxSpeakers) formData.append('max_speakers', maxSpeakers);
        return API.request('/diarize/file', 'POST', formData, true);
    },

    // Queue Endpoints
    submitBatchToQueue: (items, label = null) => {
        return API.request('/queue/submit', 'POST', {
            items,
            label
        });
    },

    getQueueStatus: (batchId) => {
        return API.request(`/queue/status/${batchId}`, 'GET');
    },

    getQueueResults: (batchId) => {
        return API.request(`/queue/results/${batchId}`, 'GET');
    }
};
