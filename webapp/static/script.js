const medForm = document.getElementById('med-form');
const medInput = document.getElementById('med-input');
const medList = document.getElementById('med-list');
const hiddenMeds = document.getElementById('hidden-meds');
const suggestionsBox = document.getElementById('suggestions-box');
const feedback = document.getElementById('feedback');
const accToggleBtn = document.getElementById('accessibility-toggle');
const accPanel = document.getElementById('accessibility-panel');
const highContrastToggle = document.getElementById('high-contrast-toggle');
const largeTextToggle = document.getElementById('large-text-toggle');

const meds = [];
let activeIndex = -1;

medInput.focus(); // Auto-focus on page load

function clearSuggestions() {
    suggestionsBox.innerHTML = '';
    activeIndex = -1;
    medInput.setAttribute('aria-expanded', 'false');
    medInput.removeAttribute('aria-activedescendant');
}

function highlightSuggestion(index) {
    const items = suggestionsBox.querySelectorAll('li');
    items.forEach((item, i) => {
        item.classList.toggle('active', i === index);
        if (i === index) {
            medInput.setAttribute('aria-activedescendant', item.id);
        }
    });
}

function addMedication({ name }) {
    const entry = name.toLowerCase();
    if (!entry || meds.some(m => m.name === entry)) return;

    meds.push({ name: entry });
    const tooltip = [
        entry.generic_names.length ? `Generic: ${entry.generic_names.join(', ')}` : '',
        entry.brand_names.length ? `Brand: ${entry.brand_names.join(', ')}` : ''
    ].filter(Boolean).join('\n');

    const li = document.createElement('li');
    li.className = 'med-item';
    li.title = tooltip;
    li.innerHTML = `
        <a href="/medication-search/${name}" target="_blank">${name}</a>
        <button class="remove-btn" aria-label="Remove">✖</button>
    `;

    li.querySelector('.remove-btn').addEventListener('click', () => {
        medList.removeChild(li);
        const index = meds.findIndex(m => m.name === entry);
        if (index !== -1) meds.splice(index, 1);
    });

    medList.appendChild(li);
    medInput.value = '';
    clearSuggestions();
}

medInput.addEventListener('input', async function () {
    const query = medInput.value.trim();
    clearSuggestions();
    feedback.textContent = '';

    if (query.length === 0) return;

    feedback.textContent = 'Loading...';

    try {
        const response = await fetch(`/autocomplete?q=${encodeURIComponent(query)}`);
        const suggestions = await response.json();

        feedback.textContent = '';

        if (response.ok && suggestions.length > 0) {
            suggestions.forEach(({ med_name, drugid, source, generic_names, brand_names }, idx) => {
                const li = document.createElement('li');
                li.id = `suggestion-${idx}`;
                li.setAttribute('role', 'option');
                
                li.innerHTML = `
                    <span class="source-tag">${source}</span>
                    <a href="/medication-search/${med_name}" target="_blank">${med_name}</a>
                `;
                
                li.addEventListener('click', () => {
                    addMedication({ name: med_name });
                });
            
                suggestionsBox.appendChild(li);
            });
            medInput.setAttribute('aria-expanded', 'true');                      
        } else {
            feedback.textContent = suggestions.message || suggestions.error || 'No medications found.';
        }
    } catch (error) {
        console.error('Autocomplete failed:', error);
        feedback.textContent = 'An error occurred. Please try again later.';
    }
});

medInput.addEventListener('keydown', function (e) {
    const items = suggestionsBox.querySelectorAll('li');

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (items.length === 0) return;
        activeIndex = (activeIndex + 1) % items.length;
        highlightSuggestion(activeIndex);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (items.length === 0) return;
        activeIndex = (activeIndex - 1 + items.length) % items.length;
        highlightSuggestion(activeIndex);
    } else if (e.key === 'Enter') {
        const selected = items[activeIndex];
        if (selected) {
            e.preventDefault();
            const anchor = selected.querySelector('a');
            if (anchor) {
                addMedication({ name: anchor.textContent, drugid: anchor.href.split('/').pop() });
            }
        } else {
            const medName = medInput.value.trim();
            if (medName) {
                e.preventDefault();
                addMedication(medName);
            }
        }
    } else if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        medForm.submit();
    } else if (e.key === 'Escape') {
        clearSuggestions();
    }
});

// Click-away to close suggestions
document.addEventListener('click', function (e) {
    if (!suggestionsBox.contains(e.target) && e.target !== medInput) {
        clearSuggestions();
    }
});

medForm.addEventListener('submit', function (e) {
    if (meds.length === 0) {
        e.preventDefault();
        feedback.textContent = 'Please enter at least one medication.';
        return;
    }
    hiddenMeds.value = JSON.stringify(meds);
});

// Show/hide settings panel
accToggleBtn.addEventListener('click', () => {
    const isExpanded = accPanel.classList.toggle('hidden') === false;
    accToggleBtn.setAttribute('aria-expanded', isExpanded.toString());
});

// Toggle high contrast
highContrastToggle.addEventListener('change', (e) => {
    document.body.classList.toggle('high-contrast', e.target.checked);
});

// Toggle large text
largeTextToggle.addEventListener('change', (e) => {
    document.body.classList.toggle('large-text', e.target.checked);
});
