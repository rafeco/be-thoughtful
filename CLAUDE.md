# Technical Documentation for AI Assistants

This document provides technical context about the Be Thoughtful for AI assistants (Claude, ChatGPT, etc.) to help with future development and maintenance.

## Architecture Overview

**Type**: Local-first web application
**Backend**: Python Flask 3.0 + SQLAlchemy
**Frontend**: Bootstrap 5 + vanilla JavaScript (no framework)
**Database**: SQLite (file-based at `instance/database.db`)
**Templates**: Jinja2
**Development**: Flask debug mode with auto-reload
**Port**: 7234 (custom port to avoid conflicts)

## Development Environment

**Critical Requirements**:
1. **Always run from within the virtual environment** (`source venv/bin/activate`)
2. **Debug mode is enabled** - changes to code auto-reload, no server restart needed
3. **Port 7234** - custom port to avoid conflicts with other services

**Auto-reload behavior**:
- Python files (`.py`) - auto-reloads on save
- Templates (`.html`) - changes picked up immediately
- Static files (`.js`, `.css`) - changes picked up immediately
- No need to restart the server during development

**Starting the server**:
```bash
# MUST be run from within activated venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py
# Server runs at http://localhost:7234
```

**Stopping the server**:
- Press `Ctrl+C` in the terminal
- Or use the /tasks command to kill the background process if running via Claude Code

## Core Concepts

### Active Year Logic
The app uses a September-December planning cycle:
- **Sep 1 - Dec 31**: Active year = current year
- **Jan 1 - Aug 31**: Active year = next year

See `utils.py::get_active_year()` for implementation.

### Year Rollover
Automatic rollover happens on first access after Dec 31:
1. Creates `AnnualSummary` record
2. Marks used gift ideas with year
3. Seeds new milestones for new year
4. Preserves all people and historical data

See `utils.py::check_and_perform_rollover()` for implementation.

## Database Schema

### Core Tables

**people**
- Tracks individuals with contact info and preferences
- Fields: `id`, `name`, `email`, `phone`, `person_type`, `card_preference`, `gets_gift`, `notes`, `ai_chat_link`, `active`
- Soft-delete via `active` flag

**gift_ideas**
- Year-over-year gift idea tracking
- Fields: `id`, `person_id`, `idea`, `added_date`, `used_year`, `notes`
- `used_year` is NULL until gift is given

**tasks**
- Per-person, per-year task tracking
- Fields: `id`, `person_id`, `task_type`, `description`, `completed`, `completed_date`, `year`, `actual_gift`
- Task types: `gift_purchased`, `gift_wrapped`, `card_written`, `gift_given`

**milestones**
- Year-scoped general milestones
- Fields: `id`, `phase`, `description`, `completed`, `completed_date`, `year`, `ai_chat_link`
- Phases: September, October, November, December
- Unique constraint on `(phase, year)`

**annual_summary**
- Historical archive records
- Fields: `id`, `year`, `total_people`, `gifts_given`, `handwritten_cards`, `ecards_sent`, `total_budget`, `completed_date`, `notes`

### Relationships
- `Person` → `GiftIdea` (one-to-many, cascade delete)
- `Person` → `Task` (one-to-many, cascade delete)

## Key Routes

### People Management
- `GET /people` - List with filters
- `GET /people/new` - Add person form
- `POST /people/new` - Create person
- `GET /people/<id>` - Person detail with history
- `GET /people/<id>/edit` - Edit form
- `POST /people/<id>/edit` - Update person
- `POST /people/<id>/delete` - Soft delete
- `POST /people/<id>/add-idea` - Add gift idea

### Data Operations
- `GET /import` - CSV import form
- `POST /import` - Process CSV (auto-detects email vs phone by '@' presence)
- `GET /shopping-list` - Gift shopping view
- `GET /writing-queue` - Handwritten cards queue

### Milestones & Tasks
- `GET /milestones` - Milestone management
- `POST /milestones/<id>/toggle` - AJAX completion toggle
- `POST /milestones/<id>/update-link` - Save AI chat link
- `POST /tasks/create/<person_id>/<task_type>` - Create task (AJAX)
- `POST /tasks/<id>/toggle` - Toggle task completion (AJAX)

### Archive
- `GET /archive` - List archived years
- `GET /archive/<year>` - Year detail view

### API Endpoints
- `GET /api/rollover-check` - Check if rollover needed
- `POST /api/quick-add-idea` - Quick add gift idea (AJAX)

## Frontend Architecture

### JavaScript Organization (`static/js/app.js`)

**Initialization**:
- `initTaskCheckboxes()` - AJAX task toggling
- `initMilestoneCheckboxes()` - AJAX milestone toggling
- `initDragAndDrop()` - CSV file drag & drop
- `initRolloverCheck()` - Year rollover detection

**AI Assistant Functions**:
- `generateGiftPrompt(personData)` - Gift brainstorming prompt
- `generateCardPrompt(personData)` - Card writing prompt
- `generateEcardPrompt(stats)` - E-card message prompt
- `copyToClipboard(text)` - Clipboard API with fallback
- `showCopyFeedback(button)` - Visual confirmation

