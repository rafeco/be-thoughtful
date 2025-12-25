# Technical Documentation

## File Structure

```
be-thoughtful/
├── app.py                 # Main Flask application
├── models.py             # Database models (SQLAlchemy)
├── forms.py              # WTForms form definitions
├── utils.py              # Helper functions (year logic, rollover)
├── instance/
│   └── database.db       # SQLite database (created on first run)
├── requirements.txt      # Python dependencies
├── README.md             # User documentation
├── TECHNICAL.md          # This file
├── spec.md               # Original specification
├── static/
│   ├── css/
│   │   └── custom.css   # Custom styles
│   ├── js/
│   │   └── app.js       # JavaScript interactivity
│   └── images/
│       └── be-thoughtful.png  # App logo
└── templates/
    ├── base.html         # Base layout with navigation
    ├── dashboard.html    # Dashboard with timeline and stats
    ├── people_list.html  # People list with filtering
    ├── person_detail.html # Person detail with gift ideas
    ├── person_form.html  # Add/edit person form
    ├── import.html       # CSV import interface
    ├── shopping_list.html # Gift shopping checklist
    ├── writing_queue.html # Card writing queue
    ├── milestones.html   # Milestone management
    ├── archive_list.html # Archive years list
    ├── archive_detail.html # Year archive detail
    └── about.html        # About page
```

## Technology Stack

### Backend
- **Flask** - Lightweight Python web framework
- **SQLAlchemy** - ORM for database operations
- **Flask-WTF** - Form handling and validation
- **email-validator** - Email field validation

### Database
- **SQLite** - File-based relational database
- Location: `instance/database.db`
- Auto-created on first run with initial milestone templates

### Frontend
- **Bootstrap 5** - CSS framework for responsive UI
- **Bootstrap Icons** - Icon set
- **Vanilla JavaScript** - No frontend frameworks
- **Jinja2** - Template engine (built into Flask)

## Database Schema

### Person
- `id` - Primary key
- `name` - Person's full name
- `email` - Email address (optional)
- `phone` - Phone number (optional)
- `person_type` - Category (Family, Close Friend, Neighbor, Colleague, etc.)
- `card_preference` - Handwritten, E-card, or None
- `gets_gift` - Boolean flag
- `budget` - Planned gift budget in whole dollars (INTEGER)
- `card_addressee` - Custom addressee for cards (e.g., "The Smith Family")
- `notes` - Freeform text notes
- `ai_chat_link` - URL to Claude/ChatGPT conversation
- `active` - Soft delete flag
- `created_at`, `updated_at` - Timestamps

### GiftIdea
- `id` - Primary key
- `person_id` - Foreign key to Person
- `idea` - Gift idea description
- `added_date` - Date added
- `used_year` - Year this idea was used (NULL if unused)
- `notes` - Additional notes

### Task
- `id` - Primary key
- `person_id` - Foreign key to Person (nullable for general tasks)
- `task_type` - Type: gift_purchased, gift_given, card_written, etc.
- `description` - Task description
- `completed` - Boolean flag
- `completed_date` - Date completed
- `year` - Year this task applies to
- `actual_gift` - What was actually given (for gift_given tasks)

### Milestone
- `id` - Primary key
- `phase` - Phase name (September, October, November, December)
- `description` - Milestone description
- `completed` - Boolean flag
- `completed_date` - Date completed
- `year` - Year this milestone applies to
- `ai_chat_link` - URL to AI conversation for this milestone
- `subtasks` - JSON array of subtask descriptions
- `completed_subtasks` - JSON array of completed subtask indices

### AnnualSummary
- `id` - Primary key
- `year` - Year (unique)
- `total_people` - Count of people
- `gifts_given` - Count of gifts given
- `handwritten_cards` - Count of handwritten cards
- `ecards_sent` - Count of e-cards
- `total_budget` - Total budget spent
- `completed_date` - Date year was archived
- `notes` - Additional notes

## Configuration

### Flask Settings (`app.py`)
```python
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

### Development Server
- **Port**: 7234
- **Debug Mode**: Enabled (auto-reload on file changes)
- **Host**: 127.0.0.1 (localhost only)

### Database Path
The database uses an absolute path constructed at runtime:
```python
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'database.db')
```

## Key Features Implementation

### Active Year Calculation
The app determines the "active year" based on the current date and whether years have been archived:

```python
def get_active_year():
    """Calculate the active planning year."""
    today = date.today()
    # Planning starts in September
    base_year = today.year if today.month >= 9 else today.year + 1

    # Check if this year was already archived
    if AnnualSummary.query.filter_by(year=base_year).first():
        return base_year + 1

    return base_year
