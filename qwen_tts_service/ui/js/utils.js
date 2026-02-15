// Utility functions

const Utils = {
    // Generate a unique ID for history items
    generateId: () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    // Format duration in mm:ss
    formatTime: (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const secondsPart = Math.floor(seconds % 60);
        return `${minutes}:${secondsPart < 10 ? '0' : ''}${secondsPart}`;
    },

    // Save to local storage
    saveToStorage: (key, value) => {
        localStorage.setItem(key, JSON.stringify(value));
    },

    // Get from local storage
    getFromStorage: (key, defaultVal = null) => {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultVal;
    },

    // Base64 to Blob
    base64ToBlob: (base64, mimeType = 'audio/wav') => {
        const byteString = atob(base64);
        const ab = new ArrayBuffer(byteString.length);
        const ia = new Uint8Array(ab);
        for (let i = 0; i < byteString.length; i++) {
            ia[i] = byteString.charCodeAt(i);
        }
        return new Blob([ab], { type: mimeType });
    }
};
