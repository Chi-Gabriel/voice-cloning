// ui-asr.js - ASR logic
UI.handleTranscribeNow = async () => {
    const btn = UI.elements.btnTranscribe;
    const originalText = btn.textContent;
    const file = UI.currentASRFile;

    if (!file) return alert("Please select a file first.");

    try {
        btn.disabled = true;
        btn.textContent = 'Transcribing...';
        UI.elements.asrResultContainer.style.display = 'none';
        if (UI.elements.asrTimelineContainer) UI.elements.asrTimelineContainer.style.display = 'none';
        if (UI.elements.asrActiveSegment) UI.elements.asrActiveSegment.style.display = 'none';

        const uploaded = await API.uploadFile(file);
        const lang = UI.elements.asrLanguage.value;
        const timestamps = UI.elements.asrTimestamps.checked;

        const response = await API.transcribeBatch([{
            file_id: uploaded.file_id,
            custom_id: file.name
        }], lang, timestamps);

        const result = response.items[0];

        UI.elements.asrResultText.innerHTML = '';
        const langHeader = document.createElement('div');
        langHeader.style.marginBottom = '10px';
        langHeader.style.color = 'var(--text-secondary)';
        langHeader.textContent = `Language: ${result.language}`;
        UI.elements.asrResultText.appendChild(langHeader);

        if (result.timestamps && result.timestamps.length > 0) {
            UI.renderInteractiveASR(result.timestamps);
        } else {
            const textNode = document.createElement('div');
            textNode.textContent = result.text;
            UI.elements.asrResultText.appendChild(textNode);
        }

        UI.elements.asrResultContainer.style.display = 'block';

    } catch (error) {
        alert("Transcription Error: " + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
};

UI.renderInteractiveASR = (timestamps) => {
    const textContainer = document.createElement('div');
    textContainer.style.lineHeight = '1.8';
    textContainer.style.fontSize = '1.05rem';
    UI.elements.asrResultText.appendChild(textContainer);

    const audio = UI.elements.asrPreview;
    const wordSpans = [];

    timestamps.forEach((ts, index) => {
        const span = document.createElement('span');
        span.textContent = ts.text + ' ';
        span.style.cursor = 'pointer';
        span.style.padding = '2px 4px';
        span.style.borderRadius = '4px';
        span.style.transition = 'background-color 0.1s, color 0.1s';
        span.title = `[${ts.start_time.toFixed(2)}s - ${ts.end_time.toFixed(2)}s]`;

        span.onmouseenter = () => {
            if (span.dataset.active !== "true") {
                span.style.backgroundColor = 'rgba(255,255,255,0.1)';
            }
        };
        span.onmouseleave = () => {
            if (span.dataset.active !== "true") {
                span.style.backgroundColor = 'transparent';
            }
        };

        span.onclick = () => {
            if (audio.src) {
                audio.currentTime = ts.start_time;
                // Play just this segment
                audio.playTargetEnd = ts.end_time;
                audio.play();
            }
        };

        textContainer.appendChild(span);
        wordSpans.push({ span, start: ts.start_time, end: ts.end_time });
    });

    audio.ontimeupdate = () => {
        const currentTime = audio.currentTime;
        let activeFound = false;

        wordSpans.forEach(item => {
            const isActive = currentTime >= item.start && currentTime <= item.end;
            if (isActive) {
                item.span.style.backgroundColor = 'var(--accent)';
                item.span.style.color = '#fff';
                item.span.dataset.active = "true";
                if (!activeFound) {
                    // Small auto-scroll logic if needed could go here
                    item.span.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    activeFound = true;
                }
            } else {
                item.span.style.backgroundColor = 'transparent';
                item.span.style.color = 'inherit';
                item.span.dataset.active = "false";
            }
        });

        if (audio.playTargetEnd && currentTime >= audio.playTargetEnd) {
            audio.pause();
            audio.playTargetEnd = null;
            // Optionally clear highlights after playing
            wordSpans.forEach(item => {
                item.span.style.backgroundColor = 'transparent';
                item.span.style.color = 'inherit';
                item.span.dataset.active = "false";
            });
        }
    };
};
