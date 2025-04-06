const medForm = document.getElementById('med-form');
const medInput = document.getElementById('med-input');
const medList = document.getElementById('med-list');
const hiddenMeds = document.getElementById('hidden-meds');
const datalist = document.getElementById('med-suggestions');
const feedback = document.getElementById('feedback');
const drugMap = new Map();  // name -> drugid

const meds = [];

medForm.addEventListener('submit', function (e) {
    if (meds.length === 0) {
        e.preventDefault();
        feedback.textContent = 'Please enter at least one medication.';
        return;
    }
    hiddenMeds.value = JSON.stringify(meds);
});

medInput.addEventListener('keydown', function (e) {
    const medName = medInput.value.trim();

    if (e.key === 'Enter' && !(e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        if (medName === '') return;

        const drugid = drugMap.get(medName.toLowerCase());
        if (!drugid || meds.includes(drugid)) return;

        meds.push(drugid);

        const li = document.createElement('li');
        li.className = 'med-item';
        li.innerHTML = `
            <span>${medName}</span>
            <button class="remove-btn" aria-label="Remove">✖</button>
        `;

        li.querySelector('.remove-btn').addEventListener('click', () => {
            medList.removeChild(li);
            const index = meds.indexOf(drugid);
            if (index !== -1) meds.splice(index, 1);
        });

        medList.appendChild(li);
        medInput.value = '';  // Clear the input field
    }

    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        hiddenMeds.value = JSON.stringify(meds);
        medForm.submit();
    }
});

medInput.addEventListener('input', async function () {
    const query = medInput.value.trim();
    if (query.length === 0) return;

    // Show loading message
    feedback.textContent = 'Loading...';

    try {
        const response = await fetch(`/autocomplete?q=${encodeURIComponent(query)}`);
        const suggestions = await response.json();

        if (response.ok) {
            datalist.innerHTML = '';
            feedback.textContent = '';

            if (suggestions.length === 0) {
                feedback.textContent = 'No medications found for your search.';
            } else {
                suggestions.forEach(({ name, drugid }) => {
                    drugMap.set(name.toLowerCase(), drugid);
                    const option = document.createElement('option');
                    option.value = name;
                    datalist.appendChild(option);
                });
            }
        } else {
            feedback.textContent = suggestions.error || 'Something went wrong. Please try again.';
        }
    } catch (error) {
        console.error('Autocomplete failed:', error);
        feedback.textContent = 'An error occurred. Please try again later.';
    }
});
