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
        
        if (!file.name.endsWith('.doc') && !file.name.endsWith('.docx')) {
            showError('Nieprawidłowy format pliku. Tylko .doc lub .docx');
            return;
        }
        
        if (file.size > 15 * 1024 * 1024) {
            showError('Plik jest zbyt duży (maks. 15 MB)');
            return;
        }
        
        fileName.textContent = `📄 ${file.name}`;
        fileName.classList.remove('hidden');
        convertBtn.disabled = false;
        result.classList.add('hidden');
        error.classList.add('hidden');
    }
}

// Handle form submission (БЕЗ АВТО-ЗАГРУЗКИ!)
uploadForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (rodoConsent && !rodoConsent.checked) {
        showError('Proszę zaakceptować politykę prywatności RODO');
        return;
    }
    
    const file = fileInput.files[0];
    if (!file) {
        showError('Proszę wybrać plik');
        return;
    }
    
    progressBar.classList.remove('hidden');
    progressFill.style.width = '0%';
    convertBtn.disabled = true;
    convertBtn.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i> Konwertuję...`;
    result.classList.add('hidden');
    error.classList.add('hidden');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
            }
        }, 200);
        
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
            
            // ✅ ТОЛЬКО УСТАНАВЛИВАЕМ ССЫЛКУ (НЕ АВТО-ЗАГРУЗКА!)
            downloadLink.href = url;
            downloadLink.download = pdfFilename;
            
            // ✅ ПОКАЗЫВАЕМ КНОПКУ
            result.classList.remove('hidden');
            progressBar.classList.add('hidden');
            
            // ❌ НЕТ КОДА АВТО-ЗАГРУЗКИ!
            
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
        const href = this.getAttribute('href');
        // Проверяем, что это якорь (#), а не blob URL
        if (href && href.startsWith('#') && href !== '#') {
            e.preventDefault();
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
    // Найти кнопку "Dalej" на шаге 1
    const nextButton = document.querySelector('button[type="submit"], .btn-next, [onclick*="next"]');
    
    if (nextButton) {
        nextButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            let isValid = true;
            const lang = localStorage.getItem('language') || 'pl';
            
            // Сброс ошибок
            document.querySelectorAll('.form-error').forEach(el => el.remove());
            
            // Проверка обязательных полей (адаптируй под реальные ID полей!)
            const requiredFields = [
                { id: 'name', label: 'Imię' },
                { id: 'email', label: 'Email' },
                { id: 'city', label: 'Miasto' }
            ];
            
            requiredFields.forEach(field => {
                const input = document.getElementById(field.id) || 
                              document.querySelector(`[name="${field.id}"]`);
                
                if (input) {
                    const value = input.value.trim();
                    
                    if (!value) {
                        showErrorBelow(input, 'Pole wymagane');
                        isValid = false;
                    }
                    
                    // Валидация email
                    if (field.id === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                        showErrorBelow(input, 'Nieprawidłowy email');
                        isValid = false;
                    }
                }
            });
            
            // Если все поля заполнены — отправляем форму
            if (isValid) {
                const form = nextButton.closest('form');
                if (form) {
                    form.submit();
                } else {
                    // Или переход на следующий шаг
                    console.log('✅ Все поля заполнены, переход на шаг 2/5');
                }
            }
        });
    }
    
    function showErrorBelow(input, message) {
        // Удаляем старые ошибки
        const existing = input.parentElement.querySelector('.form-error');
        if (existing) existing.remove();
        
        // Создаем новый элемент ошибки
        const error = document.createElement('div');
        error.className = 'form-error text-red-500 text-sm mt-1';
        error.textContent = message;
        error.style.marginTop = '4px';
        error.style.fontSize = '14px';
        
        // Вставляем после поля ввода
        input.parentElement.insertBefore(error, input.nextSibling);
        
        // Подсвечиваем поле
        input.style.borderColor = '#ef4444';
        
        // Скрываем ошибку при фокусе
        input.addEventListener('focus', () => {
            error.remove();
            input.style.borderColor = '';
        }, { once: true });
    }
});