```

### Year Rollover
Automatic rollover happens on first access after December 31st:
1. Creates AnnualSummary record
2. Archives all task completions
3. Creates fresh milestones for new year
4. Marks used gift ideas with the year
5. Shows summary modal to user

Manual archiving is available on the Archive page for users who finish early.

### Duplicate Detection
When adding new people, checks for duplicates:
- Name (always checked)
- Email (if provided)
- Phone (if provided)

Shows warning but allows user to proceed if desired.

### CSV Import
Parses Paperless Post format:
- Maps "Full Name" → name
- Maps "Email/Phone Number" → email
- Defaults: card_preference='E-card', gets_gift=False
- Deduplication matches on name+email, name+phone, or just name

### Milestone Subtasks
Monthly milestones have JSON arrays of subtasks:
- `subtasks` - Array of task descriptions
- `completed_subtasks` - Array of completed task indices
- Auto-completes milestone when all subtasks are checked
- Auto-uncompletes if a subtask is unchecked

### AI Assistant Integration
Generates contextual prompts for Claude/ChatGPT:
- Gift brainstorming (person context, past gifts, notes)
- Card writing (relationship type, personal notes)
- E-card message composition (professional tone guidance)

Users copy prompts, chat in external AI tool, and save chat URLs back to the app.

## Development Notes

### Running Migrations
SQLite doesn't support all ALTER TABLE operations. For schema changes:
1. Add column to model
2. Run ALTER TABLE via sqlite3 CLI
3. Restart Flask server (auto-reload picks up model changes)

Example:
```bash
sqlite3 instance/database.db "ALTER TABLE people ADD COLUMN budget INTEGER;"
```

### Form Validation
Uses Flask-WTF with validators:
- `DataRequired()` - Field must have value
- `Optional()` - Field can be empty
- `Email()` - Valid email format (requires email-validator package)
- `NumberRange(min=0)` - For budget field

### AJAX Endpoints
- `/api/rollover-check` - Checks for year rollover on page load
- `/tasks/<id>/toggle` - Toggle task completion
- `/milestones/<id>/toggle-subtask` - Toggle subtask completion
- `/api/quick-add-idea` - Quick-add gift idea

### Template Inheritance
All pages extend `base.html` which provides:
- Navigation bar
- Flash message display
- Bootstrap CSS/JS includes
- Festive green/red color scheme

### Static Files
- CSS auto-reloads in development mode
- JavaScript uses vanilla ES6+ (no build step)
- Images served from `static/images/`

## Deployment Considerations

**This app is designed for local, single-user use only.** It is not production-ready for multi-user or internet-facing deployment.

If you wanted to deploy it, you would need to:
- Change SECRET_KEY to a secure random value
- Use a production WSGI server (not Flask dev server)
- Consider using PostgreSQL instead of SQLite
- Add authentication/authorization
- Enable HTTPS
- Add CSRF protection for all forms (partially done via Flask-WTF)
- Add input sanitization for XSS prevention
- Set up proper logging
- Add database backups

## Troubleshooting

### Database locked errors
SQLite can have locking issues with concurrent writes. This app is single-user so it shouldn't be an issue, but if you see "database is locked":
- Make sure only one Flask instance is running
- Restart the server

### Template changes not appearing
- Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+F5)
- Touch app.py to force Flask reload: `touch app.py`

### Import errors
- Make sure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`

### Database schema mismatch
If models.py changes don't match database:
1. Stop server
2. Back up `instance/database.db`
3. Delete database or manually ALTER TABLE
4. Restart server (auto-creates schema)

## Testing

Currently no automated tests. Manual testing workflow:
1. Test CSV import with sample data
2. Add/edit/delete people
3. Add gift ideas and mark as used
4. Complete tasks and milestones
5. Test year rollover (manual trigger)
6. Browse archive views
7. Test all filters and sorting
8. Test on mobile (responsive design)

## Performance

- SQLite performs well for single-user with <10,000 records
- No pagination implemented (assumes reasonable dataset)
- AJAX reduces full page reloads
- Template caching via Jinja2
- Static file caching via Flask

## Security Notes

- No authentication (single-user, local-only)
- CSRF protection via Flask-WTF for forms
- SQL injection prevented by SQLAlchemy parameterized queries
- XSS prevention via Jinja2 auto-escaping
- Input validation via WTForms validators
- Soft deletes preserve data integrity

## Browser Compatibility

Tested on:
- Chrome/Edge (Chromium)
- Firefox
- Safari

Requires modern browser with ES6+ JavaScript support.
