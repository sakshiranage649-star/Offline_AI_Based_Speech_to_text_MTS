document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();

    // Elements
    const sourceText = document.getElementById('source-text');
    const resultText = document.getElementById('result-text');
    const translateBtn = document.getElementById('translate-btn');
    const sourceLangSelect = document.getElementById('source-lang');
    const targetLangSelect = document.getElementById('target-lang');
    const swapBtn = document.getElementById('swap-langs');
    const swapBtnMobile = document.getElementById('swap-langs-mobile');
    const copyBtn = document.getElementById('copy-btn');
    const clearBtn = document.getElementById('clear-text');
    const micBtn = document.getElementById('mic-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const historyContainer = document.getElementById('history-container');
    const loader = document.getElementById('loader');
    const toast = document.getElementById('toast');
    const charCount = document.getElementById('char-count');
    const historySearch = document.getElementById('history-search');

    const API_URL = 'https://transly-fw3a.onrender.com'; // Render Backend
    let translateTimeout;

    // --- Translation ---
    async function translate() {
        const text = sourceText.value.trim();
        if (!text) return;

        loader.classList.remove('hidden');
        
        try {
            const response = await fetch(`${API_URL}/translate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text,
                    source: sourceLangSelect.value,
                    target: targetLangSelect.value
                })
            });

            const data = await response.json();
            if (response.ok) {
                resultText.textContent = data.translated;
            } else {
                resultText.textContent = data.detail || 'Translation failed';
            }
        } catch (error) {
            console.error(error);
        } finally {
            loader.classList.add('hidden');
            loadHistory();
        }
    }

    // Auto-translate smoothly when typing stops
    sourceText.addEventListener('input', () => {
        updateCharCount();
        clearTimeout(translateTimeout);
        translateTimeout = setTimeout(() => {
            if(sourceText.value.trim()) translate();
        }, 1200);
    });

    // --- History (User Friendly Cards) ---
    async function loadHistory(search = "") {
        try {
            const response = await fetch(`${API_URL}/history?limit=10&q=${encodeURIComponent(search)}`);
            const data = await response.json();
            
            if (data.history && data.history.length > 0) {
                historyContainer.innerHTML = '';
                data.history.forEach(item => {
                    const el = document.createElement('div');
                    el.className = 'history-item active:scale-95 transition-transform group';
                    el.innerHTML = `
                        <div class="flex items-center justify-between mb-4">
                            <div class="flex items-center gap-2">
                                <span class="bg-[#222a3d] text-[#bac3ff] text-[10px] font-black px-2 py-0.5 rounded-lg uppercase tracking-tighter">${item.source_lang}</span>
                                <i data-lucide="arrow-right" class="w-3 h-3 text-gray-500"></i>
                                <span class="bg-[#bac3ff]/10 text-[#bac3ff] text-[10px] font-black px-2 py-0.5 rounded-lg uppercase tracking-tighter">${item.target_lang}</span>
                            </div>
                            <span class="text-[10px] font-bold text-gray-700 uppercase tracking-widest">${new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                        </div>
                        <p class="text-sm text-gray-400 font-medium leading-relaxed line-clamp-3 group-hover:text-white transition-colors">${item.source_text}</p>
                    `;
                    el.onclick = () => {
                        sourceText.value = item.source_text;
                        resultText.textContent = item.translated_text;
                        sourceLangSelect.value = item.source_lang;
                        targetLangSelect.value = item.target_lang;
                        updateCharCount();
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    };
                    historyContainer.appendChild(el);
                });
                lucide.createIcons();
            }
        } catch (error) {
            console.error('Failed to load history', error);
        }
    }

    // --- File Upload ---
    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('source', sourceLangSelect.value);
        formData.append('target', targetLangSelect.value);

        loader.classList.remove('hidden');
        showToast(`Processing ${file.name}...`);

        try {
            const response = await fetch(`${API_URL}/upload-translate`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                sourceText.value = data.source_text;
                resultText.textContent = data.translated;
                showToast('Dialogue Refined');
                loadHistory();
                updateCharCount();
            } else {
                alert(data.detail || 'Extraction/Processing failed');
            }
        } catch (error) {
            alert('Upload error');
        } finally {
            loader.classList.add('hidden');
            fileInput.value = '';
        }
    };

    translateBtn.onclick = translate;

    function swap() {
        const s = sourceLangSelect.value;
        sourceLangSelect.value = targetLangSelect.value;
        targetLangSelect.value = s;
        const st = sourceText.value;
        const tt = resultText.textContent;
        sourceText.value = tt;
        resultText.textContent = st;
        updateCharCount();
        showToast('Dialogue Swapped');
        if(sourceText.value.trim()) translate();
    }

    if (swapBtn) swapBtn.onclick = swap;
    if (swapBtnMobile) swapBtnMobile.onclick = swap;

    copyBtn.onclick = () => {
        if (!resultText.textContent) return;
        navigator.clipboard.writeText(resultText.textContent);
        showToast('Dialogue Copied');
    };

    if (clearBtn) {
        clearBtn.onclick = () => {
            sourceText.value = '';
            resultText.textContent = '';
            updateCharCount();
        };
    }

    // --- Real-time Speech to Text (Mic) ---
    let recognition;
    let isRecording = false;

    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            if(finalTranscript) {
                sourceText.value = (sourceText.value + " " + finalTranscript).trim();
                updateCharCount();
                translate();
            }
        };

        recognition.onerror = (e) => {
            console.error('Speech recognition error', e);
            stopRecording();
        };
    }

    function stopRecording() {
        if(recognition && isRecording) {
            recognition.stop();
            isRecording = false;
            micBtn.classList.remove('bg-red-500/20', 'text-red-500');
            showToast('Microphone Disabled');
        }
    }

    micBtn.onclick = () => {
        if (!recognition) {
            showToast('Speech Recognition not supported in this browser');
            return;
        }

        if (isRecording) {
            stopRecording();
        } else {
            // Set language dynamically
            recognition.lang = sourceLangSelect.value;
            recognition.start();
            isRecording = true;
            micBtn.classList.add('bg-red-500/20', 'text-red-500');
            showToast('Listening... Speak now');
        }
    };

    uploadBtn.onclick = () => {
        fileInput.accept = '.pdf,.mp4,.avi,.mkv,.mov,.wav,.mp3';
        fileInput.click();
    };

    function showToast(msg) {
        toast.textContent = msg;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    function updateCharCount() {
        const text = sourceText.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        charCount.textContent = `${words} word${words !== 1 ? 's' : ''}`;
    }

    if (historySearch) {
        historySearch.oninput = (e) => {
            loadHistory(e.target.value.trim());
        };
    }

    // --- Status Polling ---
    async function checkStatus() {
        try {
            const response = await fetch(`${API_URL}/status`);
            const data = await response.json();
            
            const dbStatus = document.getElementById('db-status');
            const dbDot = document.getElementById('db-dot');
            const modelStatus = document.getElementById('model-status');
            const modelDot = document.getElementById('model-dot');

            dbStatus.textContent = data.database;
            dbDot.className = `w-1.5 h-1.5 rounded-full ${data.database === 'Connected' ? 'bg-green-500' : 'bg-red-500'}`;
            
            const transReady = data.translation_engine === 'Ready';
            modelStatus.innerHTML = `${transReady ? 'Ready' : 'Standby'} | STT: ${data.transcription_engine}`;
            modelDot.className = `w-1.5 h-1.5 rounded-full ${transReady ? 'bg-[#bac3ff]' : 'bg-yellow-500'}`;
        } catch (error) {
            console.error('Status check failed');
        }
    }

    // Initial checks
    loadHistory();
    checkStatus();
    setInterval(checkStatus, 5000);
});
