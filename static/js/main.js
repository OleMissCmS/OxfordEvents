// Oxford Events JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const filterPills = document.querySelectorAll('.filter-pill');
    const allPill = document.querySelector('.filter-pill[data-category="All"]');
    const searchInput = document.getElementById('searchInput');
    const eventCards = document.querySelectorAll('.event-card');
    const eventDescriptions = Array.from(eventCards).map(card => {
        const descriptionEl = card.querySelector('.event-description');
        return descriptionEl ? descriptionEl.textContent.toLowerCase() : '';
    });
    
    const activeCategories = new Set();
    const excludedCategories = new Set();
    
    // Status polling for loading indicator
    const loadingStatus = document.getElementById('loadingStatus');
    const statusText = document.getElementById('statusText');
    let statusPollInterval = null;
    
    // Start polling for status (useful if page loads before events finish)
    function startStatusPolling() {
        // Check status immediately
        checkStatus();
        
        // Then poll every 2 seconds (reduced from 500ms to prevent spam)
        statusPollInterval = setInterval(checkStatus, 2000);
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
    
    function updateAllPillState() {
        if (!allPill) {
            return;
        }
        if (activeCategories.size === 0 && excludedCategories.size === 0) {
            allPill.classList.add('active');
        } else {
            allPill.classList.remove('active');
        }
    }

    function resetFilters() {
        activeCategories.clear();
        excludedCategories.clear();
        filterPills.forEach(pill => {
            pill.classList.remove('active');
            pill.classList.remove('excluded');
        });
        if (allPill) {
            allPill.classList.add('active');
        }
        filterEvents();
    }

    function toggleActiveCategory(category, pill) {
        if (excludedCategories.has(category)) {
            excludedCategories.delete(category);
            pill.classList.remove('excluded');
        }

        if (activeCategories.has(category)) {
            activeCategories.delete(category);
            pill.classList.remove('active');
        } else {
            activeCategories.add(category);
            pill.classList.add('active');
        }
        updateAllPillState();
        filterEvents();
    }

    function toggleExcludedCategory(category, pill) {
        if (excludedCategories.has(category)) {
            excludedCategories.delete(category);
            pill.classList.remove('excluded');
        } else {
            excludedCategories.add(category);
            pill.classList.add('excluded');
            if (activeCategories.has(category)) {
                activeCategories.delete(category);
                pill.classList.remove('active');
            }
        }
        updateAllPillState();
        filterEvents();
    }

    // Filter by category
    filterPills.forEach(pill => {
        const category = pill.getAttribute('data-category');
        const dismiss = pill.querySelector('.pill-dismiss');

        if (category === 'All') {
            pill.addEventListener('click', () => {
                resetFilters();
            });
            return;
        }

        pill.addEventListener('click', () => {
            toggleActiveCategory(category, pill);
        });

        if (dismiss) {
            dismiss.addEventListener('click', (event) => {
                event.stopPropagation();
                toggleExcludedCategory(category, pill);
            });

            dismiss.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    toggleExcludedCategory(category, pill);
                }
            });
        }
    });
    
    // Search functionality
    searchInput.addEventListener('input', function() {
        filterEvents();
    });
    
    function filterEvents() {
        const searchTerm = searchInput.value.trim().toLowerCase();

        eventCards.forEach((card, index) => {
            const cardCategory = card.getAttribute('data-category') || '';
            const title = card.getAttribute('data-title') || '';
            const location = card.getAttribute('data-location') || '';
            const description = eventDescriptions[index] || '';

            const cardCategories = cardCategory.split(',').map(c => c.trim()).filter(Boolean);

            const isExcluded = cardCategories.some(cat => excludedCategories.has(cat));
            if (isExcluded) {
                card.classList.add('hidden');
                return;
            }

            let matchesCategory = true;
            if (activeCategories.size > 0) {
                matchesCategory = cardCategories.some(cat => activeCategories.has(cat));
            }

            let matchesSearch = true;
            if (searchTerm) {
                matchesSearch =
                    title.includes(searchTerm) ||
                    location.includes(searchTerm) ||
                    description.includes(searchTerm);
            }

            if (matchesCategory && matchesSearch) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }
    
    // Initialize - show all events
    resetFilters();
});

