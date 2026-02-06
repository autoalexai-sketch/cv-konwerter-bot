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
            
            // ❌ УДАЛЕНА АВТОМАТИЧЕСКАЯ ЗАГРУЗКА
            
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

// ✅ ИСПРАВЛЕННЫЙ ОБРАБОТЧИК НАВИГАЦИИ (без ошибки в строке 192)
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        if (targetId && targetId !== '#') {
            const target = document.querySelector(targetId);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});
