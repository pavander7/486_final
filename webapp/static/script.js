const medForm = document.getElementById('med-form');
const medInput = document.getElementById('med-input');
const medList = document.getElementById('med-list');
const hiddenMeds = document.getElementById('hidden-meds');
const suggestionsBox = document.getElementById('suggestions-box');
const feedback = document.getElementById('feedback');

const meds = [];
let activeIndex = -1;

medInput.focus(); // Auto-focus on page load

function clearSuggestions() {
    suggestionsBox.innerHTML = '';
    activeIndex = -1;
}

function highlightSuggestion(index) {
    const items = suggestionsBox.querySelectorAll('li');
    items.forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });
}

function addMedication(medName) {
    const entry = medName.toLowerCase();
    if (!entry || meds.includes(entry)) return;

    meds.push(entry);

    const firstGeneric = entry.generic_names?.[0] || medName;
    const tooltip = [
        entry.generic_names.length ? `Generic: ${entry.generic_names.join(', ')}` : '',
        entry.brand_names.length ? `Brand: ${entry.brand_names.join(', ')}` : ''
    ].filter(Boolean).join('\n');

    const li = document.createElement('li');
    li.className = 'med-item';
    li.title = tooltip;
    li.innerHTML = `
        <span>
            ${firstGeneric}
        </span>
        <button class="remove-btn" aria-label="Remove">✖</button>
    `;

    li.querySelector('.remove-btn').addEventListener('click', () => {
        medList.removeChild(li);
        const index = meds.indexOf(entry);
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
            suggestions.forEach(({ med_name, drugid, source, generic_names, brand_names }) => {
                const tooltip = [
                    generic_names.length ? `Generic: ${generic_names.join(', ')}` : '',
                    brand_names.length ? `Brand: ${brand_names.join(', ')}` : ''
                ].filter(Boolean).join('\n');
            
                const li = document.createElement('li');
                li.title = tooltip;
                li.innerHTML = `
                    <span>${sourceIcons[source] || '❔'}</span>
                    <span>${med_name} <em style="color: #888; font-size: 0.85em;">(${source.replace('_', ' ')})</em></span>
                `;
                li.addEventListener('click', () => addMedication(med_name));
                suggestionsBox.appendChild(li);
            
                drugMap.set(med_name.toLowerCase(), {
                    drugid,
                    source,
                    generic_names,
                    brand_names
                });
            });                      
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
            const name = selected.querySelector('span:nth-child(2)').textContent;
            addMedication(name);
        } else {
            const medName = medInput.value.trim();
            if (medName) {
                e.preventDefault();
                addMedication(medName);
            }
        }
    } else if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        hiddenMeds.value = JSON.stringify(meds);
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
