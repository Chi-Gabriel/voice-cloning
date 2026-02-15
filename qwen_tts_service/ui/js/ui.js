// UI Controller

const UI = {
    elements: {
        tabs: document.querySelectorAll('.nav-item'),
        tabContents: document.querySelectorAll('.tab-content'),
        apiKeyInput: document.getElementById('api-key-input'),

        // Voice Design
        vdText: document.getElementById('vd-text'),
        vdInstruct: document.getElementById('vd-instruct'),
        vdLanguage: document.getElementById('vd-language'),
        btnDesign: document.getElementById('btn-generate-design'),

        // Voice Cloning
        vcText: document.getElementById('vc-text'),
        vcDropArea: document.getElementById('vc-drop-area'),
        vcFile: document.getElementById('vc-file'),
        vcPreview: document.getElementById('vc-preview'),
        vcRefText: document.getElementById('vc-ref-text'),
        vcLanguage: document.getElementById('vc-language'),
        btnClone: document.getElementById('btn-generate-clone'),

        // Custom Voice
        cvText: document.getElementById('cv-text'),
        cvSpeaker: document.getElementById('cv-speaker'),
        cvLanguage: document.getElementById('cv-language'),
        cvInstruct: document.getElementById('cv-instruct'),
        btnCustom: document.getElementById('btn-generate-custom'),

        // Output
        playPauseBtn: document.getElementById('play-pause'),
        timeDisplay: document.getElementById('time-display'),
        historyList: document.getElementById('history-list')
    },

    wavesurfer: null,

    // ISO Languages
    languages: [
        { code: 'auto', name: 'Auto Detect' },
        { code: 'en', name: 'English' },
        { code: 'zh', name: 'Chinese' },
        { code: 'ja', name: 'Japanese' },
        { code: 'ko', name: 'Korean' },
        { code: 'fr', name: 'French' },
        { code: 'de', name: 'German' },
        { code: 'es', name: 'Spanish' },
        { code: 'ru', name: 'Russian' },
        { code: 'pt', name: 'Portuguese' },
        { code: 'it', name: 'Italian' },
        { code: 'nl', name: 'Dutch' }
    ],

    init: () => {
        UI.initTabs();
        UI.initWaveSurfer();
        UI.initLanguages();
        UI.loadHistory();

        // Load API Key
        const savedKey = Utils.getFromStorage('api_key');
        if (savedKey) {
            UI.elements.apiKeyInput.value = savedKey;
            API.setApiKey(savedKey);
        }

        UI.setupEventListeners();
    },

    initTabs: () => {
        UI.elements.tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;

                // Update active tab
                UI.elements.tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                // Update content
                UI.elements.tabContents.forEach(c => c.classList.remove('active'));
                document.getElementById(target).classList.add('active');
            });
        });
    },

    initWaveSurfer: () => {
        UI.wavesurfer = WaveSurfer.create({
            container: '#waveform',
            waveColor: '#334155',
            progressColor: '#3b82f6',
            cursorColor: '#f8fafc',
            barWidth: 2,
            barRadius: 3,
            cursorWidth: 1,
            height: 80,
            barGap: 3
        });

        UI.wavesurfer.on('ready', () => {
            UI.elements.playPauseBtn.disabled = false;
            UI.updateTime();
        });

        UI.wavesurfer.on('audioprocess', () => {
            UI.updateTime();
        });

        UI.wavesurfer.on('finish', () => {
            UI.updatePlayButton(false);
        });
    },

    initLanguages: () => {
        const options = UI.languages.map(l => `<option value="${l.code}">${l.name}</option>`).join('');
        UI.elements.vdLanguage.innerHTML = options;
        UI.elements.vcLanguage.innerHTML = options;
        UI.elements.cvLanguage.innerHTML = options;
    },

    setupEventListeners: () => {
        // API Key
        UI.elements.apiKeyInput.addEventListener('change', (e) => {
            const key = e.target.value.trim();
            API.setApiKey(key);
            Utils.saveToStorage('api_key', key);
        });

        // File Upload
        const dropArea = UI.elements.vcDropArea;
        const fileInput = UI.elements.vcFile;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.add('is-active'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.remove('is-active'), false);
        });

        dropArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        });

        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });

        function handleFiles(files) {
            if (files.length > 0) {
                const file = files[0];
                if (file.type.startsWith('audio/')) {
                    UI.elements.vcPreview.src = URL.createObjectURL(file);
                    UI.elements.vcPreview.style.display = 'block';
                    UI.elements.vcDropArea.querySelector('.file-msg').textContent = file.name;
                }
            }
        }

        // Play/Pause
        UI.elements.playPauseBtn.addEventListener('click', () => {
            UI.wavesurfer.playPause();
            UI.updatePlayButton(UI.wavesurfer.isPlaying());
        });

        // Generate Buttons
        UI.elements.btnDesign.addEventListener('click', () => UI.handleGeneration('design'));
        UI.elements.btnClone.addEventListener('click', () => UI.handleGeneration('clone'));
        UI.elements.btnCustom.addEventListener('click', () => UI.handleGeneration('custom'));
    },

    handleGeneration: async (mode) => {
        const btn = mode === 'design' ? UI.elements.btnDesign :
            mode === 'clone' ? UI.elements.btnClone :
                UI.elements.btnCustom;

        const originalText = btn.textContent;
        btn.disabled = true;
        btn.textContent = 'Generating...';

        try {
            let response;
            if (mode === 'design') {
                const text = UI.elements.vdText.value;
                const instruct = UI.elements.vdInstruct.value;
                const lang = UI.elements.vdLanguage.value;
                if (!text || !instruct) throw new Error('Text and Instruction are required');

                response = await API.voiceDesign(text, instruct, lang);
            } else if (mode === 'clone') {
                const text = UI.elements.vcText.value;
                const file = UI.elements.vcFile.files[0];
                const refText = UI.elements.vcRefText.value;
                const lang = UI.elements.vcLanguage.value;

                if (!text || !file) throw new Error('Text and Reference Audio are required');

                response = await API.voiceCloneFile(text, file, refText, lang); // Using multipart endpoint
            } else if (mode === 'custom') {
                const text = UI.elements.cvText.value;
                const speaker = UI.elements.cvSpeaker.value;
                const lang = UI.elements.cvLanguage.value;
                const instruct = UI.elements.cvInstruct.value;

                if (!text || !speaker) throw new Error('Text and Speaker ID are required');

                response = await API.customVoice(text, speaker, lang, instruct);
            }

            if (response && response.items && response.items.length > 0) {
                const audioBase64 = response.items[0].audio_base64;
                const blob = Utils.base64ToBlob(audioBase64);
                const url = URL.createObjectURL(blob);

                UI.wavesurfer.load(url);
                UI.wavesurfer.play();
                UI.updatePlayButton(true);

                UI.addToHistory(mode, url, response.performance);
            }

        } catch (error) {
            alert(error.message);
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    },

    updateTime: () => {
        const current = UI.wavesurfer.getCurrentTime();
        const duration = UI.wavesurfer.getDuration();
        UI.elements.timeDisplay.textContent = `${Utils.formatTime(current)} / ${Utils.formatTime(duration)}`;
    },

    updatePlayButton: (isPlaying) => {
        const icon = isPlaying
            ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>'
            : '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>';
        UI.elements.playPauseBtn.innerHTML = icon;
    },

    addToHistory: (mode, url, performance) => {
        const item = {
            id: Utils.generateId(),
            mode: mode,
            url: url,
            performance: performance,
            timestamp: new Date().toLocaleString()
        };

        let history = Utils.getFromStorage('history', []);
        // Don't store Blob URLs in local storage as they expire. 
        // For a real app, we'd upload to server or use IndexedDB.
        // For this demo, we'll recreate the history only for the session or list currently generated items.
        // Actually, let's just prepend to DOM.

        const el = document.createElement('div');
        el.className = 'history-item';
        el.innerHTML = `
            <div class="history-info">
                <strong>${mode.toUpperCase().replace('-', ' ')}</strong>
                <span>${item.timestamp}</span>
                <span style="font-size: 0.8em; color: var(--accent); display: block; margin-top: 4px;">
                    generated in ${item.performance ? item.performance.toFixed(2) + 's' : 'N/A'}
                </span>
            </div>
            <div class="history-actions">
                <button onclick="UI.wavesurfer.load('${url}'); UI.wavesurfer.play();">Play</button>
                <a href="${url}" download="generated_${item.id}.wav" style="color:var(--accent); text-decoration:none; font-size:0.9rem; margin-left:8px;">Download</a>
            </div>
        `;

        UI.elements.historyList.prepend(el);
    },

    loadHistory: () => {
        // Since we can't persist blob URLs easily without IndexedDB, we'll just start empty.
        UI.elements.historyList.innerHTML = '<div style="text-align:center; color:var(--text-secondary); padding:20px;">Generated audio will appear here.</div>';
    }
};
