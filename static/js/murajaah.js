document.addEventListener('DOMContentLoaded', () => {

    // --- Logic for murajaah.html (Selection Page) ---
    const qariSelect = document.getElementById('qariSelect');
    const qariImage = document.getElementById('qariImage'); 
    const surahListContainer = document.getElementById('surahListContainer');
    const surahSearchInput = document.getElementById('surahSearchInput');

    if (qariSelect && surahListContainer) {
        function updateSurahLinks() {
            const selectedQari = qariSelect.value;
            const surahCards = surahListContainer.querySelectorAll('.surah-select-card');
            surahCards.forEach(card => {
                const baseUrl = card.href.split('?')[0];
                card.href = `${baseUrl}?qari=${selectedQari}`;
            });
        }
        function updateQariImage() {
            if (!qariImage) return;
            const selectedOption = qariSelect.options[qariSelect.selectedIndex];
            const newImageSrc = selectedOption.getAttribute('data-image-src');
            if (newImageSrc) qariImage.src = newImageSrc;
        }
        function filterSurahs() {
            const searchTerm = surahSearchInput.value.toLowerCase();
            const surahCards = surahListContainer.querySelectorAll('.surah-select-card');
            surahCards.forEach(card => {
                const namaLatin = card.getAttribute('data-nama-latin');
                const nomor = card.getAttribute('data-nomor');
                if (namaLatin.includes(searchTerm) || nomor.includes(searchTerm)) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }
            });
        }
        updateSurahLinks(); 
        qariSelect.addEventListener('change', () => {
            updateSurahLinks();
            updateQariImage();
        });
        surahSearchInput.addEventListener('input', filterSurahs);
    }


    // --- Logic for murajaah_detail.html (Reading Page) ---
    const audioPlayer = document.getElementById('murajaahAudioPlayer');
    const textContent = document.getElementById('murajaahTextContent');
    const autoplaySwitch = document.getElementById('autoplaySwitch');
    
    // Modal Elements
    const nextSurahModal = document.getElementById('nextSurahModal');
    const countdownDisplay = document.getElementById('countdownTimer');
    const stayButton = document.getElementById('stayButton');
    const continueButton = document.getElementById('continueButton');
    const nextSurahId = document.getElementById('nextSurahId')?.value;
    const currentQari = document.getElementById('currentQari')?.value;

    let currentPlayingAyat = null;
    let countdownInterval = null;

    if (audioPlayer && textContent) {
        
        // Play specific ayat
        function playAyat(ayatSpan) {
            const audioSrc = ayatSpan.getAttribute('data-audio-src');
            if (!audioSrc) return;

            // Reset UI for previous ayat
            if (currentPlayingAyat) {
                currentPlayingAyat.classList.remove('playing');
            }

            audioPlayer.src = audioSrc;
            audioPlayer.play();
            ayatSpan.classList.add('playing');
            currentPlayingAyat = ayatSpan;
            
            // Scroll into view smoothly if needed
            ayatSpan.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        // Handle click on text
        textContent.addEventListener('click', (event) => {
            const ayatSpan = event.target.closest('.ayat-span');
            if (!ayatSpan) return;

            // If clicking the currently playing ayat, pause it
            if (currentPlayingAyat === ayatSpan && !audioPlayer.paused) {
                audioPlayer.pause();
                return; // Don't clear 'playing' class to show position
            }
            
            // If paused on current ayat, resume
            if (currentPlayingAyat === ayatSpan && audioPlayer.paused) {
                audioPlayer.play();
                return;
            }

            // Otherwise play new ayat
            playAyat(ayatSpan);
        });

        // Handle audio ending (Autoplay Logic)
        audioPlayer.addEventListener('ended', () => {
            if (autoplaySwitch.checked && currentPlayingAyat) {
                // Find the next ayat span (skipping the separator text node/span)
                let nextElement = currentPlayingAyat.nextElementSibling;
                
                // Skip over separator spans or text nodes until we find the next .ayat-span
                while (nextElement && !nextElement.classList.contains('ayat-span')) {
                    nextElement = nextElement.nextElementSibling;
                }

                if (nextElement) {
                    playAyat(nextElement);
                } else {
                    // End of Surah reached
                    currentPlayingAyat.classList.remove('playing');
                    currentPlayingAyat = null;
                    handleEndOfSurah();
                }
            } else {
                // Autoplay off or manual stop
                if (currentPlayingAyat) {
                    currentPlayingAyat.classList.remove('playing');
                    currentPlayingAyat = null;
                }
            }
        });

        // --- Next Surah Modal Logic ---
        function handleEndOfSurah() {
            if (!nextSurahId || parseInt(nextSurahId) > 114) return; // No next surah

            nextSurahModal.style.display = 'flex';
            let timeLeft = 5;
            countdownDisplay.textContent = timeLeft;

            countdownInterval = setInterval(() => {
                timeLeft--;
                countdownDisplay.textContent = timeLeft;
                if (timeLeft <= 0) {
                    goToNextSurah();
                }
            }, 1000);
        }

        function goToNextSurah() {
            clearInterval(countdownInterval);
            // UPDATED: Append autoplay=true parameter
            window.location.href = `/murajaah/surat/${nextSurahId}?qari=${currentQari}&autoplay=true`;
        }

        if (stayButton) {
            stayButton.addEventListener('click', () => {
                clearInterval(countdownInterval);
                nextSurahModal.style.display = 'none';
            });
        }

        if (continueButton) {
            continueButton.addEventListener('click', () => {
                goToNextSurah();
            });
        }

        // --- NEW: Check for autoplay URL parameter ---
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('autoplay') === 'true' && autoplaySwitch) {
            // Turn on the switch
            autoplaySwitch.checked = true;
            
            // Find and play the first ayat
            const firstAyat = textContent.querySelector('.ayat-span');
            if (firstAyat) {
                // Slight delay to ensure audio context and page load are ready
                setTimeout(() => {
                    playAyat(firstAyat);
                }, 500);
            }
        }
    }
});