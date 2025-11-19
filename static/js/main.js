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

// ===== NEW FEATURES =====

// Carousel Functionality
(function() {
    const slides = document.querySelectorAll('.carousel-slide');
    const indicators = document.querySelectorAll('.indicator');
    let currentSlide = 0;
    
    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.toggle('active', i === index);
        });
        indicators.forEach((indicator, i) => {
            indicator.classList.toggle('active', i === index);
        });
    }
    
    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }
    
    // Auto-advance carousel
    if (slides.length > 0) {
        setInterval(nextSlide, 5000);
        
        // Click indicators to navigate
        indicators.forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                currentSlide = index;
                showSlide(currentSlide);
            });
        });
    }
})();

// Advanced Filters
(function() {
    const advancedFiltersBtn = document.getElementById('advancedFiltersBtn');
    const advancedFiltersPanel = document.getElementById('advancedFiltersPanel');
    const locationFilter = document.getElementById('locationFilter');
    const priceFilter = document.getElementById('priceFilter');
    const accessibilityFilter = document.getElementById('accessibilityFilter');
    const sortBy = document.getElementById('sortBy');
    
    if (advancedFiltersBtn && advancedFiltersPanel) {
        advancedFiltersBtn.addEventListener('click', () => {
            advancedFiltersPanel.classList.toggle('hidden');
            const isOpen = !advancedFiltersPanel.classList.contains('hidden');
            advancedFiltersBtn.textContent = isOpen ? 'Hide Filters' : 'Advanced Filters';
        });
    }
    
    // Apply filters when changed
    [locationFilter, priceFilter, accessibilityFilter, sortBy].forEach(filter => {
        if (filter) {
            filter.addEventListener('change', () => {
                // Call the existing filterEvents function from the main scope
                if (typeof window.filterEvents === 'function') {
                    window.filterEvents();
                } else {
                    // Fallback: trigger the existing filterEvents from DOMContentLoaded scope
                    const searchInput = document.getElementById('searchInput');
                    if (searchInput) {
                        searchInput.dispatchEvent(new Event('input'));
                    }
                }
            });
        }
    });
})();

// View Toggle (List/Calendar)
(function() {
    const listViewBtn = document.getElementById('listViewBtn');
    const calendarViewBtn = document.getElementById('calendarViewBtn');
    const eventsGrid = document.getElementById('eventsGrid');
    const calendarView = document.getElementById('calendarView');
    
    if (listViewBtn && calendarViewBtn) {
        listViewBtn.addEventListener('click', () => {
            listViewBtn.classList.add('active');
            calendarViewBtn.classList.remove('active');
            if (eventsGrid) eventsGrid.classList.remove('hidden');
            if (calendarView) calendarView.classList.add('hidden');
        });
        
        calendarViewBtn.addEventListener('click', () => {
            calendarViewBtn.classList.add('active');
            listViewBtn.classList.remove('active');
            if (eventsGrid) eventsGrid.classList.add('hidden');
            if (calendarView) {
                calendarView.classList.remove('hidden');
                renderCalendar();
            }
        });
    }
})();

