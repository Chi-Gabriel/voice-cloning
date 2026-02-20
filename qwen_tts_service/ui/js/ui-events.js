// ui-events.js - Event listeners
UI.setupEventListeners = () => {
    // API Key
    UI.elements.apiKeyInput.addEventListener('change', (e) => {
        const key = e.target.value.trim();
        API.setApiKey(key);
        Utils.saveToStorage('api_key', key);
    });

    // Voice Clone File Upload
    const vcDropArea = UI.elements.vcDropArea;
    const vcFileInput = UI.elements.vcFile;

    const preventDefaults = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        vcDropArea.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        vcDropArea.addEventListener(eventName, () => vcDropArea.classList.add('is-active'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        vcDropArea.addEventListener(eventName, () => vcDropArea.classList.remove('is-active'), false);
    });

    vcDropArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        handleVCFiles(dt.files);
    });

    vcFileInput.addEventListener('change', (e) => {
        handleVCFiles(e.target.files);
    });

    function handleVCFiles(files) {
        if (files.length > 0) {
            UI.currentVCFile = files[0];
            const preview = UI.elements.vcPreview;
            preview.src = URL.createObjectURL(files[0]);
            preview.style.display = 'block';
            vcDropArea.querySelector('.file-msg').textContent = files[0].name;
        }
    }

    // ASR File Upload
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
        if (files.length > 0) {
            UI.currentASRFile = files[0];
            const preview = UI.elements.asrPreview;
            preview.src = URL.createObjectURL(files[0]);
            preview.style.display = 'block';
            asrDrop.querySelector('.file-msg').textContent = files[0].name;
        }
    }

    // Diarization File Upload
    const diarizeDrop = UI.elements.diarizeDropArea;
    const diarizeInput = UI.elements.diarizeFile;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        diarizeDrop.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        diarizeDrop.addEventListener(eventName, () => diarizeDrop.classList.add('is-active'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        diarizeDrop.addEventListener(eventName, () => diarizeDrop.classList.remove('is-active'), false);
    });

    diarizeDrop.addEventListener('drop', (e) => {
        handleDiarizeFiles(e.dataTransfer.files);
    });

    diarizeInput.addEventListener('change', (e) => {
        handleDiarizeFiles(e.target.files);
    });

    function handleDiarizeFiles(files) {
        if (files.length > 0) {
            UI.currentDiarizeFile = files[0];
            const preview = UI.elements.diarizePreview;
            preview.src = URL.createObjectURL(files[0]);
            preview.style.display = 'block';
            diarizeDrop.querySelector('.file-msg').textContent = files[0].name;
        }
    }

    // Play/Pause
    UI.elements.playPauseBtn.addEventListener('click', () => {
        UI.wavesurfer.playPause();
        UI.updatePlayButton(UI.wavesurfer.isPlaying());
    });

    // Action Buttons
    UI.elements.btnDesign.addEventListener('click', () => UI.handleGeneration('design'));
    UI.elements.btnClone.addEventListener('click', () => UI.handleGeneration('clone'));
    UI.elements.btnCustom.addEventListener('click', () => UI.handleGeneration('custom'));

    document.getElementById('btn-add-batch-design').addEventListener('click', () => UI.addToBatch('design'));
    document.getElementById('btn-add-batch-clone').addEventListener('click', () => UI.addToBatch('clone'));
    document.getElementById('btn-add-batch-custom').addEventListener('click', () => UI.addToBatch('custom'));
    document.getElementById('btn-add-batch-asr').addEventListener('click', () => UI.addToBatch('asr'));
    UI.elements.btnAddBatchDiarize.addEventListener('click', () => UI.addToBatch('diarize'));

    UI.elements.btnTranscribe.addEventListener('click', () => UI.handleTranscribeNow());
    UI.elements.btnDiarizeNow.onclick = UI.handleDiarizeNow;

    // Smart Transcript Events
    const analysisDrop = UI.elements.analysisDropArea;
    const analysisInput = UI.elements.analysisFiles;

    analysisDrop.addEventListener('dragover', (e) => { e.preventDefault(); analysisDrop.classList.add('is-active'); });
    analysisDrop.addEventListener('dragleave', () => analysisDrop.classList.remove('is-active'));
    analysisDrop.addEventListener('drop', (e) => { e.preventDefault(); analysisDrop.classList.remove('is-active'); handleAnalysisFiles(e.dataTransfer.files); });
    analysisInput.addEventListener('change', (e) => handleAnalysisFiles(e.target.files));

    function handleAnalysisFiles(files) {
        if (files.length > 0) {
            UI.currentAnalysisFile = files[0];
            UI.elements.analysisPreview.src = URL.createObjectURL(files[0]);
            UI.elements.analysisPreview.style.display = 'block';
            analysisDrop.querySelector('.file-msg').textContent = files[0].name;
        }
    }

    UI.elements.btnRunAnalysis.onclick = UI.handleRunAnalysis;

    // Batch Update
    UI.elements.btnUpdateQueue.onclick = UI.updateQueue;
    const btnClearQueue = document.getElementById('btn-clear-queue');
    if (btnClearQueue) {
        btnClearQueue.addEventListener('click', () => {
            UI.batchQueue = [];
            UI.updateBatchUI();
        });
    }

    const btnRunBatch = document.getElementById('btn-run-batch');
    if (btnRunBatch) {
        btnRunBatch.addEventListener('click', () => UI.runBatch());
    }
};
