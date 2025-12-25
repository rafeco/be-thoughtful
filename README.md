# Be Thoughtful

A lightweight, local-first web application for managing Christmas gift-giving and card-sending across the annual cycle. Think "CRM for staying thoughtful" - tracks people, gift ideas, card preferences, and guides you through the September-December workflow with appropriate prompts and deadlines.

## Features

- **People Management** - Track family, friends, colleagues, and professional contacts with separate email and phone fields
- **Gift Ideas** - Capture gift ideas year-round, not just in December
- **Card Tracking** - Manage handwritten cards and e-cards
- **Timeline View** - See what needs to happen in each phase (Sept-Dec)
- **Milestone Subtasks** - Break down monthly milestones into trackable subtasks with automatic completion
- **Task Management** - Simple checkboxes for milestones and per-person tasks
- **Year Rollover** - Automatic archiving and planning for next year (or manual if you finish early)
- **Pre-planning Phase** - Get helpful suggestions during Jan-Aug before the planning cycle begins
- **Archive View** - Historical record of previous years with detailed stats
- **CSV Import** - Import contacts from Paperless Post with drag & drop and automatic deduplication
- **AI Assistant Integration** - Copy contextual prompts for Claude/ChatGPT to help brainstorm gifts and write cards

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment**:
   ```bash
   # On macOS/Linux:
   source venv/bin/activate

   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open your browser**:
   Navigate to `http://localhost:7234`

That's it! The database will be created automatically on first run.

**Note**: The app runs in Flask's development mode with auto-reload enabled. Any changes to Python files, templates, or static files will be picked up automatically without restarting the server. Always run the app from within the activated virtual environment.

## First-Time Setup

### Option 1: Import from CSV

1. Click **Import CSV** in the navigation
2. Upload your Paperless Post CSV file (see `unsent-invites.csv` for format)
3. Review imported contacts
4. Edit people to set card preferences and gift status

### Option 2: Add People Manually

1. Click **Add Person** in the navigation
2. Fill in name, email, type, card preference, and gift status
3. Add notes for context (e.g., "mentor", "board member")
4. Save and repeat

## Usage Guide

### Planning Timeline

The app automatically determines your planning phase based on the date:

- **Pre-planning (January-August)**: Get ready for the upcoming season
  - Review and update your contact list
  - Log gift ideas throughout the year
  - Review last year's archive for insights
  - Note budget changes or new traditions
  - Keep track of interests people mention

- **September**: Brainstorm gifts and draft card list
  - Review previous year's gifts and cards
  - Brainstorm gift ideas for each person
  - Finalize handwritten card list
  - Finalize e-card recipient list

- **October**: Purchase gifts for family, order physical cards
  - Purchase all family gifts
  - Order physical cards from vendor
  - Confirm card quantities match list

- **November**: Write handwritten cards, buy colleague gifts
  - Write all handwritten cards
  - Purchase all colleague gifts
  - Wrap family gifts

- **December**: Distribute gifts, send e-cards, wrap everything
  - Draft and finalize e-card message
  - Send e-cards to all recipients
  - Distribute colleague gifts
  - Wrap remaining gifts
  - Deliver/mail all gifts and cards

Each monthly milestone includes subtasks that you can check off as you complete them. When all subtasks are done, the milestone automatically marks itself complete!

### Adding Gift Ideas

Gift ideas can be added throughout the year:

1. Go to a person's detail page
2. Enter gift idea in the quick-add form
3. Ideas persist year-over-year
4. When you give a gift, mark it as "used" for that year

### Tracking Tasks

The app helps you track:

- Gift idea decided
- Gift purchased
- Gift wrapped
- Card written (for handwritten cards)
- Gift given (with notes on what you actually gave)

Check off tasks as you complete them - they'll be saved to your history.

### Year Rollover

**Automatic Rollover**: On your first visit after December 31st, the app will automatically:

1. Archive all completed tasks for the old year
2. Create an annual summary
3. Set up fresh milestones for the new year
4. Preserve all people and gift ideas
5. Show you a summary of what you accomplished

**Manual Archiving**: If you finish everything early and want to start planning for next year:

1. Navigate to the **Archive** page
2. Scroll to the bottom to find the "Manual Archive" section
3. Click "Archive [YEAR] and Move to [NEXT YEAR]"
4. Confirm the action (this cannot be undone!)
5. The app will immediately switch to planning for the next year

Once a year is archived (manually or automatically), the app will show the next year as the active planning year. For example, if you manually archive 2025 in December, the app will show "Planning for Christmas 2026" and enter pre-planning phase.

### Viewing History

