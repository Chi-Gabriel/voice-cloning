// ui-init.js - Initialization logic
UI.init = () => {
    UI.initTabs();
    UI.initWaveSurfer();
    UI.initLanguages();
    UI.initSliders();
    UI.loadHistory();

    const savedKey = Utils.getFromStorage('api_key');
    if (savedKey) {
        UI.elements.apiKeyInput.value = savedKey;
        API.setApiKey(savedKey);
    }

    UI.setupEventListeners();
};

UI.initTabs = () => {
    UI.elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.tab;
            UI.elements.tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            UI.elements.tabContents.forEach(c => c.classList.remove('active'));
            document.getElementById(target).classList.add('active');
        });
    });
};

UI.initWaveSurfer = () => {
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
};

UI.initLanguages = () => {
    const options = UI.languages.map(lang => `<option value="${lang.code}">${lang.name}</option>`).join('');
    if (UI.elements.vdLanguage) UI.elements.vdLanguage.innerHTML = options;
    if (UI.elements.vcLanguage) UI.elements.vcLanguage.innerHTML = options;
    if (UI.elements.cvLanguage) UI.elements.cvLanguage.innerHTML = options;
    if (UI.elements.asrLanguage) UI.elements.asrLanguage.innerHTML = options;
    if (UI.elements.analysisLanguage) UI.elements.analysisLanguage.innerHTML = options;
    if (UI.elements.diarizeLanguage) UI.elements.diarizeLanguage.innerHTML = options;
};

UI.initSliders = () => {
    [UI.elements.vdTemp, UI.elements.vcTemp, UI.elements.cvTemp].forEach(slider => {
        if (slider) {
            const valEl = document.getElementById(slider.id + '-value');
            slider.addEventListener('input', (e) => {
                if (valEl) valEl.textContent = e.target.value;
            });
            if (valEl) valEl.textContent = slider.value;
        }
    });
};
