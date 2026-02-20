// ui-diarization.js - Diarization logic
UI.handleDiarizeNow = async () => {
    const btn = UI.elements.btnDiarizeNow;
    const originalText = btn.textContent;
    const file = UI.currentDiarizeFile;

    if (!file) return alert("Please select an audio file first.");

    try {
        btn.disabled = true;
        btn.textContent = 'Diarizing...';
        UI.elements.diarizeResultContainer.style.display = 'none';

        const numS = UI.elements.diarizeNumSpeakers.value;
        const minS = UI.elements.diarizeMinSpeakers.value;
        const maxS = UI.elements.diarizeMaxSpeakers.value;

        const response = await API.diarizeFile(
            file,
            numS ? parseInt(numS) : null,
            minS ? parseInt(minS) : null,
            maxS ? parseInt(maxS) : null
        );

        const fileURL = URL.createObjectURL(file);
        UI.renderDiarizationPipe(response, fileURL, response.performance);

    } catch (error) {
        alert("Diarization Error: " + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
};

UI.renderDiarizationPipe = (diarizeItem, fileURL, performanceSecs) => {
    const container = UI.elements.diarizeResultContainer;
    const pipeWrapper = UI.elements.diarizePipeWrapper;
    const legend = UI.elements.diarizeSpeakerLegend;
    const scrubber = UI.elements.diarizeScrubber;
    const audio = UI.elements.diarizePreview;

    container.style.display = 'block';

    // Clear existing rows (except scrubber)
    Array.from(pipeWrapper.children).forEach(child => {
        if (child.id !== 'diarize-scrubber') {
            pipeWrapper.removeChild(child);
        }
    });
    legend.innerHTML = '';

    const segments = diarizeItem.segments || [];
    if (segments.length === 0) {
        UI.elements.diarizeTotalSpeakers.textContent = "Found: 0 Speakers";
        return;
    }

    const duration = segments.reduce((max, s) => Math.max(max, s.end), 0);
    const speakers = new Set();
    segments.forEach(s => speakers.add(s.speaker));

    UI.elements.diarizeTotalSpeakers.textContent = `Found: ${speakers.size} Speakers`;
    UI.elements.diarizeTimeMetric.textContent = `Process Time: ${(performanceSecs || 0).toFixed(2)}s`;

    const baseColors = [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
        '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'
    ];
    const speakerColors = {};
    const speakerLanes = {};

    Array.from(speakers).sort().forEach((spk, idx) => {
        speakerColors[spk] = baseColors[idx % baseColors.length];

        // Legend
        const badge = document.createElement('div');
        badge.className = 'speaker-badge';
        badge.innerHTML = `<div class="speaker-color-dot" style="background-color: ${speakerColors[spk]}"></div><span>${spk}</span>`;
        legend.appendChild(badge);

        // Row and Lane
        const row = document.createElement('div');
        row.className = 'diarize-row';

        const label = document.createElement('div');
        label.className = 'speaker-label';
        label.textContent = spk;

        const lane = document.createElement('div');
        lane.className = 'diarize-lane';
        lane.onclick = (e) => {
            const rect = lane.getBoundingClientRect();
            const clickPos = e.clientX - rect.left;
            const pct = clickPos / rect.width;
            if (audio.src && audio.duration) {
                audio.playTargetEnd = null;
                audio.currentTime = pct * audio.duration;
                audio.play();
            }
        };

        row.appendChild(label);
        row.appendChild(lane);
        pipeWrapper.appendChild(row);
        speakerLanes[spk] = lane;
    });

    segments.forEach(seg => {
        const lane = speakerLanes[seg.speaker];
        const el = document.createElement('div');
        el.className = 'diarize-segment';
        el.style.left = `${(seg.start / duration) * 100}%`;
        el.style.width = `${((seg.end - seg.start) / duration) * 100}%`;
        el.style.backgroundColor = speakerColors[seg.speaker];

        const durationSecs = (seg.end - seg.start).toFixed(1);
        el.innerHTML = `<div class="diarize-tooltip">${seg.speaker} (${durationSecs}s)</div>`;

        el.onclick = (e) => {
            e.stopPropagation();
            if (audio.src) {
                audio.playTargetEnd = seg.end;
                audio.currentTime = seg.start;
                audio.play();
            }
        };
        lane.appendChild(el);
    });

    audio.src = fileURL;
    audio.onloadedmetadata = () => {
        audio.ontimeupdate = () => {
            // Update scrubber position
            const firstLane = Object.values(speakerLanes)[0];
            if (firstLane) {
                const laneRect = firstLane.getBoundingClientRect();
                const wrapperRect = pipeWrapper.getBoundingClientRect();
                const offsetLeft = laneRect.left - wrapperRect.left;
                const currentPct = audio.currentTime / audio.duration;
                scrubber.style.left = `${offsetLeft + currentPct * laneRect.width}px`;
            }

            // Auto-stop if reached segment end
            if (audio.playTargetEnd && audio.currentTime >= audio.playTargetEnd) {
                audio.pause();
                audio.playTargetEnd = null;
            }
        };
    };
};
