// ui-tts.js - TTS and Voice Cloning logic
UI.handleGeneration = async (mode) => {
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
};
