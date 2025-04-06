const medForm = document.getElementById('med-form');
const medInput = document.getElementById('med-input');
const medList = document.getElementById('med-list');
const hiddenMeds = document.getElementById('hidden-meds');
const datalist = document.getElementById('med-suggestions');
const drugMap = new Map();  // name -> drugid

const meds = [];

medForm.addEventListener('submit', function (e) {
    if (meds.length === 0) {
        e.preventDefault();
        alert("Please enter at least one medication.");
        return;
    }
    hiddenMeds.value = JSON.stringify(meds);
});

medInput.addEventListener('keydown', function (e) {
    const medName = medInput.value.trim();

    if (e.key === 'Enter' && !(e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        if (medName === '') return;

        if (!meds.includes(drugMap.get(medName.toLowerCase()))) {
            const drugid = drugMap.get(medName.toLowerCase());
            if (!drugid) return;
        
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
        }
        

        medInput.value = '';
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

    try {
        const response = await fetch(`/autocomplete?q=${encodeURIComponent(query)}`);
        const suggestions = await response.json();

        datalist.innerHTML = '';
        drugMap.clear();

        suggestions.forEach(({ name, drugid }) => {
            drugMap.set(name.toLowerCase(), drugid);
            const option = document.createElement('option');
            option.value = name;
            datalist.appendChild(option);
        });
    } catch (error) {
        console.error('Autocomplete failed:', error);
    }
});
