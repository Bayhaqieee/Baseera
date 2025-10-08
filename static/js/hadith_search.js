document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const content = document.getElementById('dictionary-content');
    const noResultsMessage = document.getElementById('noResultsMessage');
    
    // Select all cards, whether they are list-cards (links) or dictionary-cards (details)
    const cards = content.querySelectorAll('.dictionary-card, .list-card');

    if (!searchInput) return;

    searchInput.addEventListener('input', (event) => {
        const searchTerm = event.target.value.toLowerCase();
        let visibleCount = 0;

        for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            const cardText = card.textContent || card.innerText;

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
});