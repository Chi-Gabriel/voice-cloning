// ui-history.js - History and Playback logic
UI.updateTime = () => {
    const current = UI.wavesurfer.getCurrentTime();
    const duration = UI.wavesurfer.getDuration();
    UI.elements.timeDisplay.textContent = `${Utils.formatTime(current)} / ${Utils.formatTime(duration)}`;
};

UI.updatePlayButton = (isPlaying) => {
    const icon = isPlaying
        ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>'
        : '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>';
    UI.elements.playPauseBtn.innerHTML = icon;
};

UI.addToHistory = (mode, url, performance, text = "") => {
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
    el.innerHTML = '<div class="history-item-wrapper" style="display: flex; align-items: center; justify-content: space-between; width: 100%;">' +
        '<div class="history-info">' +
        '<strong>' + mode.toUpperCase().replace('-', ' ') + '</strong>' +
        '<span style="font-size:0.7em; color:var(--accent); margin-left:10px;">ID: ' + item.id + '</span>' +
        '<span>' + item.timestamp + '</span>' +
        '<span class="history-text" style="display:block; font-size:0.9em; margin-top:4px; color:var(--text-primary); font-style:italic; opacity:0.8;">' +
        '"' + text + '"' +
        '</span>' +
        '<span style="font-size: 0.8em; color: var(--accent); display: block; margin-top: 4px;">' +
        'generated in ' + (item.performance ? item.performance.toFixed(2) : 'N/A') + 's' +
        '</span>' +
        '<code style="font-size:0.7em; background:rgba(0,0,0,0.2); padding:2px 4px; border-radius:3px; display:inline-block; margin-top:4px;">' +
        url +
        '</code>' +
        '</div>' +
        '<div class="history-actions">' +
        (mode === 'asr'
            ? '<a href="' + url + '" target="_blank" style="color:var(--accent); text-decoration:none; font-size:0.9rem;">View JSON</a>'
            : '<button onclick="console.log(\'Playing: ' + url + '\'); UI.wavesurfer.load(\'' + url + '\'); UI.wavesurfer.play();">Play</button>'
        ) +
        '<a href="' + url + '" download="' + (mode === 'asr' ? 'transcript.json' : 'generated_' + item.id + '.wav') + '" style="color:var(--accent); text-decoration:none; font-size:0.9rem; margin-left:8px;">Download</a>' +
        '</div>' +
        '</div>';

    UI.elements.historyList.prepend(el);
};

UI.loadHistory = () => {
    UI.elements.historyList.innerHTML = '<div style="text-align:center; color:var(--text-secondary); padding:20px;">Generated audio will appear here.</div>';
};
