
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('resume');
const fileNameDisplay = document.getElementById('fileNameDisplay');
const uploadForm = document.getElementById('uploadForm');
const resultCard = document.getElementById('resultCard');
const feedbackContent = document.getElementById('feedbackContent');
const loader = document.getElementById('loader');
const jobTypeInput = document.getElementById('jobType');
const loaderMessage = document.getElementById('loaderMessage');

// File Selection
dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        fileNameDisplay.textContent = `Selected: ${fileInput.files[0].name}`;
        dropZone.style.borderColor = "#6366f1";
    }
});

// Drag and Drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    fileInput.files = e.dataTransfer.files;
    if (fileInput.files.length > 0) {
        fileNameDisplay.textContent = `Selected: ${fileInput.files[0].name}`;
    }
});

// Form Submission
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append('resume', fileInput.files[0]);
    formData.append('jobType', jobTypeInput.value);

    loader.classList.remove('hidden');
    uploadForm.parentElement.classList.add('hidden');

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            feedbackContent.innerHTML = data.feedback;
            resultCard.classList.remove('hidden');
        } else {
            alert(`Error: ${data.error}`);
            resetApp();
        }
    } catch (err) {
        alert('Failed to connect to server.');
        resetApp();
    } finally {
        loader.classList.add('hidden');
    }
});

function resetApp() {
    resultCard.classList.add('hidden');
    uploadForm.parentElement.classList.remove('hidden');
    uploadForm.reset();
    fileNameDisplay.textContent = "Drag and drop your PDF resume here or click to browse";
    dropZone.style.borderColor = "rgba(255, 255, 255, 0.15)";
}
