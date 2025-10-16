document.addEventListener('DOMContentLoaded', () => {
    console.log("Chat JS Loaded"); // Debugging line to ensure script runs

    const chatForm = document.getElementById('chat-form');
    const topicInput = document.getElementById('topicInput');
    const askButton = document.getElementById('askButton');
    const chatArea = document.getElementById('chat-area');
    const suggestionsWrapper = document.getElementById('prompt-suggestions-wrapper');
    const suggestionsContainer = document.getElementById('prompt-suggestions');
    
    // SAFETY CHECK: Handle missing Showdown library gracefully
    let converter;
    try {
        if (typeof showdown !== 'undefined') {
            converter = new showdown.Converter();
        } else {
            console.warn("Showdown library not found. Markdown rendering disabled.");
            converter = { makeHtml: (text) => text }; // Fallback to plain text
        }
    } catch (e) {
        console.error("Error initializing converter:", e);
        converter = { makeHtml: (text) => text };
    }

    if (topicInput) {
        topicInput.addEventListener('input', () => {
            topicInput.style.height = 'auto';
            topicInput.style.height = `${topicInput.scrollHeight}px`;
        });
        
        // Prevent "Enter" key from submitting form blindly
        topicInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
    }

    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault(); // CRITICAL: Stop page reload
            askQuestion();
        });
    } else {
        console.error("Chat form element not found!");
    }
    
    // EXTRA SAFETY: Catch button clicks directly
    if (askButton) {
        askButton.addEventListener('click', (e) => {
            e.preventDefault(); // CRITICAL: Stop page reload
            askQuestion();
        });
    }

    async function askQuestion(questionText = null) {
        const topic = questionText || (topicInput ? topicInput.value.trim() : "");
        
        if (!topic) return;

        if (topicInput) {
            topicInput.value = '';
            topicInput.style.height = 'auto';
        }
        
        if (suggestionsWrapper) suggestionsWrapper.style.display = 'none';
        if (suggestionsContainer) suggestionsContainer.innerHTML = '';

        displayUserMessage(topic);
        const loaderId = 'loader-' + Date.now();
        displayLoader(loaderId);
        
        if (askButton) askButton.disabled = true;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic })
            });
            
            const loaderEl = document.getElementById(loaderId);
            if (loaderEl) loaderEl.remove();
            
            // Check for network errors before parsing JSON
            if (!response.ok) {
                 // Try to read error text if json fails
                 const text = await response.text();
                 throw new Error(`Server Error: ${response.status} - ${text}`);
            }

            const data = await response.json();

            if (data.status === 'error') {
                throw new Error(data.answer || data.error || 'An unknown error occurred.');
            }
            
            displayAiResponse(data);

        } catch (error) {
            console.error('Fetch Error:', error);
            const loaderEl = document.getElementById(loaderId);
            if (loaderEl) loaderEl.remove();
            displayErrorMessage(error.message);
        } finally {
            if (askButton) askButton.disabled = false;
        }
    }

    function displayUserMessage(message) {
        if (!chatArea) return;
        const userMessageHtml = `<div class="message-wrapper"><div class="message-header user-header">You</div><div class="message-content user">${message.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div></div>`;
        chatArea.insertAdjacentHTML('beforeend', userMessageHtml);
        scrollToBottom();
    }
    
    function displayLoader(id) {
        if (!chatArea) return;
        const loaderHtml = `<div class="message-wrapper" id="${id}"><div class="message-header ai-header"><i class="fas fa-robot"></i> AI Team</div><div class="loader-wrapper"><i class="fas fa-spinner fa-spin"></i> Thinking...</div></div>`;
        chatArea.insertAdjacentHTML('beforeend', loaderHtml);
        scrollToBottom();
    }

    function displayErrorMessage(errorMsg) {
        if (!chatArea) return;
        const errorHtml = `<div class="message-wrapper"><div class="message-header ai-header"><i class="fas fa-robot"></i> AI Team</div><div class="ai-response"><p style="color:#e57373;">Error: ${errorMsg}</p></div></div>`;
        chatArea.insertAdjacentHTML('beforeend', errorHtml);
        scrollToBottom();
    }

    function displayAiResponse(data) {
        if (!chatArea) return;
        const thinkingHtml = (data.chain_of_thought) ? `<div class="thinking-dropdown"><details><summary>Show thinking <i class="fas fa-chevron-down icon"></i></summary><div class="thinking-dropdown-content">${data.chain_of_thought}</div></details></div>` : '';
        
        const sourcesHtml = (data.sources && data.sources.length > 0) ? `<div class="sources-quote">${data.sources.map(s => `<p>“${s}”</p>`).join('')}</div>` : '';

        const answerHtml = data.answer ? `<div class="answer">${converter.makeHtml(data.answer)}</div>` : '<div class="answer"><p>No answer provided.</p></div>';

        let webSourcesHtml = '';
        if (data.web_sources && data.web_sources.length > 0) {
            webSourcesHtml = `<div class="web-sources-container"><div class="web-sources-header"><i class="fas fa-globe"></i> Sources</div><div class="web-sources-grid">${data.web_sources.map(ws => `<a href="${ws.url}" target="_blank" class="web-source-card">${ws.title}</a>`).join('')}</div></div>`;
        }

        const responseHtml = `<div class="message-wrapper"><div class="message-header ai-header"><i class="fas fa-robot"></i> AI Team</div><div class="ai-response">${thinkingHtml}${sourcesHtml}${answerHtml}${webSourcesHtml}</div></div>`;
        chatArea.insertAdjacentHTML('beforeend', responseHtml);

        if (data.follow_up_questions && data.follow_up_questions.length > 0 && suggestionsWrapper && suggestionsContainer) {
            suggestionsWrapper.style.display = 'block';
            suggestionsContainer.innerHTML = '';
            data.follow_up_questions.forEach(q => {
                const card = document.createElement('div');
                card.className = 'suggestion-card';
                card.textContent = q;
                card.onclick = () => askQuestion(q);
                suggestionsContainer.appendChild(card);
            });
        }
        
        scrollToBottom();
    }

    function scrollToBottom() {
        if (chatArea) chatArea.scrollTop = chatArea.scrollHeight;
    }
});