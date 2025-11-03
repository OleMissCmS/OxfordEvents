// Oxford Events JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const filterPills = document.querySelectorAll('.filter-pill');
    const searchInput = document.getElementById('searchInput');
    const eventCards = document.querySelectorAll('.event-card');
    
    // Status polling for loading indicator
    const loadingStatus = document.getElementById('loadingStatus');
    const statusText = document.getElementById('statusText');
    let statusPollInterval = null;
    
    // Start polling for status (useful if page loads before events finish)
    function startStatusPolling() {
        // Check status immediately
        checkStatus();
        
        // Then poll every 500ms
        statusPollInterval = setInterval(checkStatus, 500);
    }
    
    function checkStatus() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                // Show status if loading, hide if complete/unknown
                if (data.status === 'loading' && data.step !== undefined && data.total_steps !== undefined) {
                    // Show status with step counter
                    if (loadingStatus) {
                        loadingStatus.style.display = 'block';
                    }
                    if (statusText) {
                        let stepText = '';
                        if (data.step > 0 && data.total_steps > 0) {
                            stepText = `<span class="status-step">Step ${data.step} of ${data.total_steps}:</span> `;
                        }
                        const message = data.message || 'Loading...';
                        const details = data.details ? ` (${data.details})` : '';
                        statusText.innerHTML = stepText + message + details;
                    }
                } else {
                    // Loading complete or unknown, hide status
                    if (loadingStatus) {
                        loadingStatus.style.display = 'none';
                    }
                    if (statusPollInterval) {
                        clearInterval(statusPollInterval);
                        statusPollInterval = null;
                    }
                }
            })
            .catch(error => {
                // Silently fail - status checking is non-critical
                console.debug('Status check failed:', error);
            });
    }
    
    // Start polling on page load
    startStatusPolling();
    
    // Also check status when page becomes visible (in case tab was inactive)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden && !statusPollInterval) {
            startStatusPolling();
        }
    });
    
    // Filter by category
    filterPills.forEach(pill => {
        pill.addEventListener('click', function() {
            // Toggle active state - if already active, turn it off
            const wasActive = this.classList.contains('active');
            filterPills.forEach(p => p.classList.remove('active'));
            
            if (!wasActive) {
                // Was not active, make it active
                this.classList.add('active');
                const category = this.getAttribute('data-category');
                filterEvents(category, searchInput.value);
            } else {
                // Was active, show all
                filterEvents('All', searchInput.value);
            }
        });
    });
    
    // Search functionality
    searchInput.addEventListener('input', function() {
        const activePill = document.querySelector('.filter-pill.active');
        const category = activePill ? activePill.getAttribute('data-category') : 'All';
        filterEvents(category, this.value);
    });
    
    function filterEvents(category, searchTerm) {
        eventCards.forEach(card => {
            const cardCategory = card.getAttribute('data-category');
            const title = card.getAttribute('data-title');
            const location = card.getAttribute('data-location');
            
            // Category filter
            const categoryMatch = category === 'All' || cardCategory === category;
            
            // Search filter
            const searchMatch = !searchTerm || 
                              title.includes(searchTerm.toLowerCase()) || 
                              location.includes(searchTerm.toLowerCase());
            
            // Show/hide card
            if (categoryMatch && searchMatch) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }
    
    // Initialize - show all events
    filterEvents('All', '');
});

