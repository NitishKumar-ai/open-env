document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const elements = {
        badgeDifficulty: document.getElementById('badge-difficulty'),
        badgeStep: document.getElementById('badge-step'),
        taskDescription: document.getElementById('task-description'),
        codeSnippet: document.getElementById('code-snippet'),
        langBadge: document.getElementById('lang-badge'),
        feedbackContainer: document.getElementById('feedback-container'),
        previousFeedback: document.getElementById('previous-feedback'),
        
        form: document.getElementById('action-form'),
        submitBtn: document.getElementById('btn-submit-action'),
        resetBtn: document.getElementById('btn-reset-env'),
        
        toast: document.getElementById('reward-toast'),
        toastTitle: document.getElementById('toast-title'),
        toastMessage: document.getElementById('toast-message'),
        toastClose: document.getElementById('toast-close'),

        // Inputs
        inputBugIdentified: document.getElementById('input-bug-identified'),
        inputBugType: document.getElementById('input-bug-type'),
        inputSeverity: document.getElementById('input-severity'),
        inputBugLocation: document.getElementById('input-bug-location'),
        inputBugDescription: document.getElementById('input-bug-description'),
        inputSuggestedFix: document.getElementById('input-suggested-fix'),
        
        // Tab elements
        tabs: document.querySelectorAll('.mac-tab'),
        panes: document.querySelectorAll('.tab-pane')
    };

    let isDone = false;

    // Tab Switching Logic
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');
            
            // Update tabs
            elements.tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update panes
            elements.panes.forEach(pane => {
                if (pane.id === `tab-${target}`) {
                    pane.classList.add('active');
                } else {
                    pane.classList.remove('active');
                }
            });
        });
    });

    // Initialize Environment
    async function resetEnvironment(difficulty = 'easy') {
        elements.submitBtn.disabled = true;
        elements.resetBtn.disabled = true;
        isDone = false;
        
        try {
            const res = await fetch(`/reset?difficulty=${difficulty}`, { method: 'POST' });
            if (!res.ok) throw new Error('Failed to reset environment');
            const data = await res.json();
            updateObservation(data.observation);
            
            // clear form
            elements.form.reset();
            document.getElementById('observation-section').classList.remove('environment-done');
            hideToast();
        } catch (e) {
            showToast('Error', e.message, true);
        } finally {
            elements.submitBtn.disabled = false;
            elements.resetBtn.disabled = false;
        }
    }

    function updateObservation(obs) {
        elements.badgeDifficulty.textContent = obs.difficulty.toUpperCase();
        elements.badgeStep.textContent = `Step ${obs.step_number}/${obs.max_steps}`;
        elements.taskDescription.textContent = obs.task_description;
        elements.langBadge.textContent = `Language: ${obs.language}`;
        
        // Update code block and highlight
        elements.codeSnippet.textContent = obs.code_snippet;
        elements.codeSnippet.className = `language-${obs.language}`;
        hljs.highlightElement(elements.codeSnippet);

        if (obs.previous_feedback) {
            elements.previousFeedback.textContent = obs.previous_feedback;
            elements.feedbackContainer.classList.remove('hidden');
        } else {
            elements.feedbackContainer.classList.add('hidden');
        }
        
        if (obs.step_number >= obs.max_steps) {
            isDone = true;
        }
    }

    // Submit Step
    elements.form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (isDone) {
            showToast('Environment Finished', 'Please reset to start a new episode.', true);
            return;
        }

        const action = {
            bug_identified: elements.inputBugIdentified.value === 'true',
            bug_location: elements.inputBugLocation.value,
            bug_type: elements.inputBugType.value,
            bug_description: elements.inputBugDescription.value,
            severity: elements.inputSeverity.value,
            suggested_fix: elements.inputSuggestedFix.value
        };

        elements.submitBtn.disabled = true;
        elements.submitBtn.textContent = "Submitting...";

        try {
            const res = await fetch('/step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(action)
            });
            
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to submit action');
            }

            const data = await res.json();
            updateObservation(data.observation);
            
            if (data.done) {
                isDone = true;
                const totalScore = data.info?.total_score || data.reward;
                showToast('Episode Completed!', `Final Score: ${totalScore.toFixed(2)}`, false);
                document.getElementById('observation-section').classList.add('environment-done');
            } else {
                showToast('Step Evaluated', `Step Reward: ${data.reward.toFixed(2)}`, false);
            }
        } catch (e) {
            showToast('Action Failed', e.message, true);
        } finally {
            elements.submitBtn.disabled = false;
            elements.submitBtn.textContent = "Submit Action";
        }
    });

    // Reset button
    elements.resetBtn.addEventListener('click', () => {
        const randomDifficulty = ['easy', 'medium', 'hard'][Math.floor(Math.random() * 3)];
        resetEnvironment(randomDifficulty);
    });

    // Toast functionality
    let toastTimeout;
    function showToast(title, message, isError = false) {
        elements.toastTitle.textContent = title;
        elements.toastMessage.textContent = message;
        elements.toastMessage.style.color = isError ? 'var(--error)' : 'var(--success)';
        elements.toast.classList.remove('hidden');
        
        clearTimeout(toastTimeout);
        toastTimeout = setTimeout(hideToast, 4000);
    }

    function hideToast() {
        elements.toast.classList.add('hidden');
    }

    elements.toastClose.addEventListener('click', hideToast);

    // Initial Load
    resetEnvironment();
});
