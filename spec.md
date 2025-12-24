# Christmas Planning App - PRD (Server-Side Edition)

## Overview
A lightweight, local-first web application for managing Christmas gift-giving and card-sending across the annual cycle. Think "CRM for staying thoughtful" - tracks people, gift ideas, card preferences, and guides you through the September-December workflow with appropriate prompts and deadlines.

## Core Problem
You need to spread Christmas planning across Q3/Q4 instead of cramming it into December, and you need a system that:
- Captures gift ideas when you think of them (not just in December)
- Distinguishes between different types of relationships (family, colleagues, friends, professional contacts)
- Reminds you what to do when throughout the cycle
- Lets you track what's been purchased/sent without being burdensome
- Maintains a historical record so you can learn from previous years

## User Personas
Really just one: you. But the app should work for anyone who sends 50-200 cards/gifts annually and wants to be more thoughtful about it.

## Must-Have Features (v1)

### People Management
- Import from Paperless Post CSV (name, email at minimum)
- Classify people by type: Family, Close Friends, Colleagues (Direct Reports, Peers, Other), Professional Network, Other
- For each person, track:
  - Card preference: Handwritten, E-card, None
  - Gift status: Yes/No/Maybe
  - Gift ideas (running list with dates added)
  - Notes field for context ("mentor", "board member", "helped with X project")
  - Historical record of previous years' gifts and cards
- Add/edit/delete people via web forms
- Bulk operations (e.g., "mark all colleagues as getting e-cards")

### Year Management & Automatic Rollover
- **Active year** is determined by current date:
  - September 1 - December 31: Current year (e.g., 2024)
  - January 1 - August 31: Next year (e.g., planning for 2025)
- On first access after December 31, automatically:
  - Archive all completed tasks to history
  - Create new milestone templates for upcoming year
  - Reset task completion states for new year
  - Preserve people and gift ideas (carry forward)
- **Archive view** shows what actually happened each year:
  - Who got gifts and what they were
  - Who got which type of card
  - Completion dates for milestones
  - Budget spent (if tracked)
- Gift ideas marked as "used" stay with the person but are flagged with the year used

### Timeline View
Dashboard showing current phase and what needs to happen:
- September: "Brainstorm gifts for X people, draft card list"
- October: "Purchase gifts for family (0/X complete), order physical cards"
- November: "Write handwritten cards (0/X complete), buy colleague gifts"
- December: "Distribute colleague gifts, send e-cards, wrap everything"

Phase determination based on current date within the active year.

### Task Management
- Simple checkboxes for key milestones:
  - [ ] Brainstorm session complete
  - [ ] Physical cards ordered
  - [ ] Handwritten cards written
  - [ ] E-card sent
  - [ ] Colleague gifts purchased
- Per-person tasks:
  - [ ] Gift idea decided
  - [ ] Gift purchased
  - [ ] Gift wrapped
  - [ ] Card written (if handwritten)
  - [ ] Gift given (with optional note about what it was)
- Tasks should be easy to check off from list views
- When marking "gift given", prompt for what the gift actually was (pre-filled with gift idea if exists)