### CSS Styling (`static/css/custom.css`)
- Bootstrap 5 customizations
- Drag & drop zone styling
- Task checkbox animations
- Progress bar enhancements

## AI Assistant Integration

**Design Philosophy**:
- No chat UI in app (keeps it simple)
- No API keys required (user brings their own AI)
- Copy contextual prompts to clipboard
- Track conversation URLs for reference

**Data Flow**:
1. User clicks "Copy Prompt" button
2. JavaScript generates contextual prompt from page data
3. Prompt copied to clipboard
4. User pastes into claude.ai/chatgpt
5. User copies chat URL back
6. URL saved to `ai_chat_link` field (Person or Milestone)

**Prompt Context Includes**:
- Gift prompts: name, type, notes, past gifts, existing ideas, card preference
- Card prompts: name, type, notes
- E-card prompts: recipient count, professional tone guidance

## CSV Import Logic

**Expected Format**: Paperless Post export
- Column "Full Name" → `name`
- Column "Email/Phone Number" → `email` OR `phone`

**Auto-detection**:
```python
if '@' in contact_info:
    email = contact_info
else:
    phone = contact_info
```

**Duplicate Handling**: Skip if matching name + (email OR phone) exists

## Development Patterns

### Adding a New Field to Person
1. Update `models.py::Person` class
2. Update `forms.py::PersonForm`
3. Update create/edit routes in `app.py`
4. Update `templates/person_form.html`
5. Update `templates/person_detail.html` (display)
6. Run `sqlite3 instance/database.db "ALTER TABLE people ADD COLUMN new_field TYPE;"`

### Adding a New Route
1. Add route function in `app.py`
2. Add template in `templates/`
3. Add navigation link in `templates/base.html` if needed
4. Add JavaScript if interactive features needed

### Database Migrations
No formal migration system - use direct SQL:
```bash
sqlite3 instance/database.db "ALTER TABLE ..."
```

## Testing Approach

Manual testing workflow:
1. Import CSV with sample data
2. Test person CRUD operations
3. Test gift idea management
4. Test task completion toggles
5. Test AI prompt generation and copy
6. Test year rollover (manually set system date)
7. Verify archive views

## Common Gotchas

1. **Flask Debug Mode**: Changes auto-reload, no need to restart server
2. **CSRF Tokens**: All forms need `{{ form.hidden_tag() }}`
3. **Year Transitions**: Test around Sep 1 and Jan 1 boundaries
4. **Soft Deletes**: Use `active=True` filter on Person queries
5. **Task Creation**: Tasks are created lazily (on first toggle), not with person
6. **Jinja Filters**: Use `|tojson` for passing Python data to JavaScript

## File Locations

**Backend**:
- `app.py` - All routes and business logic
- `models.py` - SQLAlchemy models
- `forms.py` - Flask-WTF form definitions
- `utils.py` - Year calculation and rollover logic

**Frontend**:
- `templates/base.html` - Base layout with nav
- `templates/dashboard.html` - Main timeline view
- `templates/people_*.html` - People management views
- `templates/person_detail.html` - Person detail with AI assistant
- `templates/milestones.html` - Milestones with e-card AI
- `templates/import.html` - CSV import with drag & drop
- `static/js/app.js` - All JavaScript
- `static/css/custom.css` - Custom styles

**Data**:
- `instance/database.db` - SQLite database (gitignored)
- `.gitignore` - Excludes venv, database, CSV files

## Future Enhancement Ideas

From `spec.md` "Nice-to-Have" section:
- Budget tracking per person/category
- Shopping links with gift ideas
- Photo storage for inspiration
- Search/autocomplete for person names
- Export to CSV for backup
- Year-over-year comparison views
- Bulk "copy to this year" from previous successful ideas

## Dependencies

See `requirements.txt`:
- Flask 3.0.0 - Web framework
- Flask-SQLAlchemy 3.1.1 - ORM
- Flask-WTF 1.2.1 - Form handling
- WTForms 3.1.1 - Form validation

## Design Decisions

**Why SQLite?**: Local-first, no server setup, file-based backup
**Why no React/Vue?**: Simpler, faster, less overhead for this use case
**Why Bootstrap 5?**: Good defaults, responsive, well-documented
**Why copy-to-clipboard AI?**: No API costs, works with any AI tool, simpler UX
**Why soft-delete?**: Preserve historical data integrity
**Why year-over-year gift ideas?**: Last year's idea might work this year

## Maintenance Notes

**Backup Strategy**: Copy `instance/database.db` file
**Version Control**: Database and CSV files are gitignored
**Secret Key**: Hardcoded for local-only use (change if deploying)
**No Authentication**: Local-only app, single user assumed

## Contact & Support

This is a personal project. For issues or questions, refer to:
- `spec.md` - Original feature specification
- `README.md` - User-facing documentation
- This file - Technical context for AI assistants
