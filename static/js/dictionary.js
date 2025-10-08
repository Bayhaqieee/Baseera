document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const content = document.getElementById('dictionary-content');
    const cards = content.getElementsByClassName('dictionary-card');
    const searchError = document.getElementById('searchError');
    const noResultsMessage = document.getElementById('noResultsMessage');
    let searchTimeout;

    searchInput.addEventListener('input', (event) => {
        const originalSearchTerm = event.target.value.trim();

        // Clear previous timeouts and messages
        clearTimeout(searchTimeout);
        searchError.classList.remove('visible');
        noResultsMessage.style.display = 'none';

        // Reset the state of all cards before applying new filters
        for (const card of cards) {
            card.style.display = "";
            const details = card.querySelector('details');
            if (details) details.open = false;
            card.querySelectorAll('.verse-item').forEach(v => v.style.display = "");
        }

        // If search is empty, show all and do nothing else
        if (originalSearchTerm === "") {
            return;
        }

        // --- Use Case 3: Specific Verse Search (e.g., "18:1") ---
        if (/^\d+:\d+$/.test(originalSearchTerm)) {
            const [searchSurah, searchAyah] = originalSearchTerm.split(':');
            let itemFound = false;
            for (const card of cards) {
                if (card.getAttribute('data-surah-number') === searchSurah) {
                    card.style.display = "";
                    card.querySelector('details').open = true;

                    let verseFound = false;
                    card.querySelectorAll('.verse-item').forEach(verse => {
                        if (verse.getAttribute('data-ayat-number') === searchAyah) {
                            verse.style.display = "";
                            verseFound = true;
                        } else {
                            verse.style.display = "none";
                        }
                    });
                    if (verseFound) itemFound = true;
                } else {
                    card.style.display = "none";
                }
            }
            if (!itemFound) {
                noResultsMessage.textContent = `Hasil pencarian untuk '${originalSearchTerm}' tidak ditemukan.`;
                noResultsMessage.style.display = 'block';
            }
            return; // Stop execution for this specific case
        }

        // --- Use Cases 1 & 2: Text and Surah Number Search ---
        const isNumericOnly = /^\d+$/.test(originalSearchTerm);
        const searchTerm = originalSearchTerm.toLowerCase().replace(/[-\s]/g, "");

        // Validate text search length (numeric search bypasses this)
        if (!isNumericOnly && searchTerm.length > 0 && searchTerm.length < 3) {
            searchTimeout = setTimeout(() => {
                searchError.textContent = 'Pencarian membutuhkan minimal 3 karakter.';
                searchError.classList.add('visible');
            }, 5000);
            for (const card of cards) card.style.display = "none"; // Hide results for invalid input
            return;
        }

        let visibleCardsCount = 0;
        for (const card of cards) {
            const surahNumber = card.getAttribute('data-surah-number');
            const surahName = card.querySelector('h3').textContent;
            
            // Create a comprehensive string to search against, ignoring hyphens and spaces
            const fullText = `${surahNumber} ${surahName}`;
            const simplifiedText = fullText.toLowerCase().replace(/[-\s]/g, '');
            
            let isMatch = false;
            if (isNumericOnly) {
                isMatch = (surahNumber === originalSearchTerm);
            } else {
                isMatch = simplifiedText.includes(searchTerm);
            }

            if (isMatch) {
                card.style.display = "";
                visibleCardsCount++;
            } else {
                card.style.display = "none";
            }
        }

        if (visibleCardsCount === 0 && originalSearchTerm.length > 0) {
            noResultsMessage.textContent = `Hasil pencarian untuk '${originalSearchTerm}' tidak ditemukan.`;
            noResultsMessage.style.display = 'block';
        }
    });
});