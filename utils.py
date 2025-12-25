from datetime import date, datetime
from models import db, Milestone, AnnualSummary, Task, GiftIdea, Person

# Subtasks for each milestone phase
MILESTONE_SUBTASKS = {
    'September': [
        'Review previous year\'s gifts and cards',
        'Brainstorm gift ideas for each person getting a gift',
        'Finalize handwritten card list',
        'Finalize e-card recipient list',
    ],
    'October': [
        'Purchase all family gifts',
        'Order physical cards from vendor',
        'Confirm card quantities match list',
    ],
    'November': [
        'Write all handwritten cards',
        'Purchase all colleague gifts',
        'Wrap family gifts',
    ],
    'December': [
        'Draft and finalize e-card message',
        'Send e-cards to all recipients',
        'Distribute colleague gifts',
        'Wrap remaining gifts',
        'Deliver/mail all gifts and cards',
    ],
}


def get_active_year():
    """Return the year we're currently planning for.

    September 1 - December 31: Current year (unless already archived)
    January 1 - August 31: Next year

    If the current year has been archived, return next year instead.
    """
    today = date.today()
    base_year = today.year if today.month >= 9 else today.year + 1

    # Check if this year has already been archived
    from models import AnnualSummary
    if AnnualSummary.query.filter_by(year=base_year).first():
        # Already archived, move to next year
        return base_year + 1

    return base_year


def get_current_phase():
    """Return the current planning phase based on today's date."""
    today = date.today()
    active_year = get_active_year()

    # If we're planning for next year (Jan-Aug), we're in pre-planning
    if today.year < active_year:
        return 'Pre-planning'

    # If we're in the active year (Sep-Dec)
    if today.month == 9:
        return 'September'
    elif today.month == 10:
        return 'October'
    elif today.month == 11:
        return 'November'
    elif today.month == 12:
        return 'December'
    else:
        return 'Pre-planning'


def days_until_christmas(active_year):
    """Calculate the number of days until Christmas of the active year.

    Returns a dict with:
    - days: number of days until Christmas
    - christmas_date: the date of Christmas we're counting down to
    """
    today = date.today()
    christmas = date(active_year, 12, 25)

    delta = christmas - today
    days = delta.days

    return {
        'days': days,
        'christmas_date': christmas
    }


def seed_milestones_for_year(year):
    """Create milestone templates for a given year."""
    milestone_templates = [
        {
            'phase': 'September',
            'description': 'Brainstorm gifts and draft card list',
        },
        {
            'phase': 'October',
            'description': 'Purchase gifts for family and order physical cards',
        },
        {
            'phase': 'November',
            'description': 'Write handwritten cards and buy colleague gifts',
        },
        {
            'phase': 'December',
            'description': 'Distribute colleague gifts, send e-cards, and wrap everything',
        },
    ]

    for template in milestone_templates:
        # Check if milestone already exists for this phase and year
        existing = Milestone.query.filter_by(phase=template['phase'], year=year).first()
        if not existing:
            # Get subtasks from template
            subtasks = MILESTONE_SUBTASKS.get(template['phase'], [])

            milestone = Milestone(
                phase=template['phase'],
                description=template['description'],
                year=year,
                completed=False,
                subtasks=subtasks,
                completed_subtasks=[]
            )
            db.session.add(milestone)

    db.session.commit()


def check_and_perform_rollover():
    """Check if year rollover is needed and perform it if necessary.

    Returns a dict with rollover info if performed, None otherwise.
    """
    active_year = get_active_year()

    # Get the most recent milestone year
    latest_milestone = Milestone.query.order_by(Milestone.year.desc()).first()

    # If no milestones exist, seed for active year
    if not latest_milestone:
        seed_milestones_for_year(active_year)
        return None

    # If latest milestone year is less than active year, we need to rollover
    if latest_milestone.year < active_year:
        rollover_year = latest_milestone.year
        return perform_rollover(rollover_year, active_year)

    return None


def perform_rollover(old_year, new_year):
    """Perform the year rollover process.

    1. Create annual summary for completed year
    2. Mark gift ideas as used if gift was given
    3. Create new milestones for new year
    4. Reset task completion states

    Returns summary dict with stats from old year.
    """
    # Calculate stats for annual summary
    total_people = Person.query.filter_by(active=True).count()

    # Count completed gift tasks
    gifts_given = Task.query.filter_by(
        year=old_year,
        task_type='gift_given',
        completed=True
    ).count()

    # Count completed handwritten cards
    handwritten_cards = Task.query.filter(
        Task.year == old_year,
        Task.task_type == 'card_written',
        Task.completed == True
    ).join(Person).filter(
        Person.card_preference == 'Handwritten'
    ).count()

    # Count completed e-cards
    ecards_sent = Task.query.filter(
        Task.year == old_year,
        Task.task_type == 'card_written',
        Task.completed == True
    ).join(Person).filter(
        Person.card_preference == 'E-card'
    ).count()

    # Create annual summary
    summary = AnnualSummary(
        year=old_year,
        total_people=total_people,
        gifts_given=gifts_given,
        handwritten_cards=handwritten_cards,
        ecards_sent=ecards_sent,
        completed_date=date.today()
    )
    db.session.add(summary)

    # Mark gift ideas as used if gift was given
    completed_gift_tasks = Task.query.filter_by(
        year=old_year,
        task_type='gift_given',
        completed=True
    ).all()

    for task in completed_gift_tasks:
        if task.person_id:
            # Find most recent unused gift idea for this person
            gift_idea = GiftIdea.query.filter_by(
                person_id=task.person_id,
                used_year=None
            ).order_by(GiftIdea.added_date.desc()).first()

            if gift_idea:
                gift_idea.used_year = old_year

    # Create new milestones for new year
    seed_milestones_for_year(new_year)

    db.session.commit()

    # Return summary for display to user
    return {
        'year': old_year,
        'total_people': total_people,
        'gifts_given': gifts_given,
        'handwritten_cards': handwritten_cards,
        'ecards_sent': ecards_sent
    }


def initialize_database():
    """Initialize database on first run."""
    db.create_all()

    # Seed milestones for active year if none exist
    active_year = get_active_year()
    existing_milestones = Milestone.query.filter_by(year=active_year).count()

    if existing_milestones == 0:
        seed_milestones_for_year(active_year)
