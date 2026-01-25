// i18n.js - Internationalization support

let currentLang = 'pl'; // Default language
let translations = {};

// Load translation file
async function loadTranslation(lang) {
    try {
        const response = await fetch(`/static/translations/${lang}.json`);
        if (!response.ok) {
            throw new Error(`Translation file not found: ${lang}.json`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error loading translation:', error);
        // Fallback to Polish
        if (lang !== 'pl') {
            return await loadTranslation('pl');
        }
        return {};
    }
}

// Apply translations to the page
function applyTranslations() {
    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = getNestedTranslation(translations, key);
        
        if (translation) {
            // Update text content or attribute
            if (element.tagName === 'META') {
                element.setAttribute('content', translation);
            } else if (element.tagName === 'TITLE') {
                document.title = translation;
            } else {
                element.textContent = translation;
            }
        }
    });
    
    // Update Premium features lists
    updateFeaturesList('freeFeatures', translations.premium?.free?.features || []);
    updateFeaturesList('premiumFeatures', translations.premium?.paid?.features || []);
    
    // Update language buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-lang') === currentLang) {
            btn.classList.add('active');
        }
    });
    
    // Update HTML lang attribute
    document.documentElement.lang = currentLang;
}

// Helper function to get nested translation
function getNestedTranslation(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
}

// Update features list
function updateFeaturesList(elementId, features) {
    const list = document.getElementById(elementId);
    if (!list || !features.length) return;
    
    list.innerHTML = features.map(feature => 
        `<li class="flex items-center"><i class="fas fa-check ${elementId === 'freeFeatures' ? 'text-green-500' : ''} mr-2"></i> ${feature}</li>`
    ).join('');
}

// Set language
async function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('preferredLanguage', lang);
    translations = await loadTranslation(lang);
    applyTranslations();
}

// Detect user language
function detectLanguage() {
    // Check localStorage first
    const savedLang = localStorage.getItem('preferredLanguage');
    if (savedLang && ['pl', 'en', 'uk'].includes(savedLang)) {
        return savedLang;
    }
    
    // Detect browser language
    const browserLang = navigator.language || navigator.userLanguage;
    const langCode = browserLang.split('-')[0].toLowerCase();
    
    // Map browser language to supported languages
    const langMap = {
        'pl': 'pl',
        'en': 'en',
        'uk': 'uk',
        'ru': 'uk', // Russian speakers likely in Ukraine/Poland
    };
    
    return langMap[langCode] || 'pl'; // Default to Polish
}

// Get translated error message
function getErrorMessage(errorKey) {
    return getNestedTranslation(translations, `convert.error.${errorKey}`) || 
           translations.convert?.error?.serverError || 
           'Error occurred';
}

// Initialize i18n on page load
document.addEventListener('DOMContentLoaded', async () => {
    const detectedLang = detectLanguage();
    await setLanguage(detectedLang);
});