// Calendar View
function renderCalendar() {
    if (!window.eventsData) return;
    
    const calendarGrid = document.getElementById('calendarGrid');
    const calendarMonthYear = document.getElementById('calendarMonthYear');
    if (!calendarGrid || !calendarMonthYear) return;
    
    const today = new Date();
    let currentMonth = today.getMonth();
    let currentYear = today.getFullYear();
    
    function updateCalendar() {
        const firstDay = new Date(currentYear, currentMonth, 1);
        const lastDay = new Date(currentYear, currentMonth + 1, 0);
        const daysInMonth = lastDay.getDate();
        const startingDayOfWeek = firstDay.getDay();
        
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];
        
        calendarMonthYear.textContent = `${monthNames[currentMonth]} ${currentYear}`;
        
        // Clear grid
        calendarGrid.innerHTML = '';
        
        // Add day headers
        const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        dayHeaders.forEach(day => {
            const header = document.createElement('div');
            header.className = 'calendar-day-header';
            header.textContent = day;
            calendarGrid.appendChild(header);
        });
        
        // Add empty cells for days before month starts
        for (let i = 0; i < startingDayOfWeek; i++) {
            const empty = document.createElement('div');
            calendarGrid.appendChild(empty);
        }
        
        // Add days
        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'calendar-day';
            
            const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayEvents = window.eventsData.filter(event => {
                if (!event.start_iso) return false;
                return event.start_iso.startsWith(dateStr);
            });
            
            if (dayEvents.length > 0) {
                dayElement.classList.add('has-events');
            }
            
            const dayNumber = document.createElement('div');
            dayNumber.className = 'calendar-day-number';
            dayNumber.textContent = day;
            dayElement.appendChild(dayNumber);
            
            if (dayEvents.length > 0) {
                const eventsCount = document.createElement('div');
                eventsCount.className = 'calendar-day-events';
                eventsCount.textContent = `${dayEvents.length} event${dayEvents.length > 1 ? 's' : ''}`;
                dayElement.appendChild(eventsCount);
            }
            
            dayElement.addEventListener('click', () => {
                // Switch to list view and filter by date
                if (document.getElementById('listViewBtn')) {
                    document.getElementById('listViewBtn').click();
                }
                if (document.getElementById('dateRangeStart')) {
                    document.getElementById('dateRangeStart').value = dateStr;
                    document.getElementById('dateRangeEnd').value = dateStr;
                    filterEvents();
                }
            });
            
            calendarGrid.appendChild(dayElement);
        }
    }
    
    // Navigation
    const prevMonth = document.getElementById('prevMonth');
    const nextMonth = document.getElementById('nextMonth');
    
    if (prevMonth) {
        prevMonth.addEventListener('click', () => {
            currentMonth--;
            if (currentMonth < 0) {
                currentMonth = 11;
                currentYear--;
            }
            updateCalendar();
        });
    }
    
    if (nextMonth) {
        nextMonth.addEventListener('click', () => {
            currentMonth++;
            if (currentMonth > 11) {
                currentMonth = 0;
                currentYear++;
            }
            updateCalendar();
        });
    }
    
    updateCalendar();
}

// Event Modal
function openEventModal(eventId) {
    if (!window.eventsData || !window.eventsData[eventId]) return;
    
    const event = window.eventsData[eventId];
    const modal = document.getElementById('eventModal');
    const modalBody = document.getElementById('modalBody');
    
    if (!modal || !modalBody) return;
    
    const eventDate = event.start_iso ? new Date(event.start_iso).toLocaleString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
    }) : 'Date TBA';
    
    modalBody.innerHTML = `
        <div class="modal-event-header">
            <h2>${event.title || 'Event'}</h2>
            <div class="modal-event-meta">
                <div class="modal-meta-item">
                    <i class="fas fa-calendar-alt"></i>
                    <span>${eventDate}</span>
                </div>
                <div class="modal-meta-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${event.location || 'Location TBA'}</span>
                </div>
                <div class="modal-meta-item">
                    <i class="fas fa-dollar-sign"></i>
                    <span>${event.cost || 'Free'}</span>
                </div>
                <div class="modal-meta-item">
                    <i class="fas fa-tag"></i>
                    <span>${event.category || 'Event'}</span>
                </div>
            </div>
        </div>
        ${event.description ? `<div class="modal-event-description"><p>${event.description}</p></div>` : ''}
        <div class="modal-event-actions">
            ${event.info_url ? `<a href="${event.info_url}" target="_blank" class="btn-details"><i class="fas fa-external-link-alt"></i> Event Details</a>` : ''}
            ${event.tickets_url ? `<a href="${event.tickets_url}" target="_blank" class="btn-tickets"><i class="fas fa-ticket-alt"></i> Buy Tickets</a>` : ''}
            <button class="share-btn" onclick="shareEvent(${eventId})"><i class="fas fa-share-alt"></i> Share Event</button>
        </div>
        ${event.location ? `<div class="modal-event-map">
            <iframe 
                width="100%" 
                height="300" 
                style="border:0" 
                loading="lazy" 
                allowfullscreen
                src="https://www.google.com/maps/embed/v1/place?key=AIzaSyBFw0Qbyq9zTFTd-tUY6d-s6Y4cZZuwBFU&q=${encodeURIComponent(event.location)}">
            </iframe>
        </div>` : ''}
    `;
    
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeEventModal() {
    const modal = document.getElementById('eventModal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeEventModal();
    }
});