### Gift Idea Capture
- Quick-add interface: person name + idea + optional note
- Ideas persist year-over-year (last year's idea might work this year)
- Can mark ideas as "used" with year when completing "gift given" task
- Add gift idea directly from person detail page or from quick-add form
- See previous years' gifts on person detail page for inspiration

### Reporting/Views
- "Who needs what?" - filter by card type, gift status, relationship type
- "Shopping list" - all unpurchased gifts with ideas
- "Writing queue" - everyone getting a handwritten card
- Stats on dashboard: X of Y cards written, X of Y gifts purchased, etc.
- Sortable/filterable tables for all list views
- **Archive view** - browse previous years, see completion stats and what was actually done

### CSV Import
- Upload page for Paperless Post CSV
- Map CSV columns to person fields
- Preview before import
- Handle duplicates gracefully (skip or update)

## Nice-to-Have (v2+)
- Budget tracking per person/category (with annual totals in archive)
- Amazon/shopping links stored with gift ideas
- Export to CSV for backup
- Photo storage for inspiration (gift ideas, card examples)
- Colleague gift template suggestions based on team size
- Search/autocomplete for person names
- Year-over-year comparison (did I send them a card last year?)
- Bulk "copy to this year" from previous year's successful ideas

## Technical Stack

### Backend
- **Python Flask** - lightweight, perfect for local single-user app
- **SQLite** - simple, file-based, no separate database server needed
- **SQLAlchemy** - ORM for database interactions (recommended for cleaner code)
- **Flask-WTF** - form handling and CSRF protection

### Frontend
- **Bootstrap 5** - responsive, good-looking defaults
- **Vanilla JavaScript** - for interactive elements (sorting, filtering, quick updates)
- **Jinja2 templates** - Flask's built-in templating

### Development/Deployment
- Runs on `localhost:5000` (or configurable port)
- Single command to start: `python app.py` or `flask run`
- Database file stored in project directory
- No authentication needed (local only)

## Data Model

```sql
-- People table (persistent across years)
CREATE TABLE people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    person_type TEXT CHECK(person_type IN ('Family', 'Close Friend', 'Colleague - Direct Report', 'Colleague - Peer', 'Colleague - Other', 'Professional', 'Other')),
    card_preference TEXT CHECK(card_preference IN ('Handwritten', 'E-card', 'None')) DEFAULT 'E-card',
    gets_gift BOOLEAN DEFAULT 0,
    notes TEXT,
    active BOOLEAN DEFAULT 1,  -- allow soft-delete for people no longer in your life
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Gift ideas table (one-to-many with people, persistent)
CREATE TABLE gift_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    idea TEXT NOT NULL,
    added_date DATE DEFAULT CURRENT_DATE,
    used_year INTEGER,  -- NULL if never used, year if used
    notes TEXT,
    FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
);

-- Tasks table (scoped to a specific year)
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,  -- NULL for general milestones
    task_type TEXT NOT NULL,  -- 'gift_idea', 'gift_purchased', 'gift_wrapped', 'card_written', 'gift_given'
    description TEXT,
    completed BOOLEAN DEFAULT 0,
    completed_date DATE,
    year INTEGER NOT NULL,
    actual_gift TEXT,  -- what was actually given (filled when gift_given is checked)
    FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE,
    INDEX idx_tasks_year (year),
    INDEX idx_tasks_person_year (person_id, year)
);

-- Milestones table (scoped to a specific year)
CREATE TABLE milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase TEXT CHECK(phase IN ('September', 'October', 'November', 'December')),
    description TEXT NOT NULL,
    completed BOOLEAN DEFAULT 0,
    completed_date DATE,
    year INTEGER NOT NULL,
    UNIQUE(phase, year)
);

-- Annual summary table (created automatically at year rollover)
CREATE TABLE annual_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL UNIQUE,
    total_people INTEGER,
    gifts_given INTEGER,
    handwritten_cards INTEGER,
    ecards_sent INTEGER,
    total_budget REAL,  -- if tracked
    completed_date DATE,  -- when year was archived
    notes TEXT
);

-- View for current year's activity (makes queries easier)
CREATE VIEW current_year_tasks AS
SELECT * FROM tasks
WHERE year = (
    CASE
        WHEN CAST(strftime('%m', 'now') AS INTEGER) >= 9
        THEN CAST(strftime('%Y', 'now') AS INTEGER)
        ELSE CAST(strftime('%Y', 'now') AS INTEGER) + 1
    END
);
```

## Year Rollover Logic

### Automatic Rollover (triggered on first access after Dec 31)
1. Check if current active year needs rollover (compare last milestone year vs. calculated active year)
2. If rollover needed:
   - Create `annual_summary` record for completed year
   - Archive all task completion data (counts of completed tasks)
   - Create new milestone templates for upcoming year
   - Reset per-person tasks (create fresh task records for new year)
   - Mark gift ideas as used if "gift_given" was checked last year
3. Show user a summary: "Archived 2024 season: 42 gifts given, 15 handwritten cards sent"

### Active Year Calculation
```python
def get_active_year():
    """Return the year we're currently planning for"""
    today = date.today()
    if today.month >= 9:  # Sep-Dec
        return today.year
    else:  # Jan-Aug
        return today.year + 1
```

## Routes/Pages Structure

```
/                           - Dashboard (timeline view, stats, what's due now)
/people                     - List all people (filterable, sortable)
/people/new                 - Add new person
/people/<id>               - Person detail (edit, view history across years, add gift ideas)
/people/<id>/edit          - Edit person
/people/<id>/delete        - Delete person (with confirmation)

/import                     - CSV import page
/export                     - CSV export (future)

/tasks                      - All tasks view for current year (filterable by person, type, status)
/tasks/<id>/toggle         - Toggle task completion (AJAX endpoint)
/tasks/<id>/complete-gift  - Mark gift given + record what it was

/shopping-list             - All people who get gifts + their ideas (current year)
/writing-queue             - All people getting handwritten cards (current year)

/milestones                - View/manage general milestones (current year)
/milestones/<id>/toggle    - Toggle milestone completion

/archive                   - Browse previous years
/archive/<year>            - Detail view of a specific year (who got what, when milestones completed)

/api/quick-add-idea        - AJAX endpoint for quick gift idea entry
/api/rollover-check        - AJAX endpoint to check if rollover needed (called on page load)
```

## UX Principles
- Fast data entry (autofocus on forms, keyboard shortcuts where helpful)
- Minimal clicks to common actions (toggle checkboxes inline, edit from list views)
- Don't make me think about the system, make me think about the people
- Forgiving (confirm before deleting, easy to undo task completion)
- Visual progress indicators (Bootstrap progress bars for completion percentages)
- Mobile-responsive (Bootstrap handles this) but desktop-first design
- **Historical context is helpful**: show last year's gift when planning this year

## Key User Flows

### Initial Setup (September 2024)
1. Import Paperless Post CSV
2. Review imported people, set card preferences and gift status
3. Browse people, start adding gift ideas
4. Mark "Brainstorm complete" milestone

### October Flow
1. Dashboard shows: "Purchase gifts for family members"
2. Click through to shopping list filtered by family
3. Check off "gift purchased" as you buy things
4. Mark "Physical cards ordered" milestone

### November Flow
1. Dashboard shows: "Write X handwritten cards"
2. Click through to writing queue
3. Check off cards as written
4. Mark "Handwritten cards written" milestone

### December Flow
1. Dashboard shows remaining tasks
2. Wrap gifts, check off tasks
3. **As gifts are given**, check "gift given" and record what it actually was
4. Send e-cards, mark milestone
5. Done!

### January 2025 (Automatic Rollover)
1. User visits app in January
2. App detects year rollover needed
3. Shows summary modal: "2024 archived: 42 gifts given, 15 handwritten cards"
4. Dashboard now shows planning for Christmas 2025
5. All people and gift ideas carry forward
6. Fresh tasks created for 2025
7. Can browse archive to see what was done in 2024

### Archive Browsing (Anytime)
1. Click "View Archive"
2. See list of years: 2024, 2023, 2022...
3. Click into 2024
4. See: who got gifts, who got cards, when milestones were completed
5. Click on a person to see gift history across all years

## Bootstrap UI Guidelines
- Use Bootstrap cards for person details
- Use Bootstrap tables with striped rows for lists
- Use Bootstrap badges for status indicators (completed/pending)
- Use Bootstrap forms with proper validation styling
- Use Bootstrap modals for confirmations (delete, rollover summary)
- Use Bootstrap alerts for success/error messages
- Keep color scheme simple: primary for actions, success for completed, warning for pending
- Use Bootstrap timeline component (or custom CSS) for archive year view

## File Structure Recommendation
```
christmas-app/
├── app.py                 # Main Flask application
├── models.py             # SQLAlchemy models
├── forms.py              # Flask-WTF forms
├── utils.py              # Year rollover logic, active year calculation
├── database.db           # SQLite database (created on first run)
├── requirements.txt      # Python dependencies
├── README.md             # Setup instructions
├── static/
│   ├── css/
│   │   └── custom.css   # Any custom styles beyond Bootstrap
│   └── js/
│       └── app.js       # JavaScript for interactivity
└── templates/
    ├── base.html         # Base template with Bootstrap
    ├── dashboard.html
    ├── people_list.html
    ├── person_detail.html
    ├── person_form.html
    ├── import.html
    ├── shopping_list.html
    ├── writing_queue.html
    ├── archive_list.html
    ├── archive_detail.html
    └── components/       # Reusable template fragments
        ├── person_card.html
        ├── task_checkbox.html
        ├── progress_bar.html
        └── year_summary.html
```

## Success Metrics
- You use it in September instead of panicking in December
- You can look back at previous years and remember what you did
- Year-over-year, you get better at gift-giving because you have the data

## Archive Feature Details

### What Gets Archived
- All task completion data (who got gifts, who got cards, when)
- Actual gifts given (from "gift given" task completion)
- Milestone completion dates
- Summary stats for the year

### Archive Display
- List view: Years with summary stats (X gifts, Y cards)
- Detail view: Full breakdown for a specific year
  - Timeline of when milestones were completed
  - List of people and what they received
  - Sortable/filterable (same as current year views)
- Person detail pages show multi-year history

### Data Retention
- People and gift ideas never archived (persist indefinitely)
- Tasks older than current year are read-only
- Can't edit archived year data (integrity of historical record)

## Open Questions for Claude Code
- CSV import: strict Paperless Post format or flexible column mapping?
  - **Answer**: Start with strict, can add flexibility later
- Should we seed the database with milestone templates on first run?
  - **Answer**: Yes, create templates for current active year
- Should "actual gift given" be required when checking "gift given" task?
  - **Answer**: Optional but strongly encouraged (pre-fill from gift idea)
- Archive retention: keep forever or allow deletion of old years?
  - **Answer**: Keep forever (it's just text, storage is cheap)

## Out of Scope (v1)
- Multi-user support / authentication
- Shared/collaborative features
- Calendar integration
- Actual gift purchasing integration
- Card design/printing
- Shipping tracking
- Budget enforcement/alerts
- Email reminders
- Mobile native app
- Undo year rollover (once rolled over, it's done)

