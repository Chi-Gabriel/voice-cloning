// ui-core.js - Core UI object and shared state
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

        // Analysis
        analysisDropArea: document.getElementById('analysis-drop-area'),
        analysisFiles: document.getElementById('analysis-files'),
        analysisPreview: document.getElementById('analysis-preview'),
        analysisLanguage: document.getElementById('analysis-language'),
        btnRunAnalysis: document.getElementById('btn-run-analysis'),
        analysisResultContainer: document.getElementById('analysis-result-container'),
        analysisStatus: document.getElementById('analysis-status'),
        analysisResultChat: document.getElementById('analysis-result-chat'),

        // Output Control
        playPauseBtn: document.getElementById('play-pause'),

        // Batch
        btnUpdateQueue: document.getElementById('btn-update-queue'),
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
        asrTimelineContainer: document.getElementById('asr-timeline-container'),
        asrScrubber: document.getElementById('asr-scrubber'),
        asrActiveSegment: document.getElementById('asr-active-segment'),
        asrPreview: document.getElementById('asr-preview'),

        // Diarization Elements
        diarizeDropArea: document.getElementById('diarize-drop-area'),
        diarizeFile: document.getElementById('diarize-file'),
        diarizePreview: document.getElementById('diarize-preview'),
        diarizeNumSpeakers: document.getElementById('diarize-num-speakers'),
        diarizeMinSpeakers: document.getElementById('diarize-min-speakers'),
        diarizeMaxSpeakers: document.getElementById('diarize-max-speakers'),
        diarizeLanguage: document.getElementById('diarize-language'),
        btnAddBatchDiarize: document.getElementById('btn-add-batch-diarize'),
        btnDiarizeNow: document.getElementById('btn-diarize-now'),
        diarizeResultContainer: document.getElementById('diarization-result-container'),
        diarizeTotalSpeakers: document.getElementById('diarize-total-speakers'),
        diarizeTimeMetric: document.getElementById('diarize-time-metric'),
        diarizePipeWrapper: document.getElementById('diarize-pipe-wrapper'),
        diarizeScrubber: document.getElementById('diarize-scrubber'),
        diarizeSpeakerLegend: document.getElementById('diarize-speaker-legend')
    },

    wavesurfer: null,
    batchQueue: [],
    currentVCFile: null, // Track selected file for Voice Cloning
    currentASRFile: null, // Track selected file for ASR
    currentDiarizeFile: null, // Track selected file for Diarization
    currentAnalysisFile: null,

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
    ]
};
