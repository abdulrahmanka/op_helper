// Option Pricing Helper - Frontend JavaScript

// Detect environment and set API base URL
let API_BASE;
if (window.location.hostname === 'localhost' && window.location.port === '3000') {
    // Local development - frontend on 3000, backend on 5000
    API_BASE = 'http://localhost:5000';
} else if (window.location.hostname === 'localhost') {
    // Local backend only
    API_BASE = 'http://localhost:5000';
} else {
    // Netlify deployment
    API_BASE = '/.netlify/functions/api';
}

// DOM Elements
const configBtn = document.getElementById('configBtn');
const configSection = document.getElementById('configSection');
const calculatorForm = document.getElementById('calculatorForm');
const results = document.getElementById('results');
const loading = document.getElementById('loading');
const noResults = document.getElementById('noResults');

// Configuration elements
const totalCapitalInput = document.getElementById('totalCapital');
const riskPercentageInput = document.getElementById('riskPercentage');
const saveConfigBtn = document.getElementById('saveConfigBtn');
const loadConfigBtn = document.getElementById('loadConfigBtn');
const configStatus = document.getElementById('configStatus');

// Result elements
const riskValidation = document.getElementById('riskValidation');
const tradeDecay = document.getElementById('tradeDecay');
const riskAmount = document.getElementById('riskAmount');
const takeProfit = document.getElementById('takeProfit');
const stopLoss = document.getElementById('stopLoss');
const positionSizeSection = document.getElementById('positionSizeSection');
const positionSizeContent = document.getElementById('positionSizeContent');

// Event Listeners
configBtn.addEventListener('click', toggleConfigSection);
calculatorForm.addEventListener('submit', handleCalculate);
saveConfigBtn.addEventListener('click', saveConfiguration);
loadConfigBtn.addEventListener('click', loadConfiguration);

// Real-time calculation setup
const inputIds = ['delta', 'theta', 'tradeTime', 'risk', 'reward', 'entry', 'tradeType'];
let calculationTimeout;

inputIds.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
        element.addEventListener('input', debounceCalculation);
        element.addEventListener('change', debounceCalculation);
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadConfiguration();
    // Calculate with default values
    setTimeout(debounceCalculation, 500);
});

function toggleConfigSection() {
    configSection.classList.toggle('hidden');
}

function debounceCalculation() {
    clearTimeout(calculationTimeout);
    calculationTimeout = setTimeout(() => {
        performCalculation(false); // false means it's a real-time calculation, not form submit
    }, 300); // 300ms debounce
}

