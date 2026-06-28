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

    // Auth Elements
    const userDisplay = document.getElementById('user-display');
    const loginLink = document.getElementById('login-link');
    const displayUsername = document.getElementById('display-username');
    const displayTokens = document.getElementById('display-tokens');
    const adminLink = document.getElementById('admin-link');
    const userAvatar = document.getElementById('user-avatar');

    const API_URL = ''; // Local Backend
    let translateTimeout;
    let currentUser = JSON.parse(localStorage.getItem('user'));

    // --- Auth Logic ---
    function updateAuthUI() {
        if (currentUser && currentUser.username) {
            userDisplay.classList.remove('hidden');
            userDisplay.style.display = 'flex';
            loginLink.classList.add('hidden');
            loginLink.style.display = 'none';
            
            displayUsername.innerText = `Hello, ${currentUser.username}`;
            displayTokens.innerText = (currentUser.tokens || 0).toLocaleString();
            
            const avatar = document.getElementById('user-avatar');
            if (avatar) {
                avatar.src = `assets/img/default_avatar.svg`;
            }
            
            if (currentUser.role === 'admin') {
                adminLink.classList.remove('hidden');
                adminLink.style.display = 'flex';
            } else {
                adminLink.classList.add('hidden');
                adminLink.style.display = 'none';
            }
        } else {
            userDisplay.classList.add('hidden');
            userDisplay.style.display = 'none';
            loginLink.classList.remove('hidden');
            loginLink.style.display = 'inline-block';
        }
    }

    window.logout = () => {
        localStorage.removeItem('user');
        window.location.reload();
    };

    async function refreshUserInfo() {
        if (!currentUser) return;
        try {
            const res = await fetch(`${API_URL}/user-info/${currentUser.id}`);
            if (res.ok) {
                const data = await res.json();
                currentUser = data;
                localStorage.setItem('user', JSON.stringify(data));
                updateAuthUI();
            }
        } catch (e) { console.error("Refresh info failed", e); }
    }

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
                    target: targetLangSelect.value,
                    user_id: currentUser ? currentUser.id : 1
                })
            });

            const data = await response.json();
            if (response.ok) {
                resultText.textContent = data.translated;
                refreshUserInfo();
            } else {
                if (response.status === 402) {
                    resultText.textContent = "Insufficient tokens. Please contact Admin.";
                } else {
                    resultText.textContent = data.detail || 'Translation failed';
                }
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
        }, 400);
    });

    // --- History ---
    async function loadHistory(search = "") {
        try {
            const userIdParam = currentUser ? `&user_id=${currentUser.id}` : '';
            const response = await fetch(`${API_URL}/history?limit=10&q=${encodeURIComponent(search)}${userIdParam}`);
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
            } else {
                historyContainer.innerHTML = '<p class="text-gray-600 text-xs uppercase tracking-widest col-span-full text-center py-10">No recent sessions found</p>';
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
        formData.append('user_id', currentUser ? currentUser.id : 1);

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
                refreshUserInfo();
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

    // --- Mic/STT Logic ---
    // --- Mic/STT Logic (Real-Time WebSocket) ---
    let audioContext;
    let mediaStream;
    let audioProcessor;
    let analyser;
    let animationId;
    let ws;
    let isRecording = false;

    async function startRecording() {
        try {
            micBtn.classList.add('bg-red-500/20', 'text-red-500');
            showToast('Connecting...');

            // Initialize audio context to get the true hardware sample rate before opening WS
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const actualSampleRate = audioContext.sampleRate;

            // Determine WebSocket URL
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host; 
            const wsUrl = `${protocol}//${host}/ws/realtime-translate`;

            ws = new WebSocket(wsUrl);

            ws.onopen = async () => {
                showToast('Connected. Waiting for STT model...');
                
                // Send initial configuration
                ws.send(JSON.stringify({
                    source: sourceLangSelect.value,
                    target: targetLangSelect.value,
                    user_id: currentUser ? currentUser.id : 1,
                    sample_rate: actualSampleRate
                }));
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'status') {
                    if (data.message === 'Ready') {
                        showToast('Listening... Speak now.');
                        initAudioCapture();
                    } else {
                        showToast(data.message);
                    }
                } else if (data.type === 'partial') {
                    // Show partial text in source box wrapped in brackets to indicate it's real-time
                    if (data.source_text) {
                        const currentFinalSource = sourceText.value.replace(/\s*\[.*\]$/, '').trim(); 
                        sourceText.value = currentFinalSource ? `${currentFinalSource} [${data.source_text}]` : `[${data.source_text}]`;
                    }
                } else if (data.type === 'result') {
                    const currentFinalSource = sourceText.value.replace(/\s*\[.*\]$/, '').trim();
                    sourceText.value = (currentFinalSource ? currentFinalSource + " " : "") + data.source_text;
                    
                    const currentResult = resultText.textContent;
                    resultText.textContent = (currentResult ? currentResult + " " : "") + data.translated;
                    
                    updateCharCount();
                    // loadHistory(); // Don't constantly reload history to avoid flickering
                } else if (data.type === 'error') {
                    showToast(data.message);
                    stopRecording();
                }
            };

            ws.onerror = (err) => {
                console.error("WebSocket error", err);
                showToast("Connection error");
                stopRecording();
            };

            ws.onclose = () => {
                stopRecording();
            };

        } catch (err) {
            console.error("Error setting up WebSocket:", err);
            showToast('Failed to start real-time translation');
            stopRecording();
        }
    }

    async function initAudioCapture() {
        try {
            const constraints = {
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            };
            mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
            
            // Audio context is already initialized in startRecording
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
            }
            const source = audioContext.createMediaStreamSource(mediaStream);
            
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            source.connect(analyser);

            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            const micVisualizer = document.getElementById('mic-visualizer');

            function updateVisualizer() {
                if (!isRecording) {
                    if (micVisualizer) micVisualizer.style.transform = 'scale(0)';
                    return;
                }
                analyser.getByteFrequencyData(dataArray);
                let sum = 0;
                for(let i = 0; i < bufferLength; i++) {
                    sum += dataArray[i];
                }
                let avg = sum / bufferLength;
                let scale = 0.5 + (avg / 256) * 1.5; 
                if (micVisualizer) {
                    micVisualizer.style.transform = `scale(${scale})`;
                }
                animationId = requestAnimationFrame(updateVisualizer);
            }
            updateVisualizer();

            // Create a ScriptProcessorNode with a buffer size of 4096 and a single input/output channel
            audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);
            
            audioProcessor.onaudioprocess = (e) => {
                if (!isRecording || ws.readyState !== WebSocket.OPEN) return;
                
                // Get the input buffer (Float32Array)
                const inputData = e.inputBuffer.getChannelData(0);
                
                // Convert Float32 to Int16 (PCM)
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    let s = Math.max(-1, Math.min(1, inputData[i]));
                    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                
                // Send raw PCM bytes
                ws.send(pcmData.buffer);
            };
            
            source.connect(audioProcessor);
            audioProcessor.connect(audioContext.destination);
            
            isRecording = true;
        } catch (err) {
            console.error("Mic access denied or failed", err);
            showToast("Microphone access denied");
            stopRecording();
        }
    }

    function stopRecording() {
        isRecording = false;
        micBtn.classList.remove('bg-red-500/20', 'text-red-500');
        
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
        const micVisualizer = document.getElementById('mic-visualizer');
        if (micVisualizer) {
            micVisualizer.style.transform = 'scale(0)';
        }
        
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
        if (audioProcessor) {
            audioProcessor.disconnect();
            audioProcessor = null;
        }
        if (audioContext) {
            audioContext.close();
            audioContext = null;
        }
        if (analyser) {
            analyser.disconnect();
            analyser = null;
        }
        if (mediaStream) {
            mediaStream.getTracks().forEach(t => t.stop());
            mediaStream = null;
        }
        showToast('Stopped listening');
        loadHistory();
    }

    micBtn.onclick = () => {
        if (isRecording || (ws && ws.readyState === WebSocket.OPEN)) {
            stopRecording();
        } else {
            startRecording();
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

    const downloadHistoryBtn = document.getElementById('download-history');
    if (downloadHistoryBtn) {
        downloadHistoryBtn.onclick = async () => {
            if (!currentUser) {
                showToast('Login to download history');
                return;
            }
            try {
                const response = await fetch(`${API_URL}/history?limit=100&user_id=${currentUser.id}`);
                const data = await response.json();
                if (data.history && data.history.length > 0) {
                    const rows = [["Source Language", "Target Language", "Source Text", "Translated Text", "Timestamp"]];
                    data.history.forEach(item => {
                        rows.push([
                            item.source_lang,
                            item.target_lang,
                            `"${item.source_text.replace(/"/g, '""')}"`,
                            `"${item.translated_text.replace(/"/g, '""')}"`,
                            item.timestamp
                        ]);
                    });
                    
                    const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
                    const encodedUri = encodeURI(csvContent);
                    const link = document.createElement("a");
                    link.setAttribute("href", encodedUri);
                    link.setAttribute("download", `translation_history_${currentUser.username}.csv`);
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    showToast('History Exported');
                } else {
                    showToast('No history found to download');
                }
            } catch (e) {
                showToast('Download failed');
            }
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
    updateAuthUI();
    loadHistory();
    checkStatus();
    setInterval(checkStatus, 5000);

    // Global functions for HTML onclick
    window.toggleSettings = () => {
        if (!currentUser) {
            showToast('Login to access settings');
            return;
        }
        const modal = document.getElementById('settings-modal');
        modal.classList.toggle('hidden');
        if (!modal.classList.contains('hidden')) {
            document.getElementById('settings-email').value = currentUser.email || '';
            document.getElementById('settings-phone').value = currentUser.phone || '';
        }
    };

    window.saveSettings = async () => {
        const email = document.getElementById('settings-email').value;
        const phone = document.getElementById('settings-phone').value;

        try {
            const res = await fetch(`${API_URL}/user-update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: currentUser.id,
                    email,
                    phone
                })
            });

            if (res.ok) {
                showToast('Profile Updated');
                refreshUserInfo();
                window.toggleSettings();
            } else {
                showToast('Update failed');
            }
        } catch (e) {
            showToast('Network error');
        }
    };
});

