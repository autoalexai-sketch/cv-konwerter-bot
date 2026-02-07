// Drag and drop functionality
const dropArea = document.getElementById('dropArea');
const fileInput = document.getElementById('fileInput');
const uploadForm = document.getElementById('uploadForm');
const fileName = document.getElementById('fileName');
const progressBar = document.getElementById('progressBar');
const progressFill = document.getElementById('progressFill');
const convertBtn = document.getElementById('convertBtn');
const result = document.getElementById('result');
const error = document.getElementById('error');
const downloadLink = document.getElementById('downloadLink');
const errorMessage = document.getElementById('errorMessage');
const rodoConsent = document.getElementById('rodo_consent');

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight drop area when item is dragged over it
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => {
        dropArea.classList.add('dragover');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => {
        dropArea.classList.remove('dragover');
    }, false);
});

// Handle dropped files
dropArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    fileInput.files = files;
    handleFiles(files);
}

// Handle file selection via input
fileInput.addEventListener('change', function() {
    handleFiles(this.files);
});

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        
        // Check file type
        if (!file.name.endsWith('.doc') && !file.name.endsWith('.docx')) {
            showError('Nieprawidłowy format pliku. Tylko .doc lub .docx');
            return;
        }
        
        // Check file size (15MB)
        if (file.size > 15 * 1024 * 1024) {
            showError('Plik jest zbyt duży (maks. 15 MB)');
            return;
        }
        
        fileName.textContent = `📄 ${file.name}`;
        fileName.classList.remove('hidden');
        convertBtn.disabled = false;
        
        // Hide previous results
        result.classList.add('hidden');
        error.classList.add('hidden');
    }
}

// Handle form submission
uploadForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // ✅ ПРОВЕРКА СОГЛАСИЯ RODO
    if (rodoConsent && !rodoConsent.checked) {
        showError('Proszę zaakceptować politykę prywatności RODO');
        return;
    }
    
    const file = fileInput.files[0];
    if (!file) {
        showError('Proszę wybrać plik');
        return;
    }
    
    // Show progress bar
    progressBar.classList.remove('hidden');
    progressFill.style.width = '0%';
    convertBtn.disabled = true;
    convertBtn.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i> Konwertuję...`;
    
    // Hide previous results
    result.classList.add('hidden');
    error.classList.add('hidden');
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
            }
        }, 200);
        
        // Upload file
        const response = await fetch('/convert', {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const pdfFilename = file.name.replace(/\.(doc|docx)$/i, '.pdf');
            
            // ✅ УСТАНАВЛИВАЕМ ССЫЛКУ НА КНОПКУ (НЕ АВТОЗАГРУЗКУ!)
            downloadLink.href = url;
            downloadLink.download = pdfFilename;
            
            // ✅ ПОКАЗЫВАЕМ КНОПКУ "POBIERZ PDF"
            result.classList.remove('hidden');
            progressBar.classList.add('hidden');
            
        } else {
            const errorData = await response.json();
            showError(errorData.error || 'Błąd konwersji');
        }
    } catch (err) {
        showError('Błąd połączenia z serwerem');
        console.error('Error:', err);
    } finally {
        convertBtn.disabled = false;
        convertBtn.innerHTML = `<i class="fas fa-magic mr-2"></i> Konwertuj do PDF`;
    }
});

function showError(message) {
    errorMessage.textContent = message;
    error.classList.remove('hidden');
    progressBar.classList.add('hidden');
    convertBtn.disabled = false;
    convertBtn.innerHTML = `<i class="fas fa-magic mr-2"></i> Konwertuj do PDF`;
}

// ✅ ИСПРАВЛЕННЫЙ ОБРАБОТЧИК НАВИГАЦИИ (без ошибки blob:)
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const href = this.getAttribute('href');
        
        // Проверяем, что это якорь (#), а не blob URL
        if (href && href.startsWith('#') && href !== '#') {
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// ✅ ВАЛИДАЦИЯ ФОРМЫ ШАГА 1/5
document.addEventListener('DOMContentLoaded', () => {
    const nextButton = document.querySelector('[data-step="1"] .next-btn');
    
    if (nextButton) {
        nextButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            let isValid = true;
            const lang = localStorage.getItem('language') || 'pl';
            
            // Сброс ошибок
            document.querySelectorAll('.form-error').forEach(el => el.remove());
            
            // Проверка обязательных полей
            const requiredFields = [
                { id: 'first_name', type: 'text', label: getTranslation('form.step1.name', lang) },
                { id: 'last_name', type: 'text', label: getTranslation('form.step1.surname', lang) },
                { id: 'email', type: 'email', label: getTranslation('form.step1.email', lang) },
                { id: 'phone', type: 'tel', label: getTranslation('form.step1.phone', lang) },
                { id: 'city', type: 'text', label: getTranslation('form.step1.city', lang) }
            ];
            
            requiredFields.forEach(field => {
                const input = document.getElementById(field.id);
                if (input) {
                    const value = input.value.trim();
                    
                    // Проверка на пустое поле
                    if (!value) {
                        showErrorBelow(input, getTranslation('form.required', lang));
                        isValid = false;
                        return;
                    }
                    
                    // Валидация email
                    if (field.id === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                        showErrorBelow(input, getTranslation('form.invalid_email', lang));
                        isValid = false;
                        return;
                    }
                    
                    // Валидация телефона (минимум 9 цифр)
                    if (field.id === 'phone' && !/^\+?\d{9,}$/.test(value.replace(/\D/g, ''))) {
                        showErrorBelow(input, getTranslation('form.invalid_phone', lang));
                        isValid = false;
                        return;
                    }
                }
            });
            
            // Если все поля заполнены правильно — переходим на следующий шаг
            if (isValid) {
                console.log('✅ All fields valid, moving to step 2/5');
                // Здесь будет код перехода на шаг 2/5
            }
        });
    }
    
    function showErrorBelow(input, message) {
        // Удаляем старые ошибки
        const existingError = input.parentElement.querySelector('.form-error');
        if (existingError) existingError.remove();
        
        // Создаем новый элемент ошибки
        const error = document.createElement('div');
        error.className = 'form-error text-red-500 text-sm mt-1';
        error.textContent = message;
        input.classList.add('border-red-500');
        input.parentElement.appendChild(error);
        
        // Скрываем ошибку при фокусе на поле
        input.addEventListener('focus', () => {
            error.remove();
            input.classList.remove('border-red-500');
        });
    }
    
    // Функция получения перевода
    function getTranslation(key, lang = 'pl') {
        const translations = {
            pl: {
                'form.required': 'Pole wymagane',
                'form.invalid_email': 'Nieprawidłowy adres email',
                'form.invalid_phone': 'Nieprawidłowy numer telefonu (min. 9 cyfr)'
            },
            en: {
                'form.required': 'Required field',
                'form.invalid_email': 'Invalid email address',
                'form.invalid_phone': 'Invalid phone number (min. 9 digits)'
            },
            uk: {
                'form.required': 'Обов\'язкове поле',
                'form.invalid_email': 'Неправильна адреса email',
                'form.invalid_phone': 'Неправильний номер телефону (мін. 9 цифр)'
            }
        };
        
        return translations[lang]?.[key] || translations['pl'][key] || key;
    }
});
