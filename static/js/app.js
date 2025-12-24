// Christmas Planning App - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all event listeners
    initTaskCheckboxes();
    initMilestoneCheckboxes();
    initRolloverCheck();
    initModalDismiss();
    initDragAndDrop();
});

/**
 * Handle task checkbox toggling with AJAX
 */
function initTaskCheckboxes() {
    const taskCheckboxes = document.querySelectorAll('.task-checkbox');

    taskCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async function() {
            const personId = this.dataset.personId;
            const taskType = this.dataset.taskType;
            const isChecked = this.checked;

            try {
                // First, create the task if it doesn't exist (or get existing task ID)
                const createResponse = await fetch(`/tasks/create/${personId}/${taskType}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const createData = await createResponse.json();

                if (!createData.success) {
                    throw new Error('Failed to create task');
                }

                const taskId = createData.task_id;

                // Now toggle the task
                const toggleResponse = await fetch(`/tasks/${taskId}/toggle`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const toggleData = await toggleResponse.json();

                if (!toggleData.success) {
                    throw new Error('Failed to toggle task');
                }

                // Update checkbox state to match server
                this.checked = toggleData.completed;

                // Visual feedback
                const row = this.closest('tr') || this.closest('.list-group-item');
                if (row) {
                    if (toggleData.completed) {
                        row.classList.add('table-success');
                        setTimeout(() => row.classList.remove('table-success'), 500);
                    }
                }

            } catch (error) {
                console.error('Error toggling task:', error);
                // Revert checkbox on error
                this.checked = !isChecked;
                alert('Failed to update task. Please try again.');
            }
        });
    });
}

/**
 * Handle milestone checkbox toggling with AJAX
 */
function initMilestoneCheckboxes() {
    const milestoneCheckboxes = document.querySelectorAll('.milestone-checkbox');

    milestoneCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async function() {
            const milestoneId = this.dataset.milestoneId;
            const isChecked = this.checked;

            try {
                const response = await fetch(`/milestones/${milestoneId}/toggle`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (!data.success) {
                    throw new Error('Failed to toggle milestone');
                }

                // Update checkbox state to match server
                this.checked = data.completed;

                // Visual feedback
                const item = this.closest('.list-group-item');
                if (item) {
                    if (data.completed) {
                        item.classList.add('list-group-item-success');
                    } else {
                        item.classList.remove('list-group-item-success');
                    }
                }

            } catch (error) {
                console.error('Error toggling milestone:', error);
                // Revert checkbox on error
                this.checked = !isChecked;
                alert('Failed to update milestone. Please try again.');
            }
        });
    });
}

/**
 * Check for year rollover on page load
 */
function initRolloverCheck() {
    // Only check on dashboard
    if (!window.location.pathname.includes('/') && window.location.pathname !== '/') {
        return;
    }

    fetch('/api/rollover-check')
        .then(response => response.json())
        .then(data => {
            if (data.rollover_needed) {
                console.log('Year rollover performed:', data.summary);
                // Reload page to show modal
                window.location.reload();
            }
        })
        .catch(error => {
            console.error('Error checking rollover:', error);
        });
}

/**
 * Handle rollover modal dismiss
 */
function initModalDismiss() {
    const modal = document.getElementById('rolloverModal');
    if (!modal) return;

    const dismissButton = modal.querySelector('[data-bs-dismiss="modal"]');
    const backdrop = document.querySelector('.modal-backdrop');

    if (dismissButton) {
        dismissButton.addEventListener('click', function() {
            modal.style.display = 'none';
            if (backdrop) {
                backdrop.remove();
            }
        });
    }
}

/**
 * Quick add gift idea (if form exists)
 */
function quickAddGiftIdea(personId, idea, notes = '') {
    return fetch('/api/quick-add-idea', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            person_id: personId,
            idea: idea,
            notes: notes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || 'Failed to add gift idea');
        }
        return data;
    });
}

/**
 * Confirmation for delete actions
 */
document.addEventListener('click', function(e) {
    if (e.target.matches('[data-confirm]')) {
        const message = e.target.dataset.confirm;
        if (!confirm(message)) {
            e.preventDefault();
            return false;
        }
    }
});

/**
 * Initialize drag and drop for CSV import
 */
function initDragAndDrop() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('csv_file');
    const fileNameDisplay = document.getElementById('fileName');
    const submitBtn = document.getElementById('submitBtn');

    if (!dropZone || !fileInput) return;

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    // Handle click to browse
    dropZone.addEventListener('click', function(e) {
        if (e.target.tagName !== 'LABEL') {
            fileInput.click();
        }
    });

    // Handle file selection via input
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        dropZone.classList.add('drag-over');
    }

    function unhighlight() {
        dropZone.classList.remove('drag-over');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];

            // Check if it's a CSV file
            if (!file.name.endsWith('.csv')) {
                alert('Please select a CSV file');
                return;
            }

            // Update the file input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;

            // Display file name
            fileNameDisplay.textContent = `Selected: ${file.name}`;

            // Enable submit button
            if (submitBtn) {
                submitBtn.disabled = false;
            }
        }
    }
}
