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
        vcEnhanced: document.getElementById('vc-enhanced'),
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
        historyList: document.getElementById('history-list'),

        // ASR Elements
        asrFiles: document.getElementById('asr-files'),
        asrDropArea: document.getElementById('asr-drop-area'),
        asrFileList: document.getElementById('asr-file-list'),
        asrLanguage: document.getElementById('asr-language'),
        asrTimestamps: document.getElementById('asr-timestamps'),
        btnTranscribe: document.getElementById('btn-transcribe-now'),
        btnAddBatchASR: document.getElementById('btn-add-batch-asr'),
        asrResultContainer: document.getElementById('asr-result-container'),
        asrResultText: document.getElementById('asr-result-text'),
        asrPreview: document.getElementById('asr-preview')
    },

    wavesurfer: null,
    batchQueue: [],
    currentVCFile: null, // Track selected file for Voice Cloning
    asrSelectedFiles: [], // Track selected files for ASR

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
        UI.elements.asrLanguage.innerHTML = options;
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

        // Voice Clone File Upload (drag-and-drop)
        const dropArea = UI.elements.vcDropArea;
        const fileInput = UI.elements.vcFile;

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.add('is-active'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.remove('is-active'), false);
        });

        dropArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            handleVCFiles(dt.files);
        });

        fileInput.addEventListener('change', (e) => {
            handleVCFiles(e.target.files);
        });

        function handleVCFiles(files) {
            if (files.length > 0) {
                UI.currentVCFile = files[0];
                const preview = UI.elements.vcPreview;
                preview.src = URL.createObjectURL(files[0]);
                preview.style.display = 'block';
                dropArea.querySelector('.file-msg').textContent = files[0].name;
            }
        }

        // ASR File Upload (drag-and-drop)
        const asrDrop = UI.elements.asrDropArea;
        const asrInput = UI.elements.asrFiles;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            asrDrop.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            asrDrop.addEventListener(eventName, () => asrDrop.classList.add('is-active'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            asrDrop.addEventListener(eventName, () => asrDrop.classList.remove('is-active'), false);
        });

        asrDrop.addEventListener('drop', (e) => {
            handleASRFiles(e.dataTransfer.files);
        });

        asrInput.addEventListener('change', (e) => {
            handleASRFiles(e.target.files);
        });

        function handleASRFiles(files) {
            for (let i = 0; i < files.length; i++) {
                if (files[i].type.startsWith('audio/')) {
                    UI.asrSelectedFiles.push(files[i]);
                }
            }
            UI.updateASRFileList();

            // Load the first new file into preview if it exists
            if (UI.asrSelectedFiles.length > 0) {
                UI.selectASRPreview(0);
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
        document.getElementById('btn-add-batch-asr').addEventListener('click', () => UI.addToBatch('asr'));

        // Transcribe Now Button
        UI.elements.btnTranscribe.addEventListener('click', () => UI.handleTranscribeNow());

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
                const text = UI.elements.vcText.value.trim();
                const fileInput = UI.elements.vcFile;
                const file = UI.currentVCFile || (fileInput.files && fileInput.files[0]);
                const refText = UI.elements.vcRefText.value;
                const enhanced = UI.elements.vcEnhanced.checked;

                if (!text) throw new Error('Please enter the text you want to speak.');
                if (!file) throw new Error('Please select or drag a reference audio file first.');

                console.log("Generating Enhanced Clone:", { enhanced, textLength: text.length, fileName: file.name });
                response = await API.voiceCloneFile(text, file, refText, UI.elements.vcLanguage.value, parseFloat(UI.elements.vcTemp.value), enhanced);
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

        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    },

    updateASRFileList: () => {
        const list = UI.elements.asrFileList;
        const dropMsg = UI.elements.asrDropArea.querySelector('.file-msg');

        if (UI.asrSelectedFiles.length === 0) {
            list.style.display = 'none';
            UI.elements.asrPreview.style.display = 'none';
            dropMsg.textContent = 'or drag and drop multiple files here';
            return;
        }

        list.style.display = 'flex';
        list.innerHTML = '';
        dropMsg.textContent = `${UI.asrSelectedFiles.length} files selected`;

        UI.asrSelectedFiles.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'queue-item';
            item.innerHTML = `
                <div class="q-info" onclick="UI.selectASRPreview(${index})" style="cursor:pointer; flex:1;">
                    <span class="q-text" style="font-weight:500;">${file.name}</span>
                    <span class="q-type">${(file.size / 1024 / 1024).toFixed(2)} MB</span>
                </div>
                <div class="q-actions">
                    <button class="btn-delete" onclick="UI.removeASRFile(${index})" title="Remove">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
            `;
            list.appendChild(item);
        });
    },

    selectASRPreview: (index) => {
        const file = UI.asrSelectedFiles[index];
        if (file) {
            const player = UI.elements.asrPreview;
            player.src = URL.createObjectURL(file);
            player.style.display = 'block';

            // Highlight active item in list
            const items = UI.elements.asrFileList.querySelectorAll('.queue-item');
            items.forEach((item, i) => {
                if (i === index) item.classList.add('is-processing'); // Highlighting active
                else item.classList.remove('is-processing');
            });
        }
    },

    removeASRFile: (index) => {
        UI.asrSelectedFiles.splice(index, 1);
        UI.updateASRFileList();
    },

    handleTranscribeNow: async () => {
        const btn = UI.elements.btnTranscribe;
        const originalText = btn.textContent;
        const files = UI.asrSelectedFiles;

        if (files.length === 0) return alert("Please select files first.");

        try {
            btn.disabled = true;
            btn.textContent = 'Uploading...';
            UI.elements.asrResultContainer.style.display = 'none';

            // 1. Upload all files
            const uploadedItems = [];
            for (let f of files) {
                const res = await API.uploadFile(f);
                uploadedItems.push({
                    file_id: res.file_id,
                    custom_id: f.name
                });
            }

            // 2. Transcribe
            btn.textContent = 'Transcribing...';
            const lang = UI.elements.asrLanguage.value;
            const timestamps = UI.elements.asrTimestamps.checked;

            const response = await API.transcribeBatch(uploadedItems, lang, timestamps);

            // 3. Display Results
            let resultText = "";
            response.items.forEach(item => {
                resultText += `[${item.custom_id}] (${item.language})\n`;
                if (item.timestamps) {
                    item.timestamps.forEach(ts => {
                        resultText += `[${ts.start_time.toFixed(2)}s - ${ts.end_time.toFixed(2)}s] ${ts.text}\n`;
                    });
                } else {
                    resultText += `${item.text}\n`;
                }
                resultText += "\n" + "-".repeat(40) + "\n\n";
            });

            UI.elements.asrResultText.textContent = resultText;
            UI.elements.asrResultContainer.style.display = 'block';

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
                const text = UI.elements.vcText.value.trim();
                const refText = UI.elements.vcRefText.value;
                const lang = UI.elements.vcLanguage.value;
                const temp = parseFloat(UI.elements.vcTemp.value);
                const enhanced = UI.elements.vcEnhanced.checked;
                const fileInput = UI.elements.vcFile;
                const file = UI.currentVCFile || (fileInput.files && fileInput.files[0]);

                if (!text) return alert("Please enter text before adding to batch.");
                if (!file) return alert("Please select a reference audio file first.");

                btn.textContent = 'Uploading...';
                const uploadRes = await API.uploadFile(file);
                const file_id = uploadRes.file_id;
                const fileName = file.name;

                UI.batchQueue.push({ id: Utils.generateId(), mode, text, refText, lang, file_id, fileName, temp, enhanced });
            } else if (mode === 'custom') {
                const text = UI.elements.cvText.value;
                const speaker = UI.elements.cvSpeaker.value;
                const lang = UI.elements.cvLanguage.value;
                const instruct = UI.elements.cvInstruct.value;
                const temp = parseFloat(UI.elements.cvTemp.value);

                if (!text) return alert("Text is required");
                if (!speaker) return alert("Speaker ID is required");

                UI.batchQueue.push({ id: Utils.generateId(), mode, text, speaker, lang, instruct, temp });
            } else if (mode === 'asr') {
                const files = UI.asrSelectedFiles;
                if (files.length === 0) return alert("Please select files first.");

                const lang = UI.elements.asrLanguage.value;
                const timestamps = UI.elements.asrTimestamps.checked;

                btn.textContent = `Uploading ${files.length} files...`;

                for (let f of files) {
                    const res = await API.uploadFile(f);
                    UI.batchQueue.push({
                        id: Utils.generateId(),
                        mode: 'asr',
                        text: f.name,
                        file_id: res.file_id,
                        lang,
                        timestamps
                    });
                }

                UI.asrSelectedFiles = [];
                UI.updateASRFileList();
            }

            UI.updateBatchUI();

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
            el.setAttribute('data-id', item.id);
            el.setAttribute('data-status', 'queued');
            el.innerHTML = `
                <div class="q-info">
                    <span class="q-type">${item.mode.replace('-', ' ')}</span>
                    <span class="q-text">${item.text}</span>
                    <span class="q-status badge status-queued">queued</span>
                </div>
                <button class="btn-delete" onclick="UI.removeFromBatch(${index})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            `;
            list.appendChild(el);
        });
    },

    removeFromBatch: (index) => {
        UI.batchQueue.splice(index, 1);
        UI.updateBatchUI();
    },


    runBatch: async () => {
        if (UI.batchQueue.length === 0) return;

        const btn = document.getElementById('btn-run-batch');
        const clearBtn = document.getElementById('btn-clear-queue');
        btn.disabled = true;
        clearBtn.disabled = true;
        btn.textContent = 'Submitting...';

        try {
            // 1. Map UI queue items to API QueueItemRequest
            const queueItems = UI.batchQueue.map(item => {
                let operation = item.mode;
                if (item.mode === 'design') operation = 'voice_design';
                if (item.mode === 'custom') operation = 'custom_voice';
                if (item.mode === 'clone') {
                    operation = item.enhanced ? 'voice_clone_enhanced' : 'voice_clone';
                }
                if (item.mode === 'asr') operation = 'transcribe';

                return {
                    text: item.text, // For ASR this is filename (ignored by backend but useful for debugging)
                    operation: operation,
                    ref_audio: item.file_id || null,
                    ref_text: item.refText || null,
                    instruct: item.instruct || null,
                    speaker: item.speaker || null,
                    language: item.lang || 'auto',
                    temperature: item.temp || 0.3,
                    return_timestamps: item.timestamps || false,
                    custom_id: item.id // Keep UI ID for tracking
                };
            });

            // 2. Submit to Queue
            const response = await API.submitBatchToQueue(queueItems, `Web UI Batch ${new Date().toLocaleTimeString()} `);
            const batchId = response.batch_id;

            console.log("Batch submitted:", batchId);
            btn.textContent = 'Processing...';

            // 3. Start Polling
            UI.pollQueueStatus(batchId);

        } catch (error) {
            alert("Batch Error: " + error.message);
            btn.disabled = false;
            clearBtn.disabled = false;
            btn.textContent = 'Run Batch';
        }
    },

    pollQueueStatus: async (batchId) => {
        const btn = document.getElementById('btn-run-batch');
        const clearBtn = document.getElementById('btn-clear-queue');

        const poll = async () => {
            try {
                const statusRes = await API.getQueueStatus(batchId);
                UI.updateQueueProgress(statusRes);

                if (statusRes.status === 'completed' || statusRes.status === 'partial' || statusRes.status === 'error') {
                    // Batch finished
                    UI.handleQueueCompletion(batchId);
                    btn.disabled = false;
                    clearBtn.disabled = false;
                    btn.textContent = 'Run Batch';
                    return;
                }

                // Continue polling
                setTimeout(poll, 2000);
            } catch (error) {
                console.error("Polling error:", error);
                btn.disabled = false;
                clearBtn.disabled = false;
                btn.textContent = 'Run Batch';
            }
        };

        poll();
    },

    updateQueueProgress: (statusResponse) => {
        const count = document.getElementById('queue-count');
        count.textContent = `${statusResponse.completed}/${statusResponse.total}`;

        // Update individual item statuses in UI
        statusResponse.items.forEach(item => {
            const el = document.querySelector(`.queue-item[data-id="${item.custom_id}"]`);
            if (el) {
                el.setAttribute('data-status', item.status);
                const statusBadge = el.querySelector('.q-status');
                if (statusBadge) {
                    statusBadge.textContent = item.status;
                    statusBadge.className = `q-status badge status-${item.status}`;
                }

                // If processing, add a class for animation
                if (item.status === 'processing') {
                    el.classList.add('is-processing');
                } else {
                    el.classList.remove('is-processing');
                }
            }
        });
    },

    handleQueueCompletion: async (batchId) => {
        try {
            const results = await API.getQueueResults(batchId);

            results.items.forEach(item => {
                if (item.status === 'done' && item.url) {
                    // Find original item info for history
                    const originalItem = UI.batchQueue.find(i => i.id === item.custom_id);
                    const mode = originalItem ? originalItem.mode : 'unknown';
                    const text = originalItem ? originalItem.text : (item.custom_id || "Queued Text");

                    // For ASR, the URL is a JSON file, not audio. We need to handle this differently.
                    // But for History consistency, we can still add it, but maybe change "Play" button logic?
                    // For now, let's just add it. The API returns .json for transcribe.

                    UI.addToHistory(mode, item.url, 0, text);
                } else if (item.status === 'error') {
                    console.error(`Item ${item.item_id} failed: ${item.error}`);
                }
            });

            // Clear the queue UI after a short delay
            setTimeout(() => {
                UI.batchQueue = [];
                UI.updateBatchUI();
            }, 3000);

        } catch (error) {
            console.error("Error handling queue completion:", error);
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
                ${mode === 'asr'
                ? `<a href="${url}" target="_blank" style="color:var(--accent); text-decoration:none; font-size:0.9rem;">View JSON</a>`
                : `<button onclick="console.log('Playing: ${url}'); UI.wavesurfer.load('${url}'); UI.wavesurfer.play();">Play</button>`
            }
                <a href="${url}" download="${mode === 'asr' ? 'transcript.json' : 'generated_' + item.id + '.wav'}" style="color:var(--accent); text-decoration:none; font-size:0.9rem; margin-left:8px;">Download</a>
            </div>
        `;

        UI.elements.historyList.prepend(el);
    },

    loadHistory: () => {
        // Since we can't persist blob URLs easily without IndexedDB, we'll just start empty.
        UI.elements.historyList.innerHTML = '<div style="text-align:center; color:var(--text-secondary); padding:20px;">Generated audio will appear here.</div>';
    }
};
