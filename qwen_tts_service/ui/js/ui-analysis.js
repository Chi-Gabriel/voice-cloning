// ui-analysis.js - Smart Transcript Logic (ASR + Diarization Alignment)

UI.handleRunAnalysis = async () => {
    const btn = UI.elements.btnRunAnalysis;
    const file = UI.currentAnalysisFile;
    const container = UI.elements.analysisResultContainer;
    const status = UI.elements.analysisStatus;
    const chat = UI.elements.analysisResultChat;
    const lang = UI.elements.analysisLanguage.value;

    if (!file) return alert("Please select a file first.");

    try {
        btn.disabled = true;
        btn.textContent = "Processing...";
        container.style.display = 'block';
        chat.innerHTML = '';

        // Step 1: Upload
        status.textContent = "Step 1/3: Uploading audio...";
        const uploaded = await API.uploadFile(file);

        // Step 2: ASR with Timestamps
        status.textContent = "Step 2/3: Transcribing (getting timestamps)...";
        const asrRes = await API.transcribeBatch([{ file_id: uploaded.file_id, custom_id: 'analysis' }], lang, true);
        const asrData = asrRes.items[0];

        // Step 3: Diarization
        status.textContent = "Step 3/3: Identifying speakers...";
        const diarizeRes = await API.diarizeBatch([{ file_id: uploaded.file_id, custom_id: 'analysis' }]);
        const diarizeData = diarizeRes.items[0];

        // Step 4: Logic - Align and Merge
        status.textContent = "Finalizing: Aligning text with speakers...";
        const punctuatedWords = UI.alignPunctuation(asrData.timestamps, asrData.text);
        const mergedTurns = UI.mergeSpeechAndSpeakers(punctuatedWords, diarizeData.segments);

        // Render
        UI.renderAnalysisChat(mergedTurns);
        status.textContent = "Analysis Complete.";

    } catch (err) {
        alert("Analysis Error: " + err.message);
        status.textContent = "Analysis Failed.";
    } finally {
        btn.disabled = false;
        btn.textContent = "Generate Smart Transcript";
    }
};

/**
 * Case-insensitive lookahead to find punctuation from fullText.
 * Uses a fuzzy search to tolerate minor ASR tokenization differences.
 */
UI.alignPunctuation = (timedWords, fullText) => {
    let result = [];
    let currentPos = 0;
    const lowerText = fullText.toLowerCase();

    for (let i = 0; i < timedWords.length; i++) {
        const word = timedWords[i];
        const nextWord = timedWords[i + 1];

        // Skip metadata tokens like <|en|>
        if (word.text.startsWith('<|') && word.text.endsWith('|')) continue;

        const cleanWord = word.text.toLowerCase().trim();
        if (!cleanWord) continue;

        // Find the start of this word in fullText (case-insensitive)
        let wordStart = lowerText.indexOf(cleanWord, currentPos);

        // If not found, try a small backtrack or skip
        if (wordStart === -1) {
            // Try to find it nearby if there was a slight drift
            wordStart = lowerText.indexOf(cleanWord, Math.max(0, currentPos - 5));
        }

        if (wordStart === -1) {
            // Fallback: push word with a default space
            result.push({ ...word, punctuated: word.text + ' ' });
            continue;
        }

        let wordWithSuffix = "";
        let suffixEnd = wordStart + cleanWord.length;

        // Look ahead for the next word to determine the junction (punctuation/spaces)
        if (nextWord) {
            const nextCleanWord = nextWord.text.toLowerCase().trim();
            let nextWordStart = lowerText.indexOf(nextCleanWord, suffixEnd);

            // Limit lookahead to prevent swallowing too much text if a word is missing
            const maxLookahead = 50;
            if (nextWordStart !== -1 && (nextWordStart - suffixEnd) < maxLookahead) {
                wordWithSuffix = fullText.substring(wordStart, nextWordStart);
                currentPos = nextWordStart;
            } else {
                // Next word not found or too far, just take the word and any immediately following punctuation
                let searchRange = fullText.substring(wordStart, wordStart + cleanWord.length + 5);
                let puncMatch = searchRange.match(/^.*?[.,!?;:\s]*/);
                wordWithSuffix = puncMatch ? puncMatch[0] : fullText.substring(wordStart, wordStart + cleanWord.length);
                if (!wordWithSuffix.endsWith(' ')) wordWithSuffix += ' ';
                currentPos = wordStart + wordWithSuffix.length;
            }
        } else {
            // Last word - take everything remaining
            wordWithSuffix = fullText.substring(wordStart);
            currentPos = fullText.length;
        }

        result.push({
            ...word,
            punctuated: wordWithSuffix
        });
    }
    return result;
};