async function makeApiCall(endpoint, method = 'GET', data = null) {
    try {
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            config.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API request failed');
        }
        
        return result;
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

async function handleCalculate(event) {
    event.preventDefault();
    await performCalculation(true);
}

async function performCalculation(isFormSubmit = true) {
    // Show loading state only for form submits
    if (isFormSubmit) {
        results.classList.add('hidden');
        noResults.classList.add('hidden');
        loading.classList.remove('hidden');
    }
    
    try {
        // Get form data
        const data = {
            delta: parseFloat(document.getElementById('delta').value),
            theta: parseFloat(document.getElementById('theta').value),
            trade_time: parseFloat(document.getElementById('tradeTime').value),
            risk: parseFloat(document.getElementById('risk').value),
            reward: parseFloat(document.getElementById('reward').value),
            entry: parseFloat(document.getElementById('entry').value),
            trade_type: document.getElementById('tradeType').value
        };
        
        // Validate inputs for real-time calculations (be more lenient)
        for (const [key, value] of Object.entries(data)) {
            if (key !== 'trade_type' && (isNaN(value) || value === '')) {
                if (!isFormSubmit) {
                    // For real-time, just show no results if data is incomplete
                    showNoResults();
                    return;
                } else {
                    throw new Error(`Invalid ${key.replace('_', ' ')} value`);
                }
            }
        }
        
        // Make API call
        const result = await makeApiCall('/calculate', 'POST', data);
        
        // Display results
        displayResults(result);
        
        // Calculate position size if we have valid prices
        if (data.entry > 0 && result.results.exit_stop_loss > 0) {
            await calculatePositionSize(data.risk, data.entry, result.results.exit_stop_loss);
        }
        
    } catch (error) {
        if (isFormSubmit) {
            showError('Calculation failed: ' + error.message);
        } else {
            // For real-time calculations, silently fail and show no results
            showNoResults();
        }
    } finally {
        if (isFormSubmit) {
            loading.classList.add('hidden');
        }
    }
}

function displayResults(result) {
    // Update basic results
    tradeDecay.textContent = `$${result.results.trade_decay.toFixed(6)}`;
    riskAmount.textContent = `$${result.results.risk_amount.toFixed(2)}`;
    takeProfit.textContent = `$${result.results.exit_take_profit.toFixed(4)}`;
    stopLoss.textContent = `$${result.results.exit_stop_loss.toFixed(4)}`;
    
    // Display risk validation if available
    if (result.risk_validation) {
        displayRiskValidation(result.risk_validation);
    } else {
        riskValidation.classList.add('hidden');
    }
    
    // Show results
    results.classList.remove('hidden');
}

function displayRiskValidation(validation) {
    const { severity, warning_message, is_valid } = validation;
    
    // Remove existing classes
    riskValidation.className = 'p-4 rounded-lg border-2';
    
    // Add appropriate styling
    switch (severity) {
        case 'error':
            riskValidation.classList.add('risk-error');
            riskValidation.innerHTML = `<i class="fas fa-exclamation-triangle mr-2"></i>${warning_message}`;
            break;
        case 'warning':
            riskValidation.classList.add('risk-warning');
            riskValidation.innerHTML = `<i class="fas fa-exclamation-triangle mr-2"></i>${warning_message}`;
            break;
        default:
            riskValidation.classList.add('risk-success');
            riskValidation.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${warning_message}`;
    }
    
    riskValidation.classList.remove('hidden');
}

async function calculatePositionSize(riskAmount, entryPrice, stopLossPrice) {
    try {
        const data = {
            risk_amount: riskAmount,
            entry_price: entryPrice,
            stop_loss_price: stopLossPrice
        };
        
        const result = await makeApiCall('/position-size', 'POST', data);
        
        if (result.success && result.suggestion) {
            const suggestion = result.suggestion;
            
            positionSizeContent.innerHTML = `
                <div class="grid md:grid-cols-2 gap-4">
                    <div>
                        <div class="text-sm text-blue-600">Suggested Contracts</div>
                        <div class="text-lg font-semibold">${suggestion.suggested_contracts}</div>
                    </div>
                    <div>
                        <div class="text-sm text-blue-600">Risk Per Option</div>
                        <div class="text-lg font-semibold">$${suggestion.risk_per_option.toFixed(2)}</div>
                    </div>
                    <div>
                        <div class="text-sm text-blue-600">Actual Risk</div>
                        <div class="text-lg font-semibold">$${suggestion.actual_risk.toFixed(2)}</div>
                    </div>
                    <div>
                        <div class="text-sm text-blue-600">Max Allowed Risk</div>
                        <div class="text-lg font-semibold">$${suggestion.max_allowed_risk.toFixed(2)}</div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        positionSizeContent.innerHTML = `<div class="text-red-600">Position size calculation failed: ${error.message}</div>`;
    }
}

async function saveConfiguration() {
    try {
        const totalCapital = parseFloat(totalCapitalInput.value);
        const riskPercentage = parseFloat(riskPercentageInput.value);
        
        if (!totalCapital || totalCapital <= 0) {
            throw new Error('Total capital must be a positive number');
        }
        
        if (!riskPercentage || riskPercentage <= 0 || riskPercentage > 100) {
            throw new Error('Risk percentage must be between 0 and 100');
        }
        
        const data = {
            total_capital: totalCapital,
            risk_per_trade_percentage: riskPercentage
        };
        
        const result = await makeApiCall('/config', 'POST', data);
        
        showConfigStatus('Configuration saved successfully!', 'success');
        
    } catch (error) {
        showConfigStatus('Failed to save configuration: ' + error.message, 'error');
    }
}

async function loadConfiguration() {
    try {
        const result = await makeApiCall('/config', 'GET');
        
        if (result.success && result.config) {
            totalCapitalInput.value = result.config.total_capital;
            riskPercentageInput.value = result.config.risk_per_trade_percentage;
            showConfigStatus('Configuration loaded successfully!', 'success');
        }
        
    } catch (error) {
        showConfigStatus('Failed to load configuration: ' + error.message, 'error');
    }
}

function showConfigStatus(message, type) {
    configStatus.className = 'mt-3 p-3 rounded-md text-sm';
    
    if (type === 'success') {
        configStatus.classList.add('bg-green-100', 'text-green-700', 'border', 'border-green-200');
        configStatus.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
    } else {
        configStatus.classList.add('bg-red-100', 'text-red-700', 'border', 'border-red-200');
        configStatus.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
    }
    
    // Clear status after 5 seconds
    setTimeout(() => {
        configStatus.innerHTML = '';
        configStatus.className = 'mt-3';
    }, 5000);
}

function showNoResults() {
    results.classList.add('hidden');
    loading.classList.add('hidden');
    noResults.classList.remove('hidden');
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50';
    errorDiv.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-exclamation-circle mr-2"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-red-500 hover:text-red-700">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentElement) {
            errorDiv.remove();
        }
    }, 5000);
    
    // Show no results state
    showNoResults();
}

// Utility function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}