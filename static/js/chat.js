document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const topicInput = document.getElementById('topicInput');
    const askButton = document.getElementById('askButton');
    const chatArea = document.getElementById('chat-area');
    const suggestionsWrapper = document.getElementById('prompt-suggestions-wrapper');
    const suggestionsContainer = document.getElementById('prompt-suggestions');
    
    const converter = new showdown.Converter();

    topicInput.addEventListener('input', () => {
        topicInput.style.height = 'auto';
        topicInput.style.height = `${topicInput.scrollHeight}px`;
    });

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        askQuestion();
    });

    async function askQuestion(questionText = null) {
        const topic = questionText || topicInput.value.trim();
        if (!topic) return;

        topicInput.value = '';
        topicInput.style.height = 'auto';
        suggestionsWrapper.style.display = 'none';
        suggestionsContainer.innerHTML = '';

        displayUserMessage(topic);
        const loaderId = 'loader-' + Date.now();
        displayLoader(loaderId);
        askButton.disabled = true;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic })
            });
            
            document.getElementById(loaderId)?.remove();
            
            const data = await response.json();

            if (!response.ok || data.status === 'error') {
                throw new Error(data.answer || data.error || 'An unknown error occurred.');
            }
            
            displayAiResponse(data);

        } catch (error) {
            console.error('Error:', error);
            displayErrorMessage(error.message);
        } finally {
            askButton.disabled = false;
        }
    }

    function displayUserMessage(message) {
        const userMessageHtml = `<div class="message-wrapper"><div class="message-header user-header">You</div><div class="message-content user">${message.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div></div>`;
        chatArea.insertAdjacentHTML('beforeend', userMessageHtml);
        scrollToBottom();
    }
    
    function displayLoader(id) {
        const loaderHtml = `<div class="message-wrapper" id="${id}"><div class="message-header ai-header"><i class="fas fa-robot"></i> AI Team</div><div class="loader-wrapper"><i class="fas fa-spinner fa-spin"></i> Thinking...</div></div>`;
        chatArea.insertAdjacentHTML('beforeend', loaderHtml);
        scrollToBottom();
    }

    function displayErrorMessage(errorMsg) {
        const errorHtml = `<div class="message-wrapper"><div class="message-header ai-header"><i class="fas fa-robot"></i> AI Team</div><div class="ai-response"><p style="color:#e57373;">Error: ${errorMsg}</p></div></div>`;
        chatArea.insertAdjacentHTML('beforeend', errorHtml);
        scrollToBottom();
    }

    function displayAiResponse(data) {
        const thinkingHtml = (data.chain_of_thought) ? `<div class="thinking-dropdown"><details><summary>Show thinking <i class="fas fa-chevron-down icon"></i></summary><div class="thinking-dropdown-content">${data.chain_of_thought}</div></details></div>` : '';
        
        // UPDATED: Use <p> tags instead of <ul><li> for the quotes to remove bullet points
        const sourcesHtml = (data.sources && data.sources.length > 0) ? `<div class="sources-quote">${data.sources.map(s => `<p>“${s}”</p>`).join('')}</div>` : '';

        const answerHtml = data.answer ? `<div class="answer">${converter.makeHtml(data.answer)}</div>` : '<div class="answer"><p>No answer provided.</p></div>';

        let webSourcesHtml = '';
        if (data.web_sources && data.web_sources.length > 0) {
            webSourcesHtml = `<div class="web-sources-container"><div class="web-sources-header"><i class="fas fa-globe"></i> Sources</div><div class="web-sources-grid">${data.web_sources.map(ws => `<a href="${ws.url}" target="_blank" class="web-source-card">${ws.title}</a>`).join('')}</div></div>`;
        }

        const responseHtml = `<div class="message-wrapper"><div class="message-header ai-header"><i class="fas fa-robot"></i> AI Team</div><div class="ai-response">${thinkingHtml}${sourcesHtml}${answerHtml}${webSourcesHtml}</div></div>`;
        chatArea.insertAdjacentHTML('beforeend', responseHtml);

        if (data.follow_up_questions && data.follow_up_questions.length > 0) {
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
        chatArea.scrollTop = chatArea.scrollHeight;
    }
});