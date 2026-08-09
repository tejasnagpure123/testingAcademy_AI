document.addEventListener('DOMContentLoaded', () => {
    // Tab Switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.dataset.tab === 'explainer') return; // Handled inline as window.open
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
        });
    });

    // Pipeline UI updates
    const stages = ['ingest', 'query', 'search', 'rerank', 'generate'];
    function updateStage(stageName, statusText, isActive = false) {
        const el = document.getElementById(`stage-${stageName}`);
        if (el) {
            const statusEl = el.querySelector('.status-text');
            if (statusEl) statusEl.textContent = statusText;
            
            stages.forEach(s => document.getElementById(`stage-${s}`).classList.remove('active'));
            if (isActive) {
                el.classList.add('active');
            }
        }
    }

    // Upload & Ingest
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const ingestLog = document.getElementById('ingest-log');
    const ingestProgress = document.getElementById('ingest-progress');

    uploadBtn.addEventListener('click', async () => {
        if (!fileInput.files.length) {
            alert('Please select a file first.');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading...';
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (response.ok) {
                // Start SSE for ingestion
                ingestProgress.style.display = 'block';
                ingestLog.innerHTML = 'Starting ingestion...\n';
                updateStage('ingest', 'Processing chunks...', true);
                
                const eventSource = new EventSource('/ingest?filename=' + encodeURIComponent(data.filename));
                
                eventSource.onmessage = function(event) {
                    const parsed = JSON.parse(event.data);
                    ingestLog.innerHTML += `${parsed.message}\n`;
                    ingestLog.scrollTop = ingestLog.scrollHeight;
                    
                    if (parsed.status === 'complete') {
                        eventSource.close();
                        updateStage('ingest', 'Complete', false);
                        uploadBtn.disabled = false;
                        uploadBtn.textContent = 'Start Ingestion';
                        alert('Ingestion Complete!');
                    }
                };
                
                eventSource.onerror = function() {
                    ingestLog.innerHTML += `\nError during ingestion.\n`;
                    eventSource.close();
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Start Ingestion';
                };
            } else {
                alert(data.error || 'Upload failed');
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Start Ingestion';
            }
        } catch (error) {
            console.error(error);
            alert('Error connecting to backend');
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Start Ingestion';
        }
    });

    // Load Chunks
    const loadChunksBtn = document.getElementById('load-chunks-btn');
    const chunksList = document.getElementById('chunks-list');
    
    loadChunksBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/chunks');
            const data = await response.json();
            
            chunksList.innerHTML = '';
            
            if (!data.chunks || data.chunks.length === 0) {
                chunksList.innerHTML = '<p>No chunks found.</p>';
                return;
            }
            
            data.chunks.forEach(chunk => {
                const card = document.createElement('div');
                card.className = 'chunk-card';
                card.innerHTML = `
                    <h4>Chunk ID: ${chunk.id.substring(0,8)}...</h4>
                    <p><strong>Score:</strong> ${chunk.score || 'N/A'}</p>
                    <div class="details-block">
                        ${chunk.payload?.text || 'No text payload'}
                    </div>
                `;
                chunksList.appendChild(card);
            });
            
        } catch(error) {
            chunksList.innerHTML = '<p>Error loading chunks.</p>';
        }
    });

    // Chat
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    function appendMessage(text, role) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        msgDiv.innerHTML = `<p>${text.replace(/\n/g, '<br>')}</p>`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgDiv;
    }

    chatSendBtn.addEventListener('click', async () => {
        const query = chatInput.value.trim();
        if (!query) return;

        appendMessage(query, 'user');
        chatInput.value = '';
        
        updateStage('query', 'Rewriting query...', true);
        
        try {
            // Using SSE for chat to get stage updates
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            
            let assistantMsg = appendMessage('...', 'assistant');
            let fullResponse = '';
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunkStr = decoder.decode(value, { stream: true });
                const lines = chunkStr.split('\n');
                
                for (let line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            
                            if (data.stage) {
                                updateStage(data.stage, data.statusText || 'Processing...', true);
                            }
                            
                            if (data.text) {
                                fullResponse += data.text;
                                assistantMsg.innerHTML = `<p>${fullResponse.replace(/\n/g, '<br>')}</p>`;
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                        } catch(e) {}
                    }
                }
            }
            
            stages.forEach(s => document.getElementById(`stage-${s}`).classList.remove('active'));
            
        } catch(e) {
            appendMessage('Error processing request.', 'assistant');
            stages.forEach(s => document.getElementById(`stage-${s}`).classList.remove('active'));
        }
    });
});
