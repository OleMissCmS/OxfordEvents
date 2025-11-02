// Oxford Events JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const filterPills = document.querySelectorAll('.filter-pill');
    const searchInput = document.getElementById('searchInput');
    const eventCards = document.querySelectorAll('.event-card');
    
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

