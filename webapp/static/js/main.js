// Global variables
let selectedDrugs = new Map();

document.addEventListener('DOMContentLoaded', function () {
    // Initialize accessibility features
    initAccessibility();

    // Initialize search functionality
    initSearch();

    // Initialize interaction checking
    initInteractionCheck();
});

function initAccessibility() {
    // Font size controls
    const fontSizeControls = document.querySelectorAll('.font-size-control');
    fontSizeControls.forEach(control => {
        control.addEventListener('click', function (e) {
            e.preventDefault();
            const size = this.dataset.size;
            document.body.style.fontSize = size;
            announceToScreenReader(`Font size set to ${size}`);
        });
    });

    // High contrast toggle
    const contrastToggle = document.querySelector('.contrast-toggle');
    if (contrastToggle) {
        contrastToggle.addEventListener('click', function () {
            document.body.classList.toggle('high-contrast');
            const isHighContrast = document.body.classList.contains('high-contrast');
            announceToScreenReader(`High contrast mode ${isHighContrast ? 'enabled' : 'disabled'}`);
        });
    }

    // Keyboard navigation
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });

    document.addEventListener('mousedown', function () {
        document.body.classList.remove('keyboard-navigation');
    });
}

function initSearch() {
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-input');
    const resultsContainer = document.querySelector('.results-section');
    const selectedDrugsList = document.querySelector('.selected-drugs-list');
    const interactionForm = document.querySelector('.interaction-form');
    const checkButton = interactionForm.querySelector('button[type="submit"]');

    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const query = searchInput.value.trim();

            if (query) {
                try {
                    const response = await fetch('/search', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query }),
                    });

                    const results = await response.json();
                    displayResults(results);
                } catch (error) {
                    console.error('Search error:', error);
                    announceToScreenReader('Error performing search. Please try again.');
                }
            }
        });
    }

    // Add event listener for drug selection
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('select-drug')) {
            const drugId = e.target.dataset.drugId;
            const drugName = e.target.dataset.drugName;

            if (selectedDrugs.has(drugId)) {
                selectedDrugs.delete(drugId);
                e.target.textContent = 'Select';
                e.target.classList.remove('selected');
            } else {
                selectedDrugs.set(drugId, drugName);
                e.target.textContent = 'Selected';
                e.target.classList.add('selected');
            }

            updateSelectedDrugsList();
            checkButton.disabled = selectedDrugs.size < 2;
        } else if (e.target.classList.contains('remove-drug')) {
            const drugId = e.target.dataset.drugId;
            selectedDrugs.delete(drugId);
            updateSelectedDrugsList();
            checkButton.disabled = selectedDrugs.size < 2;

            // Also update the select button in the search results
            const selectButton = document.querySelector(`.select-drug[data-drug-id="${drugId}"]`);
            if (selectButton) {
                selectButton.textContent = 'Select';
                selectButton.classList.remove('selected');
            }
        }
    });

    function updateSelectedDrugsList() {
        selectedDrugsList.innerHTML = '';
        selectedDrugs.forEach((name, id) => {
            const drugItem = document.createElement('div');
            drugItem.className = 'selected-drug-item';
            drugItem.innerHTML = `
                <span>${name}</span>
                <button class="remove-drug" data-drug-id="${id}">×</button>
            `;
            selectedDrugsList.appendChild(drugItem);
        });
    }
}

function initInteractionCheck() {
    const interactionForm = document.querySelector('.interaction-form');
    const checkButton = interactionForm.querySelector('button[type="submit"]');

    // Check interactions
    interactionForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        if (selectedDrugs.size < 2) {
            alert('Please select at least two drugs to check interactions');
            return;
        }

        try {
            const response = await fetch('/interactions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    drugs: Array.from(selectedDrugs.keys())
                })
            });

            const interactions = await response.json();
            displayInteractions(interactions);
        } catch (error) {
            console.error('Error checking interactions:', error);
            alert('Error checking interactions. Please try again.');
        }
    });
}

function displayResults(results) {
    const resultsContainer = document.querySelector('.results-section');
    if (!resultsContainer) return;

    resultsContainer.innerHTML = results.map(result => `
        <div class="drug-card" role="article">
            <h3>${result.name}</h3>
            <p>${result.description}</p>
            <button class="select-drug" 
                    data-drug-id="${result.drugid}" 
                    data-drug-name="${result.name}"
                    aria-label="Select ${result.name}">
                Select Drug
            </button>
        </div>
    `).join('');

    announceToScreenReader(`Found ${results.length} results`);
}

function displayInteractions(interactions) {
    const interactionsContainer = document.querySelector('.interactions-section');
    if (!interactionsContainer) return;

    if (interactions.length === 0) {
        interactionsContainer.innerHTML = `
            <div class="no-interactions" role="alert">
                <p>No known interactions found between the selected medications.</p>
                <p class="note">Note: This does not guarantee that there are no interactions. Always consult with your healthcare provider about potential drug interactions.</p>
            </div>
        `;
        announceToScreenReader('No known interactions found between the selected medications.');
        return;
    }

    interactionsContainer.innerHTML = interactions.map(interaction => `
        <div class="interaction-warning ${interaction.severity}" role="alert">
            <h4>${interaction.title || 'Potential Interaction'}</h4>
            <p>${interaction.description}</p>
            ${interaction.recommendation ? `<p><strong>Recommendation:</strong> ${interaction.recommendation}</p>` : ''}
        </div>
    `).join('');

    announceToScreenReader(`Found ${interactions.length} potential interactions`);
}

function announceToScreenReader(message) {
    const liveRegion = document.querySelector('[aria-live]');
    if (liveRegion) {
        liveRegion.textContent = message;
    }
}

// Error handling
window.addEventListener('error', function (e) {
    console.error('Error:', e.error);
    announceToScreenReader('An error occurred. Please try again.');
}); 