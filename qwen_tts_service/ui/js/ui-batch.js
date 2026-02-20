// ui-batch.js - Batch and Queue logic
UI.addToBatch = async (mode) => {
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
            const file = UI.currentASRFile;
            if (!file) return alert("Please select a file first.");

            const lang = UI.elements.asrLanguage.value;
            const timestamps = UI.elements.asrTimestamps.checked;

            btn.textContent = 'Uploading...';
            const res = await API.uploadFile(file);
            
            UI.batchQueue.push({
                id: Utils.generateId(),
                mode: 'asr',
                text: file.name,
                file_id: res.file_id,
                lang,
                timestamps
            });
        } else if (mode === 'diarize') {
            const fileInput = UI.elements.diarizeFile;
            const file = UI.currentDiarizeFile || (fileInput.files && fileInput.files[0]);
            if (!file) return alert("Please select an audio file first.");

            const numS = UI.elements.diarizeNumSpeakers.value;
            const minS = UI.elements.diarizeMinSpeakers.value;
            const maxS = UI.elements.diarizeMaxSpeakers.value;

            btn.textContent = 'Uploading...';
            const uploadRes = await API.uploadFile(file);

            UI.batchQueue.push({
                id: Utils.generateId(),
                mode: 'diarize',
                text: file.name,
                file_id: uploadRes.file_id,
                numSpeakers: numS ? parseInt(numS) : null,
                minSpeakers: minS ? parseInt(minS) : null,
                maxSpeakers: maxS ? parseInt(maxS) : null
            });
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
};

UI.updateBatchUI = () => {
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
        el.innerHTML = '<div class="batch-item-content" style="display: flex; align-items: center; justify-content: space-between; width: 100%;">' +
            '<div class="q-info">' +
            '<span class="q-type">' + item.mode.replace('-', ' ') + '</span>' +
            '<span class="q-text">' + item.text + '</span>' +
            '<span class="q-status badge status-queued">queued</span>' +
            '</div>' +
            '<button class="btn-delete" onclick="UI.removeFromBatch(' + index + ')">' +
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>' +
            '</button>' +
            '</div>';
        list.appendChild(el);
    });
};

UI.removeFromBatch = (index) => {
    UI.batchQueue.splice(index, 1);
    UI.updateBatchUI();
};

UI.runBatch = async () => {
    if (UI.batchQueue.length === 0) return;

    const btn = document.getElementById('btn-run-batch');
    const clearBtn = document.getElementById('btn-clear-queue');
    btn.disabled = true;
    clearBtn.disabled = true;
    btn.textContent = 'Submitting...';

    try {
        const queueItems = UI.batchQueue.map(item => {
            let operation = item.mode;
            if (item.mode === 'design') operation = 'voice_design';
            if (item.mode === 'custom') operation = 'custom_voice';
            if (item.mode === 'clone') {
                operation = item.enhanced ? 'voice_clone_enhanced' : 'voice_clone';
            }
            if (item.mode === 'asr') operation = 'transcribe';
            if (item.mode === 'diarize') operation = 'diarize';

            return {
                text: item.text,
                operation: operation,
                ref_audio: item.file_id || null,
                ref_text: item.refText || null,
                instruct: item.instruct || null,
                speaker: item.speaker || null,
                language: item.lang || 'auto',
                temperature: item.temp || 0.3,
                return_timestamps: item.timestamps || false,
                custom_id: item.id
            };
        });

        const response = await API.submitBatchToQueue(queueItems, `Web UI Batch ${new Date().toLocaleTimeString()} `);
        const batchId = response.batch_id;

        console.log("Batch submitted:", batchId);
        btn.textContent = 'Processing...';

        UI.pollQueueStatus(batchId);

    } catch (error) {
        alert("Batch Error: " + error.message);
        btn.disabled = false;
        clearBtn.disabled = false;
        btn.textContent = 'Run Batch';
    }
};

UI.pollQueueStatus = async (batchId) => {
    const btn = document.getElementById('btn-run-batch');
    const clearBtn = document.getElementById('btn-clear-queue');

    const poll = async () => {
        try {
            const statusRes = await API.getQueueStatus(batchId);
            UI.updateQueueProgress(statusRes);

            if (statusRes.status === 'completed' || statusRes.status === 'partial' || statusRes.status === 'error') {
                UI.handleQueueCompletion(batchId);
                btn.disabled = false;
                clearBtn.disabled = false;
                btn.textContent = 'Run Batch';
                return;
            }
            setTimeout(poll, 2000);
        } catch (error) {
            console.error("Polling error:", error);
            btn.disabled = false;
            clearBtn.disabled = false;
            btn.textContent = 'Run Batch';
        }
    };
    poll();
};

UI.updateQueueProgress = (statusResponse) => {
    const count = document.getElementById('queue-count');
    count.textContent = `${statusResponse.completed}/${statusResponse.total}`;

    statusResponse.items.forEach(item => {
        const el = document.querySelector(`.queue-item[data-id="${item.custom_id}"]`);
        if (el) {
            el.setAttribute('data-status', item.status);
            const statusBadge = el.querySelector('.q-status');
            if (statusBadge) {
                statusBadge.textContent = item.status;
                statusBadge.className = `q-status badge status-${item.status}`;
            }
            if (item.status === 'processing') {
                el.classList.add('is-processing');
            } else {
                el.classList.remove('is-processing');
            }
        }
    });
};

UI.handleQueueCompletion = async (batchId) => {
    try {
        const results = await API.getQueueResults(batchId);
        results.items.forEach(item => {
            if (item.status === 'done' && item.url) {
                const originalItem = UI.batchQueue.find(i => i.id === item.custom_id);
                const mode = originalItem ? originalItem.mode : 'unknown';
                const text = originalItem ? originalItem.text : (item.custom_id || "Queued Text");
                UI.addToHistory(mode, item.url, 0, text);
            } else if (item.status === 'error') {
                console.error(`Item ${item.item_id} failed: ${item.error}`);
            }
        });

        setTimeout(() => {
            UI.batchQueue = [];
            UI.updateBatchUI();
        }, 3000);

    } catch (error) {
        console.error("Error handling queue completion:", error);
    }
};
