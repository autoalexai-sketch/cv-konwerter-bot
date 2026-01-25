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
            showError(getErrorMessage('wrongFormat'));
            return;
        }
        
        // Check file size (15MB)
        if (file.size > 15 * 1024 * 1024) {
            showError(getErrorMessage('tooLarge'));
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
    
    const file = fileInput.files[0];
    if (!file) {
        showError(getErrorMessage('noFile'));
        return;
    }
    
    // Show progress bar
    progressBar.classList.remove('hidden');
    progressFill.style.width = '0%';
    convertBtn.disabled = true;
    
    // Use translated "Converting..." text
    const convertingText = getNestedTranslation(translations, 'convert.converting') || 'Konwersja...';
    convertBtn.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i> ${convertingText}`;
    
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
            console.log('✅ Response OK, creating blob...');
            const blob = await response.blob();
            console.log('✅ Blob created:', blob.size, 'bytes, type:', blob.type);
            
            const url = window.URL.createObjectURL(blob);
            console.log('✅ Object URL created:', url);
            
            const pdfFilename = file.name.replace(/\.(doc|docx)$/i, '.pdf');
            
            downloadLink.href = url;
            downloadLink.download = pdfFilename;
            console.log('✅ Download link set:', downloadLink.href);
            console.log('✅ Download filename:', downloadLink.download);
            
            // Show result section first
            result.classList.remove('hidden');
            progressBar.classList.add('hidden');
            
            // Try automatic download with a small delay
            console.log('🚀 Triggering automatic download...');
            setTimeout(() => {
                try {
                    // Create a temporary link and click it
                    const tempLink = document.createElement('a');
                    tempLink.href = url;
                    tempLink.download = pdfFilename;
                    tempLink.style.display = 'none';
                    document.body.appendChild(tempLink);
                    tempLink.click();
                    document.body.removeChild(tempLink);
                    console.log('✅ Automatic download triggered successfully');
                } catch (err) {
                    console.error('❌ Automatic download failed:', err);
                    console.log('ℹ️ Please click the "Download PDF" button manually');
                }
            }, 100);
        } else {
            console.error('❌ Response not OK:', response.status);
            const errorData = await response.json();
            showError(errorData.error || getErrorMessage('conversionFailed'));
        }
    } catch (err) {
        showError(getErrorMessage('serverError'));
        console.error('Error:', err);
    } finally {
        convertBtn.disabled = false;
        const buttonText = getNestedTranslation(translations, 'convert.button') || 'Konwertuj do PDF';
        convertBtn.innerHTML = `<i class="fas fa-magic mr-2"></i> ${buttonText}`;
    }
});

function showError(message) {
    errorMessage.textContent = message;
    error.classList.remove('hidden');
    progressBar.classList.add('hidden');
    convertBtn.disabled = false;
    
    // Use translated button text
    const buttonText = getNestedTranslation(translations, 'convert.button') || 'Konwertuj do PDF';
    convertBtn.innerHTML = `<i class="fas fa-magic mr-2"></i> ${buttonText}`;
}

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});
