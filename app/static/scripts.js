document.addEventListener('DOMContentLoaded', function() {
    // Optional: Add some dynamic interactions
    const completeForms = document.querySelectorAll('form[action*="complete_todo"]');
    
    completeForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const confirmed = confirm('Are you sure you want to mark this todo as complete?');
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });
});