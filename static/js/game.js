document.addEventListener('DOMContentLoaded', () => {
    // --- MENU PAGE LOGIC ---
    const ayatGuesserCard = document.getElementById('ayatGuesserCard');
    const gameConfigModal = document.getElementById('gameConfigModal');
    const cancelGameBtn = document.getElementById('cancelGameBtn');
    const startGameBtn = document.getElementById('startGameBtn');
    
    // Mode Toggles
    const radioButtons = document.querySelectorAll('input[name="gameMode"]');
    const surahSelectGroup = document.getElementById('surahSelectGroup');
    const juzSelectGroup = document.getElementById('juzSelectGroup');

    if (ayatGuesserCard && gameConfigModal) {
        
        // Show/Hide dropdowns based on mode
        if (radioButtons) {
            radioButtons.forEach(radio => {
                radio.addEventListener('change', (e) => {
                    if (e.target.value === 'surah') {
                        surahSelectGroup.style.display = 'block';
                        juzSelectGroup.style.display = 'none';
                    } else {
                        surahSelectGroup.style.display = 'none';
                        juzSelectGroup.style.display = 'block';
                    }
                });
            });
        }

        ayatGuesserCard.addEventListener('click', () => {
            gameConfigModal.style.display = 'flex';
        });

        cancelGameBtn.addEventListener('click', () => {
            gameConfigModal.style.display = 'none';
        });

        startGameBtn.addEventListener('click', () => {
            const mode = document.querySelector('input[name="gameMode"]:checked').value;
            let target;

            if (mode === 'surah') {
                target = document.getElementById('gameSurahSelect').value;
            } else {
                target = document.getElementById('gameJuzSelect').value;
            }

            const qari = document.getElementById('gameQariSelect').value;
            const amount = document.getElementById('gameAmountSelect').value;

            // Save config to sessionStorage
            const gameConfig = { mode, target, qari, amount };
            sessionStorage.setItem('ayatGameConfig', JSON.stringify(gameConfig));

            // Navigate to play page
            window.location.href = '/game/ayat/play';
        });
    }

    // --- GAMEPLAY PAGE LOGIC ---
    const gameInterface = document.getElementById('gameInterface');
    if (gameInterface) {
        const configStr = sessionStorage.getItem('ayatGameConfig');
        if (!configStr) {
            window.location.href = '/game'; 
            return;
        }
        
        const config = JSON.parse(configStr);
        let questions = [];
        let currentIndex = 0;
        let score = 0;

        const audioPlayer = document.getElementById('gameAudioPlayer');
        const playBtn = document.getElementById('playQuestionAudio');
        const optionsGrid = document.getElementById('optionsGrid');
        const currentNumEl = document.getElementById('currentQuestionNum');
        const totalNumEl = document.getElementById('totalQuestionNum');
        const gameOverScreen = document.getElementById('gameOverScreen');

        // Fetch Questions
        fetch('/api/game/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert("Gagal memuat permainan: " + data.error);
                window.location.href = '/game';
                return;
            }
            questions = data;
            totalNumEl.textContent = questions.length;
            loadQuestion(0);
        })
        .catch(err => {
            console.error("Error generating game:", err);
            alert("Gagal memuat permainan.");
            window.location.href = '/game';
        });

        function loadQuestion(index) {
            if (index >= questions.length) {
                endGame();
                return;
            }

            const q = questions[index];
            currentNumEl.textContent = index + 1;
            
            // Reset Audio UI
            audioPlayer.src = q.audio;
            playBtn.classList.remove('playing');
            playBtn.innerHTML = '<i class="fas fa-play"></i>';

            // Render Options
            optionsGrid.innerHTML = '';
            q.options.forEach(optText => {
                const btn = document.createElement('button');
                btn.className = 'option-btn';
                btn.textContent = optText;
                btn.onclick = () => checkAnswer(btn, optText, q.correct);
                optionsGrid.appendChild(btn);
            });
        }

        function checkAnswer(btn, selected, correct) {
            const allBtns = optionsGrid.querySelectorAll('.option-btn');
            allBtns.forEach(b => b.disabled = true);

            if (selected === correct) {
                btn.classList.add('correct');
                score++;
            } else {
                btn.classList.add('wrong');
                allBtns.forEach(b => {
                    if (b.textContent === correct) b.classList.add('correct');
                });
            }

            setTimeout(() => {
                currentIndex++;
                loadQuestion(currentIndex);
            }, 1500);
        }

        function endGame() {
            gameInterface.style.display = 'none';
            gameOverScreen.style.display = 'block';
            document.getElementById('finalScore').textContent = `${score}/${questions.length}`;
        }

        // Audio Controls
        playBtn.addEventListener('click', () => {
            if (audioPlayer.paused) {
                audioPlayer.play();
                playBtn.classList.add('playing');
                playBtn.innerHTML = '<i class="fas fa-pause"></i>';
            } else {
                audioPlayer.pause();
                playBtn.classList.remove('playing');
                playBtn.innerHTML = '<i class="fas fa-play"></i>';
            }
        });

        audioPlayer.addEventListener('ended', () => {
            playBtn.classList.remove('playing');
            playBtn.innerHTML = '<i class="fas fa-play"></i>';
        });

        document.getElementById('playAgainBtn').addEventListener('click', () => {
            window.location.reload(); 
        });
    }
});