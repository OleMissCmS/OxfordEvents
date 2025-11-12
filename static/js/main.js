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

    // Date filtering elements
    const dateFilterWarning = document.getElementById('dateFilterWarning');
    const dateFilterStatus = document.getElementById('dateFilterStatus');
    const dateRangeStart = document.getElementById('dateRangeStart');
    const dateRangeEnd = document.getElementById('dateRangeEnd');
    const threeWeekWindowMs = 21 * 24 * 60 * 60 * 1000;
    let dateStatusTimer = null;
    const pillSelectors = document.querySelectorAll('.pill-selector');
    
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
                        loadingStatus.classList.remove('hidden');
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
                        loadingStatus.style.display = '';
                        loadingStatus.classList.add('hidden');
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

    // Hide Ole Miss logo placeholder if it fails to load
    document.querySelectorAll('.ole-miss-logo').forEach((logo) => {
        logo.addEventListener('error', () => {
            logo.classList.add('hidden');
        });
    });
    
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

    function isBeyondWindow(dateFilter) {
        if (!dateFilter || dateFilter.type === 'none' || !dateFilter.selectedDates.length) {
            return false;
        }
        const cutoff = Date.now() + threeWeekWindowMs;
        return dateFilter.selectedDates.some(dateObj => dateObj && dateObj.getTime() > cutoff);
    }

    function indicateDateCollection() {
        if (!dateFilterStatus) {
            return;
        }
        const dateFilter = getActiveDateFilter();
        const beyondWindow = isBeyondWindow(dateFilter);
        if (!beyondWindow) {
            if (dateStatusTimer) {
                clearTimeout(dateStatusTimer);
            }
            dateFilterStatus.textContent = '';
            dateFilterStatus.classList.add('hidden');
            return;
        }
        if (dateStatusTimer) {
            clearTimeout(dateStatusTimer);
        }
        dateFilterStatus.classList.remove('hidden');
        dateFilterStatus.textContent = 'Collecting extended happenings...';
        dateStatusTimer = setTimeout(() => {
            dateFilterStatus.textContent = 'Extended happenings ready.';
        }, 1400);
    }

    function parseDateValue(value, endOfDay = false) {
        if (!value) {
            return null;
        }
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) {
            return null;
        }
        if (endOfDay) {
            parsed.setHours(23, 59, 59, 999);
        } else {
            parsed.setHours(0, 0, 0, 0);
        }
        return parsed;
    }

    function getActiveDateFilter() {
        const start = parseDateValue(dateRangeStart?.value, false);
        const end = parseDateValue(dateRangeEnd?.value, true);

        if (!start && !end) {
            return { type: 'none', selectedDates: [] };
        }

        return { type: 'range', start, end, selectedDates: [start, end].filter(Boolean) };
    }

    function updateDateWarning(dateFilter) {
        if (!dateFilterWarning) {
            return;
        }
        if (!dateFilter || dateFilter.type === 'none' || !dateFilter.selectedDates.length) {
            dateFilterWarning.classList.add('hidden');
            return;
        }
        const beyondWindow = isBeyondWindow(dateFilter);
        if (beyondWindow) {
            dateFilterWarning.classList.remove('hidden');
        } else {
            dateFilterWarning.classList.add('hidden');
        }
    }

    function matchesDateFilter(eventIso, dateFilter) {
        if (!dateFilter || dateFilter.type === 'none') {
            return true;
        }
        if (!eventIso) {
            return false;
        }
        const eventDate = new Date(eventIso);
        if (Number.isNaN(eventDate.getTime())) {
            return true;
        }

        if (!dateFilter.start && !dateFilter.end) {
            return true;
        }
        if (dateFilter.start && eventDate.getTime() < dateFilter.start.getTime()) {
            return false;
        }
        if (dateFilter.end && eventDate.getTime() > dateFilter.end.getTime()) {
            return false;
        }
        return true;
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
    
    // Date filter interactions
    ['change', 'input'].forEach(evt => {
        if (dateRangeStart) {
            dateRangeStart.addEventListener(evt, () => {
                indicateDateCollection();
                filterEvents();
            });
        }
        if (dateRangeEnd) {
            dateRangeEnd.addEventListener(evt, () => {
                indicateDateCollection();
                filterEvents();
            });
        }
    });

    pillSelectors.forEach(selector => {
        const inputId = selector.getAttribute('data-input');
        const input = document.getElementById(inputId);
        if (!input) {
            return;
        }

        selector.addEventListener('click', event => {
            const button = event.target.closest('.pill-selector-pill');
            if (!button) {
                return;
            }
            event.preventDefault();
            const value = button.getAttribute('data-value');
            const currentCategories = input.value ? input.value.split(',').map(c => c.trim()).filter(Boolean) : [];
            const index = currentCategories.indexOf(value);
            if (index >= 0) {
                currentCategories.splice(index, 1);
                button.classList.remove('selected');
            } else {
                currentCategories.push(value);
                button.classList.add('selected');
            }
            input.value = currentCategories.join(', ');
        });
    });
    
    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterEvents();
        });
    }
    
    function filterEvents() {
        const searchTerm = (searchInput ? searchInput.value.trim().toLowerCase() : '');
        const dateFilter = getActiveDateFilter();
        updateDateWarning(dateFilter);

        eventCards.forEach((card, index) => {
            const cardCategory = card.getAttribute('data-category') || '';
            const title = card.getAttribute('data-title') || '';
            const location = card.getAttribute('data-location') || '';
            const description = eventDescriptions[index] || '';
            const eventStartIso = card.getAttribute('data-start') || '';

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

            const matchesDate = matchesDateFilter(eventStartIso, dateFilter);

            if (matchesCategory && matchesSearch && matchesDate) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }
    
    // Initialize - show all events
    resetFilters();
});