// Share Event
function shareEvent(eventId) {
    if (!window.eventsData || !window.eventsData[eventId]) return;
    
    const event = window.eventsData[eventId];
    const shareData = {
        title: event.title,
        text: `${event.title} - ${event.location || 'Oxford'}`,
        url: window.location.href
    };
    
    if (navigator.share) {
        navigator.share(shareData).catch(err => console.log('Error sharing', err));
    } else {
        // Fallback: copy to clipboard
        const text = `${event.title}\n${event.location || 'Oxford'}\n${event.start_iso ? new Date(event.start_iso).toLocaleDateString() : ''}\n${window.location.href}`;
        navigator.clipboard.writeText(text).then(() => {
            alert('Event details copied to clipboard!');
        });
    }
}

// Enhanced Filter Events (with advanced filters)
function filterEvents() {
    const searchTerm = (document.getElementById('searchInput')?.value.trim().toLowerCase() || '');
    const locationFilter = document.getElementById('locationFilter')?.value || '';
    const priceFilter = document.getElementById('priceFilter')?.value || '';
    const sortBy = document.getElementById('sortBy')?.value || 'date';
    
    const eventCards = document.querySelectorAll('.event-card');
    
    eventCards.forEach(card => {
        const title = card.getAttribute('data-title') || '';
        const location = card.getAttribute('data-location') || '';
        const cost = card.getAttribute('data-cost') || '';
        const category = card.getAttribute('data-category') || '';
        const startIso = card.getAttribute('data-start') || '';
        
        let matches = true;
        
        // Search filter
        if (searchTerm && !title.includes(searchTerm) && !location.includes(searchTerm)) {
            matches = false;
        }
        
        // Location filter
        if (locationFilter && !location.toLowerCase().includes(locationFilter.toLowerCase())) {
            matches = false;
        }
        
        // Price filter
        if (priceFilter === 'free' && !cost.toLowerCase().includes('free')) {
            matches = false;
        } else if (priceFilter === 'paid' && cost.toLowerCase().includes('free')) {
            matches = false;
        }
        
        // Category filter (from existing code)
        const cardCategories = category.split(',').map(c => c.trim()).filter(Boolean);
        const activeCategories = new Set(Array.from(document.querySelectorAll('.filter-pill.active')).map(p => p.getAttribute('data-category')));
        const excludedCategories = new Set(Array.from(document.querySelectorAll('.filter-pill.excluded')).map(p => p.getAttribute('data-category')));
        
        if (excludedCategories.size > 0 && cardCategories.some(cat => excludedCategories.has(cat))) {
            matches = false;
        }
        
        if (activeCategories.size > 0 && !activeCategories.has('All')) {
            if (!cardCategories.some(cat => activeCategories.has(cat))) {
                matches = false;
            }
        }
        
        // Date filter (from existing code)
        const dateRangeStart = document.getElementById('dateRangeStart')?.value;
        const dateRangeEnd = document.getElementById('dateRangeEnd')?.value;
        
        if (dateRangeStart || dateRangeEnd) {
            const eventDate = startIso ? new Date(startIso) : null;
            if (eventDate) {
                if (dateRangeStart && eventDate < new Date(dateRangeStart)) {
                    matches = false;
                }
                if (dateRangeEnd && eventDate > new Date(dateRangeEnd + 'T23:59:59')) {
                    matches = false;
                }
            }
        }
        
        if (matches) {
            card.classList.remove('hidden');
        } else {
            card.classList.add('hidden');
        }
    });
    
    // Sort events
    const visibleCards = Array.from(eventCards).filter(card => !card.classList.contains('hidden'));
    const eventsGrid = document.getElementById('eventsGrid');
    
    if (eventsGrid && sortBy) {
        visibleCards.sort((a, b) => {
            if (sortBy === 'date') {
                const dateA = a.getAttribute('data-start') || '';
                const dateB = b.getAttribute('data-start') || '';
                return dateA.localeCompare(dateB);
            } else if (sortBy === 'date-desc') {
                const dateA = a.getAttribute('data-start') || '';
                const dateB = b.getAttribute('data-start') || '';
                return dateB.localeCompare(dateA);
            } else if (sortBy === 'title') {
                const titleA = a.getAttribute('data-title') || '';
                const titleB = b.getAttribute('data-title') || '';
                return titleA.localeCompare(titleB);
            }
            return 0;
        });
        
        visibleCards.forEach(card => {
            eventsGrid.appendChild(card);
        });
    }
}

// Make functions globally available
window.openEventModal = openEventModal;
window.closeEventModal = closeEventModal;
window.shareEvent = shareEvent;
window.filterEvents = filterEvents;
window.renderCalendar = renderCalendar;

