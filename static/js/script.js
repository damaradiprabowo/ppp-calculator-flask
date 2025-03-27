document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('calculatorForm');
    const result = document.getElementById('result');
    const otherData = document.getElementById('otherData');

    document.getElementById('calculatorForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const loadingElement = document.getElementById('loading');
        const resultElement = document.getElementById('result');
        const otherDataElement = document.getElementById('otherData');
        const submitButton = this.querySelector('button[type="submit"]');

        // Show loading, hide results
        loadingElement.style.display = 'flex';
        resultElement.style.display = 'none';
        otherDataElement.style.display = 'none';
        submitButton.disabled = true;
        
        const formData = new FormData(form);
        
        fetch('/calculate', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading, show results
            loadingElement.style.display = 'none';
            resultElement.style.display = 'block';
            otherDataElement.style.display = 'block';
            submitButton.disabled = false;

            // Generate flag image URLs
            const sourceFlagUrl = `https://flagcdn.com/16x12/${data.sourceIso2Code}.png`;
            const targetFlagUrl = `https://flagcdn.com/16x12/${data.targetIso2Code}.png`;

            // Update result
            document.getElementById('resultFlag').innerHTML = `
                <img src="${targetFlagUrl}" 
                     srcset="https://flagcdn.com/32x24/${data.targetIso2Code}.png 2x,
                             https://flagcdn.com/48x36/${data.targetIso2Code}.png 3x"
                     width="24" 
                     height="16" 
                     alt="${data.targetCountry}">
            `;

            // Result data
            document.getElementById('resultCountry').textContent = `${data.targetCountry}`;
            document.getElementById('resultValueYearly').textContent = `${data.targetAmountYearly}`;
            document.getElementById('resultValueMonthly').textContent = `${data.targetAmountMonthly}`;
            result.style.display = 'block';

            // Update other data
            const incomeLevelCell = document.getElementById('incomeLevel');
            const distanceCell = document.getElementById('distance');
            const targetCapitalCell = document.getElementById('targetCapital');
            const gdpPerCapitaCell = document.getElementById('gdpPerCapita');
            
            const incomeLevels = ['Low income', 'Lower middle income', 'Upper middle income', 'High income'];
            const sourceIndex = incomeLevels.indexOf(data.sourceIncomeLevel);
            const targetIndex = incomeLevels.indexOf(data.targetIncomeLevel);
            
            let incomeChangeSymbol = '🟰';
            if (targetIndex > sourceIndex) {
                incomeChangeSymbol = '⏶';
                incomeLevelCell.classList.add('income-increase');
                incomeLevelCell.classList.remove('income-decrease');
            } else if (targetIndex < sourceIndex) {
                incomeChangeSymbol = '⏷';
                incomeLevelCell.classList.add('income-decrease');
                incomeLevelCell.classList.remove('income-increase');
            } else {
                incomeLevelCell.classList.remove('income-increase', 'income-decrease');
            }
            
            incomeLevelCell.textContent = `${incomeChangeSymbol} ${data.targetIncomeLevel}`;
            
            const distance = parseFloat(data.distance);
            const flightHours = Math.round(distance / 800 ) ; // Assuming 800 km/h average speed
            distanceCell.textContent = `${data.distance} KM (🛫 ~${flightHours} hours)`;
            
            const mapUrl = `https://www.google.com/maps/place/${encodeURIComponent(data.targetCapital)}`;
            targetCapitalCell.innerHTML = `${data.targetCapital} <a href="${mapUrl}" target="_blank">🗺️</a>`;
            
            gdpPerCapitaCell.textContent = `$${parseFloat(data.targetGDP).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

            // Calculate and display GDP difference
            const gdpDifference = ((parseFloat(data.targetGDP) - parseFloat(data.sourceGDP)) / parseFloat(data.sourceGDP) * 100).toFixed(2);
            let gdpChangeSymbol;
            if (gdpDifference > 0) {
                gdpChangeSymbol = '⏶';
                gdpPerCapitaCell.classList.add('income-increase');
                gdpPerCapitaCell.classList.remove('income-decrease');
            } else if (gdpDifference < 0) {
                gdpChangeSymbol = '⏷';
                gdpPerCapitaCell.classList.add('income-decrease');
                gdpPerCapitaCell.classList.remove('income-increase');
            } else {
                gdpChangeSymbol = '🟰';
                gdpPerCapitaCell.classList.remove('income-increase', 'income-decrease');
            }
            gdpPerCapitaCell.textContent += ` (${gdpChangeSymbol} ${gdpDifference}%)`;
            
            otherData.style.display = 'block';
        })
        .catch((error) => {
            console.error('Error:', error);
            loadingElement.style.display = 'none';
            submitButton.disabled = false;
        });
    });

    // Auto-trigger conversion if URL has parameters
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('source') && urlParams.has('destination')) {
        const submitButton = document.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.click();
        }
    }
});

document.getElementById('sourceAmount').addEventListener('input', function(e) {
    // Remove non-digit characters
    let value = this.value.replace(/[^\d.]/g, '');
    
    // Ensure only one decimal point
    let parts = value.split('.');
    if (parts.length > 2) {
        parts = [parts[0], parts.slice(1).join('')];
    }
    if (parts[1]) {
        parts[1] = parts[1].slice(0, 2);
    }
    value = parts.join('.');

    // Format with commas
    value = value.replace(/\B(?=(\d{3})+(?!\d))/g, ",");

    // Update input value
    this.value = value;
});

// Modal functionality
const modals = {
    credits: document.getElementById("creditsPopup"),
    definitions: document.getElementById("definitionsPopup")
};

const buttons = {
    credits: document.getElementById("creditsButton"),
    definitions: document.getElementById("definitionsButton")
};

// Open modal
function openModal(modalType) {
    modals[modalType].style.display = "block";
}

// Close modal
function closeModal(modalType) {
    modals[modalType].style.display = "none";
}

// Event listeners for opening modals
buttons.credits.onclick = () => openModal('credits');
buttons.definitions.onclick = () => openModal('definitions');

// Event listeners for closing modals
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.onclick = function() {
        closeModal(this.closest('.popup').id.replace('Popup', ''));
    }
});

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('popup')) {
        closeModal(event.target.id.replace('Popup', ''));
    }
}

// Add this function after DOMContentLoaded
function updateURL() {
    const sourceCountry = document.getElementById('sourceCountry').value;
    const targetCountry = document.getElementById('targetCountry').value;
    const amount = document.getElementById('sourceAmount').value;
    const frequency = document.getElementById('salaryFrequency').value;
    
    // Create URL-friendly slugs
    const sourceSlug = sourceCountry.toLowerCase().replace(/ /g, '-');
    const targetSlug = targetCountry.toLowerCase().replace(/ /g, '-');
    
    // Build query string
    const params = new URLSearchParams({
        source: sourceSlug,
        destination: targetSlug,
        granularity: frequency
    });
    
    // Only add amount if it's not empty
    if (amount) {
        params.append('value', amount.replace(/,/g, ''));
    }
    
    // Update URL without reloading the page
    const newPath = `/convert/?${params.toString()}`;
    window.history.pushState({}, '', newPath);
}

// Add these event listeners after the existing ones
document.getElementById('sourceCountry').addEventListener('change', updateURL);
document.getElementById('targetCountry').addEventListener('change', updateURL);
document.getElementById('sourceAmount').addEventListener('input', updateURL);
document.getElementById('salaryFrequency').addEventListener('change', updateURL);

// Update switchCountries event listener
document.getElementById('switchCountries').addEventListener('click', function() {
    const sourceCountry = document.getElementById('sourceCountry');
    const targetCountry = document.getElementById('targetCountry');
    
    // Store the current values
    const sourceValue = sourceCountry.value;
    const targetValue = targetCountry.value;
    
    // Swap the values
    sourceCountry.value = targetValue;
    targetCountry.value = sourceValue;
    
    // Update URL after switching
    updateURL();
});