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
        UI.elements.asrTimelineContainer.style.display = 'none';
        UI.elements.asrActiveSegment.style.display = 'none';

        const uploaded = await API.uploadFile(file);
        const lang = UI.elements.asrLanguage.value;
        const timestamps = UI.elements.asrTimestamps.checked;

        const response = await API.transcribeBatch([{
            file_id: uploaded.file_id,
            custom_id: file.name
        }], lang, timestamps);

        const result = response.items[0];
        let resultText = `Language: ${result.language}\n\n`;

        if (result.timestamps && result.timestamps.length > 0) {
            UI.renderASRTimeline(result.timestamps);
            result.timestamps.forEach(ts => {
                resultText += `[${ts.start_time.toFixed(2)}s - ${ts.end_time.toFixed(2)}s] ${ts.text}\n`;
            });
        } else {
            resultText += result.text;
        }

        UI.elements.asrResultText.textContent = resultText;
        UI.elements.asrResultContainer.style.display = 'block';

    } catch (error) {
        alert("Transcription Error: " + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
};

UI.renderASRTimeline = (timestamps) => {
    const container = UI.elements.asrTimelineContainer;
    const scrubber = UI.elements.asrScrubber;
    const activeText = UI.elements.asrActiveSegment;
    const audio = UI.elements.asrPreview;

    container.style.display = 'block';
    activeText.style.display = 'block';
    activeText.textContent = "Click a segment to see text...";

    // Clear existing lanes
    Array.from(container.children).forEach(child => {
        if (child.id !== 'asr-scrubber') container.removeChild(child);
    });

    const duration = timestamps[timestamps.length - 1].end_time;

    const row = document.createElement('div');
    row.className = 'diarize-row';

    const label = document.createElement('div');
    label.className = 'speaker-label';
    label.textContent = "Transcript";

    const lane = document.createElement('div');
    lane.className = 'diarize-lane';
    lane.style.height = '40px';

    row.appendChild(label);
    row.appendChild(lane);
    container.appendChild(row);

    timestamps.forEach(ts => {
        const el = document.createElement('div');
        el.className = 'diarize-segment';
        el.style.left = `${(ts.start_time / duration) * 100}%`;
        el.style.width = `${((ts.end_time - ts.start_time) / duration) * 100}%`;
        el.style.backgroundColor = 'var(--accent)';
        el.style.opacity = '0.7';
        el.style.border = '1px solid rgba(255,255,255,0.1)';

        el.onclick = (e) => {
            e.stopPropagation();
            activeText.textContent = ts.text;
            activeText.style.background = 'rgba(59, 130, 246, 0.2)';

            if (audio.src) {
                audio.playTargetEnd = ts.end_time;
                audio.currentTime = ts.start_time;
                audio.play();
            }
        };
        lane.appendChild(el);
    });

    audio.ontimeupdate = () => {
        const laneRect = lane.getBoundingClientRect();
        const wrapperRect = container.getBoundingClientRect();
        const offsetLeft = laneRect.left - wrapperRect.left;
        const currentPct = audio.currentTime / audio.duration;
        scrubber.style.left = `${offsetLeft + currentPct * laneRect.width}px`;

        if (audio.playTargetEnd && audio.currentTime >= audio.playTargetEnd) {
            audio.pause();
            audio.playTargetEnd = null;
        }
    };
};