/**
 * Groups punctuated words into speaker turns based on Diorization segments
 */
UI.mergeSpeechAndSpeakers = (punctuatedWords, diarizeSegments) => {
    let turns = [];
    let currentTurn = null;

    punctuatedWords.forEach(word => {
        const midpoint = (word.start_time + word.end_time) / 2;

        // Find owner speaker
        const segment = diarizeSegments.find(s => midpoint >= s.start && midpoint <= s.end)
            || diarizeSegments.find(s => word.start_time >= s.start && word.start_time <= s.end)
            || { speaker: "Unknown" };

        if (!currentTurn || currentTurn.speaker !== segment.speaker) {
            currentTurn = {
                speaker: segment.speaker,
                text: word.punctuated,
                start: word.start_time,
                end: word.end_time
            };
            turns.push(currentTurn);
        } else {
            currentTurn.text += word.punctuated;
            currentTurn.end = word.end_time;
        }
    });

    return turns;
};

UI.renderAnalysisChat = (turns) => {
    const chat = UI.elements.analysisResultChat;
    const audio = UI.elements.analysisPreview;
    const bubbles = [];

    turns.forEach(turn => {
        const bubble = document.createElement('div');
        bubble.className = 'card analysis-bubble';
        bubble.style.padding = '15px';
        bubble.style.borderRadius = '12px';
        bubble.style.marginBottom = '10px';
        bubble.style.cursor = 'pointer';
        bubble.style.transition = 'all 0.2s ease';
        bubble.style.background = 'rgba(255,255,255,0.03)';
        bubble.style.borderLeft = `4px solid ${UI.getSpeakerColor(turn.speaker)}`;

        const header = document.createElement('div');
        header.style.display = 'flex';
        header.style.justifyContent = 'space-between';
        header.style.marginBottom = '8px';
        header.style.fontSize = '0.85rem';
        header.style.fontWeight = 'bold';
        header.style.color = 'var(--text-secondary)';

        const name = document.createElement('span');
        name.textContent = turn.speaker;
        name.style.color = UI.getSpeakerColor(turn.speaker);

        const time = document.createElement('span');
        time.textContent = `${turn.start.toFixed(1)}s - ${turn.end.toFixed(1)}s`;

        header.appendChild(name);
        header.appendChild(time);

        const body = document.createElement('div');
        body.style.lineHeight = '1.6';
        body.textContent = turn.text.trim();

        bubble.appendChild(header);
        bubble.appendChild(body);

        bubble.onclick = () => {
            if (audio.src) {
                audio.currentTime = turn.start;
                // Play just this segment
                audio.playTargetEnd = turn.end;
                audio.play();
            }
        };

        bubble.onmouseenter = () => {
            if (!bubble.classList.contains('active-segment')) {
                bubble.style.background = 'rgba(255,255,255,0.06)';
            }
        };
        bubble.onmouseleave = () => {
            if (!bubble.classList.contains('active-segment')) {
                bubble.style.background = 'rgba(255,255,255,0.03)';
            }
        };

        chat.appendChild(bubble);
        bubbles.push({ el: bubble, start: turn.start, end: turn.end });
    });

    audio.ontimeupdate = () => {
        const currentTime = audio.currentTime;

        bubbles.forEach(item => {
            const isActive = currentTime >= item.start && currentTime <= item.end;
            if (isActive) {
                item.el.classList.add('active-segment');
                item.el.style.background = 'rgba(59, 130, 246, 0.15)';
                item.el.style.borderColor = 'var(--accent)';
                // Optional: scroll into view
                // item.el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                item.el.classList.remove('active-segment');
                item.el.style.background = 'rgba(255,255,255,0.03)';
                item.el.style.borderColor = 'transparent';
            }
        });

        if (audio.playTargetEnd && currentTime >= audio.playTargetEnd) {
            audio.pause();
            audio.playTargetEnd = null;
        }
    };
};

// Helper for persistent speaker colors
UI.speakerColors = {};
UI.getSpeakerColor = (speaker) => {
    if (UI.speakerColors[speaker]) return UI.speakerColors[speaker];
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
    const color = colors[Object.keys(UI.speakerColors).length % colors.length];
    UI.speakerColors[speaker] = color;
    return color;
};