Click **Archive** to browse previous years and see:

- Who got gifts (and what they were)
- Who got cards
- When milestones were completed
- Overall stats for each year

### Using the AI Assistant

The app includes AI assistance features to help you brainstorm gifts and write thoughtful cards, without building complex chat UI or requiring API keys.

**How it works**:
1. Click a "Copy Prompt" button (on person pages or milestones)
2. The app generates a contextual prompt with relevant information
3. Open claude.ai (or ChatGPT) in a new tab
4. Paste the prompt and chat with the AI
5. Copy the chat URL from your browser
6. Paste it back into the app's chat link field
7. Now you can quickly return to that conversation anytime

**Where to find it**:

**Gift Brainstorming** (Person Detail Pages):
- "Copy Gift Idea Prompt" - generates a prompt with person's details, your notes, past gifts, and existing ideas
- Save the Claude chat link to track your brainstorming conversation

**Card Writing Help** (Person Detail Pages):
- "Copy Card Writing Prompt" - helps you write personalized handwritten card messages
- Context includes relationship type and your notes about the person

**E-card Message** (Milestones Page):
- "Copy E-card Writing Prompt" - helps compose your main holiday e-card message
- Guidance for professional, warm tone appropriate for colleagues and contacts
- Save the chat link with the December milestone

**Benefits**:
- No API keys or AI costs required
- Works with any AI tool (Claude, ChatGPT, etc.)
- Contextual prompts save you from retyping information
- Track conversations for each person
- Simple, focused assistance when you need it

## File Structure

```
be-thoughtful/
├── app.py                 # Main Flask application
├── models.py             # Database models
├── forms.py              # Form definitions
├── utils.py              # Year logic and helpers
├── database.db           # SQLite database (created on first run)
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── spec.md               # Original specification
├── static/
│   ├── css/
│   │   └── custom.css   # Custom styles
│   └── js/
│       └── app.js       # JavaScript interactivity
└── templates/
    ├── base.html         # Base layout
    ├── dashboard.html    # Dashboard view
    ├── people_list.html  # People list
    ├── person_detail.html # Person detail
    ├── person_form.html  # Add/edit person
    ├── import.html       # CSV import
    ├── shopping_list.html # Gift shopping view
    ├── writing_queue.html # Card writing queue
    ├── milestones.html   # Milestone tracking
    ├── archive_list.html # Archive list
    ├── archive_detail.html # Year archive
    └── components/       # Reusable components
        ├── person_card.html
        ├── task_checkbox.html
        └── progress_bar.html
```

## Technology Stack

- **Backend**: Python Flask, SQLAlchemy, Flask-WTF
- **Database**: SQLite (local file-based)
- **Frontend**: Bootstrap 5, vanilla JavaScript
- **Templates**: Jinja2

## Configuration

The app uses sensible defaults for local development:

- **Port**: 7234 (change in `app.py` if needed)
- **Database**: `instance/database.db` (SQLite file in instance directory)
- **Secret Key**: Set in `app.py` (change for production use)

## Tips for Success

1. **Import early**: Start in September by importing your contacts
2. **Capture ideas year-round**: Add gift ideas whenever you think of them
3. **Review people periodically**: Update card preferences and gift status
4. **Use the timeline**: Follow the monthly guidance on the dashboard
5. **Track what you actually gave**: Fill in actual gifts to build history
6. **Review the archive**: Look at previous years for inspiration

## Troubleshooting

### Database issues
If you need to reset the database:
1. Stop the Flask server (Ctrl+C)
2. Delete `instance/database.db`
3. Restart the app with `python app.py`
4. A fresh database will be created automatically

### Import problems
Make sure your CSV has columns named exactly:
- `Full Name`
- `Email/Phone Number`

Other columns will be ignored. Duplicate detection checks for matching name + email (or name + phone, or just name if neither is provided).

### Year rollover not triggering
The automatic rollover checks on first access after December 31st. Visit the dashboard to trigger it. Alternatively, use the manual archive button on the Archive page if you want to finish early.

### Dashboard shows wrong year after archiving
If you manually archive a year, refresh the page to see the updated active year. The app checks if the calculated year has been archived and automatically moves to the next year.

## Support

This is a local, single-user application with no cloud dependencies. All data is stored locally in `database.db`.

For issues or questions, refer to `spec.md` for detailed feature documentation.

## Future Enhancements (v2+)

- Budget tracking per person/category
- Shopping links with gift ideas
- Photo storage for inspiration
- Search/autocomplete for person names
- Export to CSV for backup
- Year-over-year comparison views

Enjoy being more thoughtful this holiday season!
