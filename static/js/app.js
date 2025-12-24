// Christmas Planning App - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all event listeners
    initTaskCheckboxes();
    initMilestoneCheckboxes();
    initRolloverCheck();
    initModalDismiss();
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
