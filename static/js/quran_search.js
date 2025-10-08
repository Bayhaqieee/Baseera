document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const content = document.getElementById('dictionary-content');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const audioPlayer = document.getElementById('audioPlayer');
    let currentPlayingButton = null;

    // Check if we are on the detail page (has .verse-card) or list page (has .list-card)
    let cards = content.querySelectorAll('.verse-card');
    let isDetailPage = true;
    if (cards.length === 0) {
        cards = content.querySelectorAll('.list-card');
        isDetailPage = false;
    }

    // --- Search Functionality ---
    if (searchInput) {
        searchInput.addEventListener('input', (event) => {
            const searchTerm = event.target.value.toLowerCase().trim();
            let visibleCount = 0;

            for (let i = 0; i < cards.length; i++) {
                const card = cards[i];
                let cardText = '';

                if (isDetailPage) {
                    // On detail page, search translation, latin text, and ayat number
                    const ayatNum = card.querySelector('.verse-item').getAttribute('data-ayat-number');
                    const translation = card.querySelector('.translation-text').textContent; // Use specific class
                    const latin = card.querySelector('.latin-text').textContent;
                    cardText = `${ayatNum} ${translation} ${latin}`;
                } else {
                    // On list page, search surah name, latin name, and number
                    const surahNum = card.getAttribute('data-surah-number');
                    const surahName = card.querySelector('h3').textContent;
                    const arabicName = card.querySelector('.arabic-surah-name').textContent;
                    cardText = `${surahNum} ${surahName} ${arabicName}`;
                }

                if (cardText.toLowerCase().indexOf(searchTerm) > -1) {
                    card.style.display = "";
                    visibleCount++;
                } else {
                    card.style.display = "none";
                }
            }

            if (visibleCount === 0 && searchTerm.length > 0) {
                noResultsMessage.textContent = `No results found for '${event.target.value}'`;
                noResultsMessage.style.display = 'block';
            } else {
                noResultsMessage.style.display = 'none';
            }
        });
    }

    // --- Audio Player Functionality ---
    if (isDetailPage && audioPlayer) {
        content.querySelectorAll('.play-button').forEach(button => {
            button.addEventListener('click', () => {
                const audioSrc = button.getAttribute('data-audio-src');
                if (!audioSrc) return;

                if (currentPlayingButton === button && !audioPlayer.paused) {
                    // Pause current audio if same button clicked
                    audioPlayer.pause();
                    button.classList.remove('fa-pause-circle');
                    button.classList.add('fa-play-circle');
                    currentPlayingButton = null;
                } else {
                    // Stop previous audio if different button clicked
                    if (currentPlayingButton) {
                         currentPlayingButton.classList.remove('fa-pause-circle');
                         currentPlayingButton.classList.add('fa-play-circle');
                    }
                    // Play new audio
                    audioPlayer.src = audioSrc;
                    audioPlayer.play();
                    button.classList.remove('fa-play-circle');
                    button.classList.add('fa-pause-circle');
                    currentPlayingButton = button;
                }
            });
        });

        // Reset icon when audio finishes
        audioPlayer.addEventListener('ended', () => {
            if (currentPlayingButton) {
                currentPlayingButton.classList.remove('fa-pause-circle');
                currentPlayingButton.classList.add('fa-play-circle');
                currentPlayingButton = null;
            }
        });
         // Reset icon if paused manually (not via button click)
        audioPlayer.addEventListener('pause', () => {
             if (currentPlayingButton && audioPlayer.paused && audioPlayer.currentTime > 0) {
                 // Check currentTime > 0 to differentiate from initial state or ended state
                 // Only reset if pause wasn't triggered by clicking the *same* button
                 if (currentPlayingButton !== event?.target) { // Check if pause came from button click event
                     currentPlayingButton.classList.remove('fa-pause-circle');
                     currentPlayingButton.classList.add('fa-play-circle');
                     currentPlayingButton = null;
                 }
             }
         });
    }

    // --- Copy Button Functionality ---
    if (isDetailPage) {
        content.querySelectorAll('.copy-button').forEach(button => {
            button.addEventListener('click', () => {
                const verseItem = button.closest('.verse-card').querySelector('.verse-item');
                const arabic = verseItem.querySelector('.arabic-text').textContent;
                const latin = verseItem.querySelector('.latin-text').textContent;
                const translation = verseItem.querySelector('.translation-text').textContent;
                const ayatNumber = verseItem.getAttribute('data-ayat-number');
                const surahName = document.querySelector('.quran-detail-header-card h1').textContent; // Get Surah name

                const textToCopy = `QS. ${surahName} [${ayatNumber}]\n\n${arabic}\n\n${latin}\n\n${translation}`;

                navigator.clipboard.writeText(textToCopy).then(() => {
                    // Success feedback: change icon briefly
                    button.classList.remove('fa-copy');
                    button.classList.add('fa-check'); // Use checkmark icon
                    button.classList.add('copied');   // Add class for styling
                    setTimeout(() => {
                        button.classList.remove('fa-check');
                        button.classList.add('fa-copy');
                        button.classList.remove('copied');
                    }, 1500); // Change back after 1.5 seconds
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                    // Optional: Add visual feedback for error
                });
            });
        });
    }
});