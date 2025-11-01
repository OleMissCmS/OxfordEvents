"""
Bandsintown-inspired CSS styles with light, clean colors
"""

BANDSINTOWN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Force white background everywhere */
.stApp {
    background-color: #FFFFFF !important;
}

.stMainFrame {
    background-color: #FFFFFF !important;
}

/* Clean white background container */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1400px;
    background-color: #FFFFFF;
}

/* Remove dark theme */
[data-baseweb="theme"] {
    background-color: #FFFFFF !important;
}

/* Top accent bar - subtle blue */
.accent-bar { 
    height: 4px; 
    background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%); 
    margin-bottom: 0; 
}

/* Hero - clean white with subtle gray text */
.hero {
    background: #FFFFFF;
    color: #333333;
    padding: 2rem 1rem;
    border-radius: 0 0 8px 8px;
    margin-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
}
.hero h1 { 
    font-size: 2.25rem; 
    margin: 0 0 .5rem 0; 
    letter-spacing: -0.02em; 
    color: #333333;
    font-weight: 700;
}
.hero p { 
    margin: 0; 
    color: #6C757D;
    font-size: 1rem;
}

/* Event cards - smaller, condensed like Bandsintown */
.event-card {
    background: white;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #e9ecef;
    transition: box-shadow 0.2s, transform 0.2s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    display: flex;
    flex-direction: column;
    margin-bottom: 1rem;
}
.event-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    border-color: #dee2e6;
    transform: translateY(-2px);
}

.event-image {
    width: 100%;
    height: 150px;
    object-fit: cover;
    background: #f8f9fa;
}

.event-date-pill {
    font-size: 0.75rem;
    color: #6C757D;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    margin: 0.5rem 0 0.25rem 0;
}

.event-title {
    font-size: 1rem;
    font-weight: 600;
    color: #333333;
    margin: 0.25rem 0;
    line-height: 1.4;
}
.event-title a {
    color: #333333;
    text-decoration: none;
}
.event-title a:hover {
    color: #007BFF;
}

.event-venue {
    font-size: 0.875rem;
    color: #6C757D;
    margin: 0.25rem 0;
}

.event-meta {
    font-size: 0.75rem;
    color: #6C757D;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.calendar-icon {
    display: inline-block;
    width: 14px;
    height: 14px;
    vertical-align: middle;
    margin-right: 4px;
    opacity: 0.6;
}

/* Filter chips - horizontal like Bandsintown */
.filter-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    padding: 0.75rem 0;
    align-items: center;
}

.filter-chips-container button.stButton {
    margin: 0;
    padding: 0;
    flex-shrink: 0;
}

.filter-chips-container button.stButton > button {
    padding: 0.5rem 1rem !important;
    border-radius: 20px !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    border: 1px solid #dee2e6 !important;
    background: #f8f9fa !important;
    color: #333333 !important;
    transition: all 0.2s !important;
    white-space: nowrap !important;
    width: auto !important;
}

.filter-chips-container button.stButton > button:hover {
    background: #e9ecef !important;
    border-color: #ced4da !important;
    transform: translateY(-1px);
}

/* Active state - blue like Bandsintown */
.filter-chips-container button.stButton[data-active="true"] > button {
    background: #007BFF !important;
    color: white !important;
    border-color: #007BFF !important;
}

.filter-chips-container button.stButton[data-active="true"] > button:hover {
    background: #0056b3 !important;
    border-color: #0056b3 !important;
}

/* Search input styling */
.filter-chips-container .stTextInput {
    flex: 1;
    min-width: 200px;
    margin-left: 0.5rem;
}

.filter-chips-container .stTextInput > div > div > input {
    padding: 0.5rem 1rem !important;
    border-radius: 20px !important;
    border: 1px solid #dee2e6 !important;
    font-size: 0.875rem !important;
    background: white !important;
}

/* Stats section */
.stats-section {
    background: white;
    padding: 1.25rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    border: 1px solid #e9ecef;
}

.stat-card {
    text-align: center;
    padding: 0.75rem;
}

.stat-number {
    font-size: 1.5rem;
    font-weight: 700;
    color: #333333;
    margin: 0;
}

.stat-label {
    font-size: 0.875rem;
    color: #6C757D;
    margin: 0.25rem 0 0 0;
}

/* Tickets button - Bandsintown style (pinkish-red) */
div[data-testid="stButton"] button {
    border-radius: 6px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
}

/* Responsive */
@media (max-width: 768px) {
    .event-grid {
        grid-template-columns: 1fr;
    }

    .hero h1 {
        font-size: 1.5rem;
    }

    .action-buttons {
        flex-direction: column;
    }
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
