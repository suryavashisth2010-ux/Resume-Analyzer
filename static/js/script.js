const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('resume');
const fileNameDisplay = document.getElementById('fileNameDisplay');
const uploadForm = document.getElementById('uploadForm');
const resultCard = document.getElementById('resultCard');
const atsScore = document.getElementById('atsScore');
const scoreCircle = document.getElementById('scoreCircle');
const summaryText = document.getElementById('summaryText');
const skillsContainer = document.getElementById('skillsContainer');
const improvementsList = document.getElementById('improvementsList');
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
            // Update ATS Score
            const score = data.ats_score || 0;
            atsScore.textContent = score;
            scoreCircle.style.setProperty('--score-percent', `${score}%`);

            // Set circle color based on score
            if (score > 80) scoreCircle.style.setProperty('--success', '#10b981');
            else if (score > 50) scoreCircle.style.setProperty('--success', '#f59e0b');
            else scoreCircle.style.setProperty('--success', '#ef4444');

            // Update Summary
            summaryText.textContent = data.summary;

            // Update Skills
            skillsContainer.innerHTML = '';
            (data.skills || []).forEach(skill => {
                const tag = document.createElement('span');
                tag.className = 'skill-tag';
                tag.textContent = skill;
                skillsContainer.appendChild(tag);
            });

            // Update Improvements
            improvementsList.innerHTML = '';
            (data.improvements || []).forEach(tip => {
                const item = document.createElement('div');
                item.className = 'improvement-item';
                item.textContent = tip;
                improvementsList.appendChild(item);
            });

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

    // Clear dynamic fields
    atsScore.textContent = '0';
    scoreCircle.style.setProperty('--score-percent', '0%');
    summaryText.textContent = '';
    skillsContainer.innerHTML = '';
    improvementsList.innerHTML = '';
}
