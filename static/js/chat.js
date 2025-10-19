document.addEventListener('DOMContentLoaded', () => {
    console.log("Chat JS Loaded"); 

    const chatForm = document.getElementById('chat-form');
    const topicInput = document.getElementById('topicInput');
    const askButton = document.getElementById('askButton');
    const chatArea = document.getElementById('chat-area');
    const suggestionsWrapper = document.getElementById('prompt-suggestions-wrapper');
    const suggestionsContainer = document.getElementById('prompt-suggestions');
    
    let converter;
    try {
        if (typeof showdown !== 'undefined') {
            converter = new showdown.Converter();
        } else {
            converter = { makeHtml: (text) => text };
        }
    } catch (e) {
        converter = { makeHtml: (text) => text };
    }

    if (topicInput) {
        topicInput.addEventListener('input', () => {
            topicInput.style.height = 'auto';
            topicInput.style.height = `${Math.min(topicInput.scrollHeight, 150)}px`;
        });
        
        topicInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
    }

    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault(); 
            askQuestion();
        });
    }
    
    if (askButton) {
        askButton.addEventListener('click', (e) => {
            e.preventDefault(); 
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
            
            if (!response.ok) {
                 const text = await response.text();
                 throw new Error(`Server Error: ${response.status}`);
            }

            const data = await response.json();

            if (data.status === 'error') {
                throw new Error(data.answer || 'An unknown error occurred.');
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
        // User message: Just the bubble, right aligned
        const html = `
        <div class="message-row user">
            <div class="message-bubble user">${message.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
        </div>`;
        chatArea.insertAdjacentHTML('beforeend', html);
        scrollToBottom();
    }
    
    function displayLoader(id) {
        if (!chatArea) return;
        // Loader: Avatar + Thinking text
        const html = `
        <div class="message-row ai" id="${id}">
            <div class="avatar ai"><i class="fas fa-robot"></i></div>
            <div class="message-bubble ai">
                <div class="loader-wrapper">
                    <i class="fas fa-spinner fa-spin"></i> Thinking...
                </div>
            </div>
        </div>`;
        chatArea.insertAdjacentHTML('beforeend', html);
        scrollToBottom();
    }

    function displayErrorMessage(errorMsg) {
        if (!chatArea) return;
        const html = `
        <div class="message-row ai">
            <div class="avatar ai"><i class="fas fa-exclamation-triangle" style="color: #e74c3c;"></i></div>
            <div class="message-bubble ai">
                <p style="color:#e57373;">Error: ${errorMsg}</p>
            </div>
        </div>`;
        chatArea.insertAdjacentHTML('beforeend', html);
        scrollToBottom();
    }

    function displayAiResponse(data) {
        if (!chatArea) return;
        
        let contentHtml = '';

        // 1. Thinking Process (Optional)
        if (data.chain_of_thought) {
            contentHtml += `
            <div class="thinking-dropdown">
                <details>
                    <summary>Thinking Process <i class="fas fa-chevron-down icon"></i></summary>
                    <div class="thinking-dropdown-content">${data.chain_of_thought}</div>
                </details>
            </div>`;
        }

        // 2. Religious Sources Quote (Optional)
        if (data.sources && data.sources.length > 0) {
            contentHtml += `<div class="sources-quote">${data.sources.map(s => `<p>“${s}”</p>`).join('')}</div>`;
        }

        // 3. The Main Answer
        const answerText = data.answer ? converter.makeHtml(data.answer) : '<p>No answer provided.</p>';
        contentHtml += `<div class="ai-answer">${answerText}</div>`;

        // 4. Web Sources (Optional)
        if (data.web_sources && data.web_sources.length > 0) {
            const sourcesList = data.web_sources.map(ws => 
                `<a href="${ws.url}" target="_blank" class="web-source-card">${ws.title}</a>`
            ).join('');
            
            contentHtml += `
            <div class="web-sources-container">
                <div class="web-sources-grid">${sourcesList}</div>
            </div>`;
        }

        const html = `
        <div class="message-row ai">
            <div class="avatar ai"><i class="fas fa-robot"></i></div>
            <div class="message-bubble ai">
                <div class="ai-response-content">${contentHtml}</div>
            </div>
        </div>`;

        chatArea.insertAdjacentHTML('beforeend', html);

        // 5. Follow-up Suggestions
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
        if (chatArea) {
            // Smooth scroll to bottom
            chatArea.scrollTo({ top: chatArea.scrollHeight, behavior: 'smooth' });
        }
    }
});