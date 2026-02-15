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
        vdTemp: document.getElementById('vd-temperature'),
        vdTempVal: document.getElementById('vd-temp-value'),
        btnDesign: document.getElementById('btn-generate-design'),

        // Voice Cloning
        vcText: document.getElementById('vc-text'),
        vcDropArea: document.getElementById('vc-drop-area'),
        vcFile: document.getElementById('vc-file'),
        vcPreview: document.getElementById('vc-preview'),
        vcRefText: document.getElementById('vc-ref-text'),
        vcLanguage: document.getElementById('vc-language'),
        vcTemp: document.getElementById('vc-temperature'),
        vcTempVal: document.getElementById('vc-temp-value'),
        btnClone: document.getElementById('btn-generate-clone'),

        // Custom Voice
        cvText: document.getElementById('cv-text'),
        cvSpeaker: document.getElementById('cv-speaker'),
        cvLanguage: document.getElementById('cv-language'),
        cvInstruct: document.getElementById('cv-instruct'),
        cvTemp: document.getElementById('cv-temperature'),
        cvTempVal: document.getElementById('cv-temp-value'),
        btnCustom: document.getElementById('btn-generate-custom'),

        // Output
        playPauseBtn: document.getElementById('play-pause'),
        timeDisplay: document.getElementById('time-display'),
        historyList: document.getElementById('history-list')
    },

    wavesurfer: null,
    batchQueue: [],

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
        UI.initSliders(); // Initialize sliders
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

    initSliders: () => {
        // Voice Design Temperature Slider
        UI.elements.vdTemp.addEventListener('input', (e) => {
            UI.elements.vdTempVal.textContent = e.target.value;
        });
        UI.elements.vdTempVal.textContent = UI.elements.vdTemp.value; // Set initial value

        // Voice Cloning Temperature Slider
        UI.elements.vcTemp.addEventListener('input', (e) => {
            UI.elements.vcTempVal.textContent = e.target.value;
        });
        UI.elements.vcTempVal.textContent = UI.elements.vcTemp.value; // Set initial value

        // Custom Voice Temperature Slider
        UI.elements.cvTemp.addEventListener('input', (e) => {
            UI.elements.cvTempVal.textContent = e.target.value;
        });
        UI.elements.cvTempVal.textContent = UI.elements.cvTemp.value; // Set initial value
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

        // Batch Buttons
        document.getElementById('btn-add-batch-design').addEventListener('click', () => UI.addToBatch('design'));
        document.getElementById('btn-add-batch-clone').addEventListener('click', () => UI.addToBatch('clone'));
        document.getElementById('btn-add-batch-custom').addEventListener('click', () => UI.addToBatch('custom'));

        document.getElementById('btn-clear-queue').addEventListener('click', () => {
            UI.batchQueue = [];
            UI.updateBatchUI();
        });

        document.getElementById('btn-run-batch').addEventListener('click', () => UI.runBatch());
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
                if (!text || !instruct) throw new Error('Text and Instruction are required');
                response = await API.voiceDesign(text, instruct, UI.elements.vdLanguage.value, parseFloat(UI.elements.vdTemp.value));
            } else if (mode === 'clone') {
                const text = UI.elements.vcText.value;
                const file = UI.elements.vcFile.files[0];
                const refText = UI.elements.vcRefText.value;
                if (!text || !file) throw new Error('Text and Reference Audio are required');
                response = await API.voiceCloneFile(text, file, refText, UI.elements.vcLanguage.value, parseFloat(UI.elements.vcTemp.value)); // Using multipart endpoint
            } else if (mode === 'custom') {
                const text = UI.elements.cvText.value;
                const speaker = UI.elements.cvSpeaker.value;
                const instruct = UI.elements.cvInstruct.value;
                if (!text || !speaker) throw new Error('Text and Speaker ID are required');
                response = await API.customVoice(text, speaker, UI.elements.cvLanguage.value, instruct, parseFloat(UI.elements.cvTemp.value));
            }

            if (response && response.items && response.items.length > 0) {
                const audioBase64 = response.items[0].audio_base64;
                const blob = Utils.base64ToBlob(audioBase64);
                const url = URL.createObjectURL(blob);

                UI.wavesurfer.load(url);
                UI.wavesurfer.play();
                UI.updatePlayButton(true);

                let displayText = "";
                if (mode === 'design') displayText = UI.elements.vdText.value;
                else if (mode === 'clone') displayText = UI.elements.vcText.value;
                else if (mode === 'custom') displayText = UI.elements.cvText.value;

                UI.addToHistory(mode, url, response.performance, displayText);
            }

        } catch (error) {
            alert(error.message);
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    },

    addToBatch: async (mode) => {
        const btnId = `btn-add-batch-${mode}`;
        const btn = document.getElementById(btnId);
        const originalText = btn.textContent;

        try {
            btn.disabled = true;
            btn.textContent = 'Adding...';

            if (mode === 'design') {
                const text = UI.elements.vdText.value;
                const instruct = UI.elements.vdInstruct.value;
                const lang = UI.elements.vdLanguage.value;
                const temp = parseFloat(UI.elements.vdTemp.value);

                if (!text) return alert("Text is required");
                if (!instruct) return alert("Instruction is required");

                UI.batchQueue.push({ id: Utils.generateId(), mode, text, instruct, lang, temp });
            } else if (mode === 'clone') {
                const text = UI.elements.vcText.value;
                const refText = UI.elements.vcRefText.value;
                const lang = UI.elements.vcLanguage.value;
                const temp = parseFloat(UI.elements.vcTemp.value);
                const file = UI.elements.vcFile.files[0];

                if (!text) return alert("Text is required");
                if (!file) return alert("Reference Audio is required");

                // Upload file first
                btn.textContent = 'Uploading...';
                const uploadRes = await API.uploadFile(file);
                const file_id = uploadRes.file_id;
                const fileName = file.name;

                UI.batchQueue.push({ id: Utils.generateId(), mode, text, refText, lang, file_id, fileName, temp });
            } else if (mode === 'custom') {
                const text = UI.elements.cvText.value;
                const speaker = UI.elements.cvSpeaker.value;
                const lang = UI.elements.cvLanguage.value;
                const instruct = UI.elements.cvInstruct.value;
                const temp = parseFloat(UI.elements.cvTemp.value);

                if (!text) return alert("Text is required");
                if (!speaker) return alert("Speaker ID is required");

                UI.batchQueue.push({ id: Utils.generateId(), mode, text, speaker, lang, instruct, temp });
            }

            UI.updateBatchUI();

            // Visual feedback
            btn.textContent = 'Added!';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.disabled = false;
            }, 1000);

        } catch (error) {
            alert(error.message);
            btn.textContent = originalText;
            btn.disabled = false;
        }
    },

    removeFromBatch: (index) => {
        UI.batchQueue.splice(index, 1);
        UI.updateBatchUI();
    },

    updateBatchUI: () => {
        const container = document.getElementById('batch-queue-container');
        const list = document.getElementById('batch-list');
        const count = document.getElementById('queue-count');

        count.textContent = UI.batchQueue.length;

        if (UI.batchQueue.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'block';
        list.innerHTML = '';

        UI.batchQueue.forEach((item, index) => {
            const el = document.createElement('div');
            el.className = 'queue-item';
            el.innerHTML = `
                <div class="q-info">
                    <span class="q-type">${item.mode.replace('-', ' ')}</span>
                    <span class="q-text">${item.text}</span>
                </div>
                <button class="btn-delete" onclick="UI.removeFromBatch(${index})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            `;
            list.appendChild(el);
        });
    },

    runBatch: async () => {
        if (UI.batchQueue.length === 0) return;

        const btn = document.getElementById('btn-run-batch');
        btn.disabled = true;
        btn.textContent = 'Processing...';

        try {
            // Group by mode
            const batches = {};
            UI.batchQueue.forEach(item => {
                if (!batches[item.mode]) batches[item.mode] = [];
                batches[item.mode].push(item);
            });

            for (const mode in batches) {
                const items = batches[mode];
                const texts = items.map(i => i.text);
                const langs = items.map(i => i.lang);

                let response;

                if (mode === 'design') {
                    const instructs = items.map(i => i.instruct);
                    const temps = items.map(i => i.temp);
                    // Assumption: use temperature of first item for the batch request if scalar, 
                    // but backend supports list or scalar. For simplicity, we use scalar if all same, 
                    // or just pass first one if not specified or list of them.
                    // Actually, let's pass the list!
                    response = await API.voiceDesign(texts, instructs, langs, temps);
                } else if (mode === 'custom') {
                    const speakers = items.map(i => i.speaker);
                    const instructs = items.map(i => i.instruct);
                    const temps = items.map(i => i.temp);
                    response = await API.customVoice(texts, speakers, langs, instructs, temps);
                } else if (mode === 'clone') {
                    // Group by file_id for optimized batching
                    const fileGroups = {};
                    const sequentialItems = [];

                    items.forEach(item => {
                        if (item.file_id) {
                            if (!fileGroups[item.file_id]) fileGroups[item.file_id] = [];
                            fileGroups[item.file_id].push(item);
                        } else {
                            sequentialItems.push(item); // Fallback for raw files (shouldn't happen with new logic)
                        }
                    });

                    // 1. Process File Groups (Optimized Batch)
                    for (const fileId in fileGroups) {
                        const groupItems = fileGroups[fileId];
                        const groupTexts = groupItems.map(i => i.text);
                        // Assumption: Language is same for the file? Protocol says list is supported.
                        const groupLangs = groupItems.map(i => i.lang);
                        const groupRefTexts = groupItems.map(i => i.refText);

                        const res = await API.voiceClone(groupTexts, fileId, groupRefTexts, groupLangs, groupItems.map(i => i.temp));
                        if (res && res.items) {
                            res.items.forEach((r, idx) => {
                                const originalItem = groupItems[idx];
                                const text = originalItem ? originalItem.text : "";
                                const url = r.url || URL.createObjectURL(Utils.base64ToBlob(r.audio_base64));
                                console.log(`Batch Result [${idx}]: ${text} -> ${url}`);
                                UI.addToHistory(mode, url, res.performance, text);
                            });
                        }
                    }

                    // 2. Process Sequential (Fallback)
                    for (const item of sequentialItems) {
                        const res = await API.voiceCloneFile(item.text, item.file, item.refText, item.lang, item.temp);
                        if (res && res.items) {
                            res.items.forEach(r => {
                                const url = r.url || URL.createObjectURL(Utils.base64ToBlob(r.audio_base64));
                                UI.addToHistory(mode, url, res.performance, item.text);
                            });
                        }
                    }
                    continue;
                }

                if (response && response.items) {
                    response.items.forEach((r, idx) => {
                        const originalItem = items[idx];
                        const text = originalItem ? originalItem.text : "";
                        const url = r.url || URL.createObjectURL(Utils.base64ToBlob(r.audio_base64));
                        UI.addToHistory(mode, url, response.performance, text);
                    });
                }
            }

            // Clear queue on success
            UI.batchQueue = [];
            UI.updateBatchUI();

        } catch (error) {
            alert("Batch Error: " + error.message);
        } finally {
            btn.disabled = false;
            btn.textContent = 'Run Batch';
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

    addToHistory: (mode, url, performance, text = "") => {
        const item = {
            id: Utils.generateId(),
            mode: mode,
            url: url,
            text: text,
            performance: performance,
            timestamp: new Date().toLocaleString()
        };

        const el = document.createElement('div');
        el.className = 'history-item';
        el.innerHTML = `
            <div class="history-info">
                <strong>${mode.toUpperCase().replace('-', ' ')}</strong>
                <span style="font-size:0.7em; color:var(--accent); margin-left:10px;">ID: ${item.id}</span>
                <span>${item.timestamp}</span>
                <span class="history-text" style="display:block; font-size:0.9em; margin-top:4px; color:var(--text-primary); font-style:italic; opacity:0.8;">
                    "${text}"
                </span>
                <span style="font-size: 0.8em; color: var(--accent); display: block; margin-top: 4px;">
                    generated in ${item.performance ? item.performance.toFixed(2) + 's' : 'N/A'}
                </span>
                <code style="font-size:0.7em; background:rgba(0,0,0,0.2); padding:2px 4px; border-radius:3px; display:inline-block; margin-top:4px;">
                    ${url}
                </code>
            </div>
            <div class="history-actions">
                <button onclick="console.log('Playing: ${url}'); UI.wavesurfer.load('${url}'); UI.wavesurfer.play();">Play</button>
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
