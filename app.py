#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import date
import csv
import io
import sys
from sqlalchemy.orm.attributes import flag_modified
from models import db, Person, GiftIdea, Task, Milestone, AnnualSummary, EcardDelivery
from forms import PersonForm, GiftIdeaForm, ImportCSVForm, ImportEcardDeliveriesForm, CompleteGiftForm
from utils import (
    get_active_year, get_current_phase, check_and_perform_rollover,
    perform_rollover, initialize_database, days_until_christmas,
    normalize_phone, format_phone
)

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
# Use absolute path to database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize database on first run
with app.app_context():
    initialize_database()

# Add custom template filters
app.jinja_env.filters['format_phone'] = format_phone


@app.route('/')
def dashboard():
    """Dashboard with timeline view and stats."""
    # Check for year rollover (automatic or from manual archive)
    rollover_summary = session.pop('rollover_summary', None) or check_and_perform_rollover()

    active_year = get_active_year()
    current_phase = get_current_phase()

    # Get stats for current year
    total_people = Person.query.filter_by(active=True).count()
    people_with_gifts = Person.query.filter_by(active=True, gets_gift=True).count()

    # Count handwritten cards needed
    handwritten_count = Person.query.filter_by(
        active=True,
        card_preference='Handwritten'
    ).count()

    # Count e-cards needed
    ecard_count = Person.query.filter_by(
        active=True,
        card_preference='E-card'
    ).count()

    # Calculate total budget
    total_budget = db.session.query(db.func.sum(Person.budget)).filter(
        Person.active == True,
        Person.gets_gift == True,
        Person.budget.isnot(None)
    ).scalar() or 0

    # Get milestones for current year
    milestones = Milestone.query.filter_by(year=active_year).order_by(Milestone.phase).all()

    # Get current phase milestone
    current_milestone = Milestone.query.filter_by(year=active_year, phase=current_phase).first()

    # Calculate milestone completion
    completed_milestones = sum(1 for m in milestones if m.completed)
    milestone_progress = (completed_milestones / len(milestones) * 100) if milestones else 0

    # Get tasks for current year
    gift_tasks_completed = Task.query.filter_by(
        year=active_year,
        task_type='gift_purchased',
        completed=True
    ).count()

    cards_written = Task.query.filter_by(
        year=active_year,
        task_type='card_written',
        completed=True
    ).count()

    gifts_given = Task.query.filter_by(
        year=active_year,
        task_type='gift_given',
        completed=True
    ).count()

    # Calculate days until Christmas
    countdown = days_until_christmas(active_year)

    return render_template('dashboard.html',
                           active_year=active_year,
                           current_phase=current_phase,
                           current_milestone=current_milestone,
                           total_people=total_people,
                           people_with_gifts=people_with_gifts,
                           handwritten_count=handwritten_count,
                           ecard_count=ecard_count,
                           total_budget=total_budget,
                           milestones=milestones,
                           milestone_progress=milestone_progress,
                           gift_tasks_completed=gift_tasks_completed,
                           cards_written=cards_written,
                           gifts_given=gifts_given,
                           countdown=countdown,
                           rollover_summary=rollover_summary)


@app.route('/people')
def people_list():
    """List all people with filtering."""
    person_type = request.args.get('type', '')
    card_pref = request.args.get('card', '')
    gift_status = request.args.get('gift', '')

    query = Person.query.filter_by(active=True)

    if person_type:
        query = query.filter_by(person_type=person_type)
    if card_pref:
        query = query.filter_by(card_preference=card_pref)
    if gift_status:
        gets_gift = gift_status == 'yes'
        query = query.filter_by(gets_gift=gets_gift)

    people = query.order_by(Person.name).all()

    return render_template('people_list.html', people=people)


@app.route('/people/new', methods=['GET', 'POST'])
def person_new():
    """Add a new person."""
    form = PersonForm()

    if form.validate_on_submit():
        # Check for duplicates
        duplicates = []

        # Check name
        if Person.query.filter_by(active=True, name=form.name.data).first():
            duplicates.append(f'name "{form.name.data}"')

        # Check email if provided
        if form.email.data and form.email.data.strip():
            if Person.query.filter_by(active=True, email=form.email.data).first():
                duplicates.append(f'email "{form.email.data}"')

        # Check phone if provided
        if form.phone.data and form.phone.data.strip():
            normalized = normalize_phone(form.phone.data)
            if normalized and Person.query.filter_by(active=True, phone=normalized).first():
                duplicates.append(f'phone "{form.phone.data}"')

        if duplicates:
            flash(f'Warning: A person with the same {", ".join(duplicates)} already exists!', 'warning')
            return render_template('person_form.html', form=form, title='Add Person')

        person = Person(
            name=form.name.data,
            email=form.email.data,
            phone=normalize_phone(form.phone.data),
            person_type=form.person_type.data,
            card_preference=form.card_preference.data,
            gets_gift=form.gets_gift.data,
            budget=form.budget.data,
            card_addressee=form.card_addressee.data,
            notes=form.notes.data,
            ai_chat_link=form.ai_chat_link.data
        )
        db.session.add(person)
        db.session.commit()

        flash(f'Added {person.name}!', 'success')
        return redirect(url_for('people_list'))

    return render_template('person_form.html', form=form, title='Add Person')


@app.route('/people/<int:id>')
def person_detail(id):
    """View person details with history."""
    person = Person.query.get_or_404(id)
    active_year = get_active_year()

    # Get gift ideas (sorted by most recent first)
    gift_ideas = GiftIdea.query.filter_by(person_id=id).order_by(
        GiftIdea.added_date.desc()
    ).all()

    # Get tasks for this person across all years
    tasks_by_year = {}
    all_tasks = Task.query.filter_by(person_id=id).order_by(Task.year.desc()).all()

    for task in all_tasks:
        if task.year not in tasks_by_year:
            tasks_by_year[task.year] = []
        tasks_by_year[task.year].append(task)

    # Get gift history (completed gift_given tasks with actual gifts)
    gift_history = Task.query.filter_by(
        person_id=id,
        task_type='gift_given',
        completed=True
    ).order_by(Task.year.desc()).all()

    return render_template('person_detail.html',
                           person=person,
                           gift_ideas=gift_ideas,
                           tasks_by_year=tasks_by_year,
                           gift_history=gift_history,
                           active_year=active_year)


@app.route('/people/<int:id>/edit', methods=['GET', 'POST'])
def person_edit(id):
    """Edit a person."""
    person = Person.query.get_or_404(id)
    form = PersonForm(obj=person)

    if form.validate_on_submit():
        person.name = form.name.data
        person.email = form.email.data
        person.phone = normalize_phone(form.phone.data)
        person.person_type = form.person_type.data
        person.card_preference = form.card_preference.data
        person.gets_gift = form.gets_gift.data
        person.budget = form.budget.data
        person.card_addressee = form.card_addressee.data
        person.notes = form.notes.data
        person.ai_chat_link = form.ai_chat_link.data

        db.session.commit()
        flash(f'Updated {person.name}!', 'success')
        return redirect(url_for('person_detail', id=person.id))

    return render_template('person_form.html', form=form, title='Edit Person', person=person)


@app.route('/people/<int:id>/delete', methods=['POST'])
def person_delete(id):
    """Delete a person (soft delete)."""
    person = Person.query.get_or_404(id)
    person.active = False
    db.session.commit()

    flash(f'Removed {person.name}.', 'info')
    return redirect(url_for('people_list'))


@app.route('/people/<int:id>/add-idea', methods=['POST'])
def add_gift_idea(id):
    """Add a gift idea for a person."""
    person = Person.query.get_or_404(id)

    idea_text = request.form.get('idea', '').strip()
    notes = request.form.get('notes', '').strip()

    if idea_text:
        gift_idea = GiftIdea(
            person_id=person.id,
            idea=idea_text,
            notes=notes
        )
        db.session.add(gift_idea)
        db.session.commit()
        flash('Gift idea added!', 'success')
    else:
        flash('Please enter a gift idea.', 'warning')

    return redirect(url_for('person_detail', id=person.id))


@app.route('/import', methods=['GET', 'POST'])
def import_csv():
    """Import people from CSV."""
    form = ImportCSVForm()

    if form.validate_on_submit():
        csv_file = request.files['csv_file']

        # Read CSV
        stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        imported_count = 0
        skipped_count = 0

        for row in csv_reader:
            name = row.get('Full Name', '').strip()
            contact_info = row.get('Email/Phone Number', '').strip()

            if not name:
                continue

            # Detect if contact_info is email or phone
            email = None
            phone = None
            if contact_info:
                if '@' in contact_info:
                    email = contact_info
                else:
                    phone = normalize_phone(contact_info)

            # Check for duplicate (by name and either email or phone)
            existing = None
            if email:
                existing = Person.query.filter_by(name=name, email=email, active=True).first()
            elif phone:
                existing = Person.query.filter_by(name=name, phone=phone, active=True).first()
            else:
                existing = Person.query.filter_by(name=name, active=True).first()

            if existing:
                skipped_count += 1
                continue

            # Create new person with defaults
            person = Person(
                name=name,
                email=email,
                phone=phone,
                person_type='Other',
                card_preference='E-card',
                gets_gift=False
            )
            db.session.add(person)
            imported_count += 1

        db.session.commit()

        flash(f'Imported {imported_count} people. Skipped {skipped_count} duplicates.', 'success')
        return redirect(url_for('people_list'))

    return render_template('import.html', form=form)


@app.route('/import-ecard-deliveries', methods=['GET', 'POST'])
def import_ecard_deliveries():
    """Import e-card delivery data from Paperless Post CSV."""
    form = ImportEcardDeliveriesForm()

    # Set default year: most recently completed season
    # If we're Jan-Aug, default to previous year
    # If we're Sep-Dec, default to current year
    today = date.today()
    if today.month <= 8:
        default_year = today.year - 1
    else:
        default_year = today.year

    if request.method == 'GET':
        form.year.data = default_year

    if form.validate_on_submit():
        csv_file = request.files['csv_file']
        delivery_year = form.year.data

        # Read CSV
        stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        imported_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        for row in csv_reader:
            name = row.get('Full Name', '').strip()
            contact_info = row.get('Email/Phone Number', '').strip()
            status = row.get('Status', '').strip()
            message = row.get('Message', '').strip()
            contact_type = row.get('Type', '').strip()  # 'email' or 'sms'

            if not name or not contact_info:
                continue

            # Normalize phone if it's SMS
            if contact_type == 'sms':
                contact_info = normalize_phone(contact_info)

            # Find matching person by contact info
            person = None
            if contact_type == 'sms' and contact_info:
                person = Person.query.filter_by(phone=contact_info, active=True).first()
            elif contact_type == 'email':
                person = Person.query.filter_by(email=contact_info, active=True).first()

            if not person:
                # Try to find by name as fallback
                person = Person.query.filter_by(name=name, active=True).first()
                if not person:
                    errors.append(f'Could not find person: {name} ({contact_info})')
                    skipped_count += 1
                    continue

            # Check if delivery record already exists
            existing = EcardDelivery.query.filter_by(
                person_id=person.id,
                year=delivery_year,
                contact_used=contact_info
            ).first()

            if existing:
                # Update existing record
                existing.status = status
                existing.message = message if message else existing.message
                existing.imported_date = date.today()
                updated_count += 1
            else:
                # Create new delivery record
                delivery = EcardDelivery(
                    person_id=person.id,
                    year=delivery_year,
                    status=status,
                    contact_used=contact_info,
                    contact_type=contact_type,
                    message=message if message else None
                )
                db.session.add(delivery)
                imported_count += 1

        db.session.commit()

        flash(f'Imported {imported_count} new deliveries, updated {updated_count} for {delivery_year}. Skipped {skipped_count}.', 'success')
        if errors:
            flash(f'Errors: {"; ".join(errors[:5])}', 'warning')

        return redirect(url_for('ecard_deliveries', year=delivery_year))

    return render_template('import_ecard_deliveries.html', form=form, default_year=default_year)


@app.route('/shopping-list')
def shopping_list():
    """View all people who get gifts and their ideas."""
    active_year = get_active_year()

    # Get all people who get gifts
    people = Person.query.filter_by(active=True, gets_gift=True).order_by(Person.name).all()

    # For each person, get their gift ideas and task status
    shopping_data = []
    for person in people:
        # Get unused gift ideas
        ideas = GiftIdea.query.filter_by(
            person_id=person.id,
            used_year=None
        ).order_by(GiftIdea.added_date.desc()).all()

        # Get task status for current year
        purchased_task = Task.query.filter_by(
            person_id=person.id,
            year=active_year,
            task_type='gift_purchased'
        ).first()

        given_task = Task.query.filter_by(
            person_id=person.id,
            year=active_year,
            task_type='gift_given'
        ).first()

        shopping_data.append({
            'person': person,
            'ideas': ideas,
            'purchased': purchased_task.completed if purchased_task else False,
            'given': given_task.completed if given_task else False
        })

    return render_template('shopping_list.html',
                           shopping_data=shopping_data,
                           active_year=active_year)


@app.route('/writing-queue')
def writing_queue():
    """View all people getting handwritten cards."""
    active_year = get_active_year()

    # Get all people with handwritten card preference
    people = Person.query.filter_by(
        active=True,
        card_preference='Handwritten'
    ).order_by(Person.name).all()

    # For each person, get card writing status
    writing_data = []
    for person in people:
        card_task = Task.query.filter_by(
            person_id=person.id,
            year=active_year,
            task_type='card_written'
        ).first()

        writing_data.append({
            'person': person,
            'completed': card_task.completed if card_task else False,
            'task_id': card_task.id if card_task else None
        })

    return render_template('writing_queue.html',
                           writing_data=writing_data,
                           active_year=active_year)


@app.route('/milestones')
def milestones():
    """View and manage milestones."""
    active_year = get_active_year()
    milestones = Milestone.query.filter_by(year=active_year).order_by(Milestone.phase).all()

    return render_template('milestones.html',
                           milestones=milestones,
                           active_year=active_year)


@app.route('/milestones/<int:id>/toggle', methods=['POST'])
def milestone_toggle(id):
    """Toggle milestone completion."""
    milestone = Milestone.query.get_or_404(id)

    milestone.completed = not milestone.completed
    milestone.completed_date = date.today() if milestone.completed else None

    db.session.commit()

    return jsonify({
        'success': True,
        'completed': milestone.completed
    })


@app.route('/milestones/<int:id>/update-link', methods=['POST'])
def milestone_update_link(id):
    """Update milestone AI chat link."""
    milestone = Milestone.query.get_or_404(id)

    data = request.get_json()
    ai_chat_link = data.get('ai_chat_link', '').strip()

    milestone.ai_chat_link = ai_chat_link if ai_chat_link else None
    db.session.commit()

    return jsonify({
        'success': True,
        'ai_chat_link': milestone.ai_chat_link
    })


@app.route('/milestones/<int:id>/toggle-subtask', methods=['POST'])
def milestone_toggle_subtask(id):
    """Toggle a subtask completion for a milestone."""
    milestone = Milestone.query.get_or_404(id)
    data = request.get_json()
    subtask_index = data.get('subtask_index')

    if subtask_index is None:
        return jsonify({'success': False, 'error': 'Missing subtask_index'}), 400

    # Initialize completed_subtasks if None
    if milestone.completed_subtasks is None:
        milestone.completed_subtasks = []

    # Toggle the subtask
    if subtask_index in milestone.completed_subtasks:
        milestone.completed_subtasks.remove(subtask_index)
    else:
        milestone.completed_subtasks.append(subtask_index)

    # Mark the field as modified so SQLAlchemy detects the change
    flag_modified(milestone, 'completed_subtasks')

    # Check if all subtasks are complete
    total_subtasks = len(milestone.subtasks) if milestone.subtasks else 0
    all_complete = len(milestone.completed_subtasks) == total_subtasks and total_subtasks > 0

    # Auto-complete milestone if all subtasks done
    if all_complete and not milestone.completed:
        milestone.completed = True
        milestone.completed_date = date.today()
    elif not all_complete and milestone.completed:
        # Uncomplete if user unchecks a subtask
        milestone.completed = False
        milestone.completed_date = None

    db.session.commit()

    return jsonify({
        'success': True,
        'completed_subtasks': milestone.completed_subtasks,
        'milestone_completed': milestone.completed
    })


@app.route('/archive-year', methods=['POST'])
def archive_year():
    """Manually archive the current year and roll over to the next."""
    active_year = get_active_year()

    # Check if this year is already archived
    existing_summary = AnnualSummary.query.filter_by(year=active_year).first()
    if existing_summary:
        flash(f'{active_year} has already been archived!', 'warning')
        return redirect(url_for('dashboard'))

    # Perform the rollover
    next_year = active_year + 1
    rollover_summary = perform_rollover(active_year, next_year)

    # Store rollover summary in session to display the modal
    session['rollover_summary'] = rollover_summary

    flash(f'Successfully archived {active_year} and created milestones for {next_year}!', 'success')

    # Redirect to dashboard which will show the rollover modal
    return redirect(url_for('dashboard'))


@app.route('/archive')
def archive_list():
    """View list of archived years."""
    summaries = AnnualSummary.query.order_by(AnnualSummary.year.desc()).all()
    active_year = get_active_year()

    return render_template('archive_list.html', summaries=summaries, active_year=active_year)


@app.route('/archive/<int:year>')
def archive_detail(year):
    """View details of a specific archived year."""
    summary = AnnualSummary.query.filter_by(year=year).first_or_404()

    # Get all tasks for this year
    tasks = Task.query.filter_by(year=year).all()

    # Get milestones for this year
    milestones = Milestone.query.filter_by(year=year).order_by(Milestone.phase).all()

    # Get people who received gifts
    gift_recipients = []
    gift_tasks = Task.query.filter_by(
        year=year,
        task_type='gift_given',
        completed=True
    ).all()

    for task in gift_tasks:
        if task.person:
            gift_recipients.append({
                'person': task.person,
                'gift': task.actual_gift or 'No details recorded'
            })

    # Get e-card delivery stats for this year
    total_deliveries = EcardDelivery.query.filter_by(year=year).count()
    messages_received = EcardDelivery.query.filter(
        EcardDelivery.year == year,
        EcardDelivery.message.isnot(None),
        EcardDelivery.message != ''
    ).count()
    bounced_count = EcardDelivery.query.filter_by(year=year, status='Bounced').count()

    return render_template('archive_detail.html',
                           summary=summary,
                           milestones=milestones,
                           gift_recipients=gift_recipients,
                           total_deliveries=total_deliveries,
                           messages_received=messages_received,
                           bounced_count=bounced_count)


@app.route('/tasks/create/<int:person_id>/<task_type>', methods=['POST'])
def task_create(person_id, task_type):
    """Create a task for a person in the current year."""
    active_year = get_active_year()

    # Check if task already exists
    existing = Task.query.filter_by(
        person_id=person_id,
        year=active_year,
        task_type=task_type
    ).first()

    if not existing:
        task = Task(
            person_id=person_id,
            year=active_year,
            task_type=task_type,
            description=f'{task_type} for {active_year}'
        )
        db.session.add(task)
        db.session.commit()

        return jsonify({'success': True, 'task_id': task.id})

    return jsonify({'success': True, 'task_id': existing.id})


@app.route('/tasks/<int:id>/toggle', methods=['POST'])
def task_toggle(id):
    """Toggle task completion."""
    task = Task.query.get_or_404(id)

    task.completed = not task.completed
    task.completed_date = date.today() if task.completed else None

    db.session.commit()

    return jsonify({
        'success': True,
        'completed': task.completed
    })


@app.route('/tasks/<int:id>/complete-gift', methods=['POST'])
def complete_gift_task(id):
    """Mark a gift as given with details."""
    task = Task.query.get_or_404(id)

    actual_gift = request.form.get('actual_gift', '').strip()

    task.completed = True
    task.completed_date = date.today()
    task.actual_gift = actual_gift

    db.session.commit()

    flash('Gift marked as given!', 'success')
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/api/quick-add-idea', methods=['POST'])
def api_quick_add_idea():
    """AJAX endpoint for quick gift idea entry."""
    data = request.get_json()

    person_id = data.get('person_id')
    idea = data.get('idea', '').strip()
    notes = data.get('notes', '').strip()

    if not person_id or not idea:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    person = Person.query.get(person_id)
    if not person:
        return jsonify({'success': False, 'error': 'Person not found'}), 404

    gift_idea = GiftIdea(
        person_id=person_id,
        idea=idea,
        notes=notes
    )
    db.session.add(gift_idea)
    db.session.commit()

    return jsonify({
        'success': True,
        'idea_id': gift_idea.id
    })


@app.route('/api/rollover-check', methods=['GET'])
def api_rollover_check():
    """AJAX endpoint to check if rollover is needed."""
    rollover_summary = check_and_perform_rollover()

    if rollover_summary:
        return jsonify({
            'rollover_needed': True,
            'summary': rollover_summary
        })

    return jsonify({'rollover_needed': False})


@app.route('/ecard-deliveries')
def ecard_deliveries():
    """View e-card delivery status for all people."""
    # Get year from query param, or default to most recent season
    today = date.today()
    if today.month <= 8:
        default_year = today.year - 1
    else:
        default_year = today.year

    selected_year = request.args.get('year', default_year, type=int)

    # Get all deliveries for selected year
    deliveries = EcardDelivery.query.filter_by(year=selected_year).all()

    # Group by person
    delivery_data = {}
    for delivery in deliveries:
        person_id = delivery.person_id
        if person_id not in delivery_data:
            delivery_data[person_id] = {
                'person': delivery.person,
                'deliveries': []
            }
        delivery_data[person_id]['deliveries'].append(delivery)

    # Sort by person name
    sorted_data = sorted(delivery_data.values(), key=lambda x: x['person'].name)

    # Get available years for year selector
    available_years = db.session.query(EcardDelivery.year).distinct().order_by(EcardDelivery.year.desc()).all()
    available_years = [y[0] for y in available_years]

    return render_template('ecard_deliveries.html',
                           delivery_data=sorted_data,
                           selected_year=selected_year,
                           available_years=available_years)


@app.route('/contact-issues')
def contact_issues():
    """View people with bounced e-cards who need contact info updates."""
    # Get year from query param, or default to most recent season
    today = date.today()
    if today.month <= 8:
        default_year = today.year - 1
    else:
        default_year = today.year

    selected_year = request.args.get('year', default_year, type=int)

    # Get all bounced deliveries for selected year
    bounced_deliveries = EcardDelivery.query.filter_by(
        year=selected_year,
        status='Bounced'
    ).all()

    # Group by person to avoid duplicates
    people_with_issues = {}
    for delivery in bounced_deliveries:
        person_id = delivery.person_id
        if person_id not in people_with_issues:
            people_with_issues[person_id] = {
                'person': delivery.person,
                'bounced_contacts': []
            }
        people_with_issues[person_id]['bounced_contacts'].append({
            'contact': delivery.contact_used,
            'type': delivery.contact_type
        })

    # Sort by person name
    sorted_data = sorted(people_with_issues.values(), key=lambda x: x['person'].name)

    # Get available years for year selector
    available_years = db.session.query(EcardDelivery.year).distinct().order_by(EcardDelivery.year.desc()).all()
    available_years = [y[0] for y in available_years]

    return render_template('contact_issues.html',
                           people_with_issues=sorted_data,
                           selected_year=selected_year,
                           available_years=available_years)


@app.route('/ecard-messages')
def ecard_messages():
    """View all messages received from e-card recipients."""
    # Get year from query param, or default to most recent season
    today = date.today()
    if today.month <= 8:
        default_year = today.year - 1
    else:
        default_year = today.year

    selected_year = request.args.get('year', default_year, type=int)

    # Get all deliveries with messages for selected year
    deliveries_with_messages = EcardDelivery.query.filter(
        EcardDelivery.year == selected_year,
        EcardDelivery.message.isnot(None),
        EcardDelivery.message != ''
    ).order_by(EcardDelivery.imported_date.desc()).all()

    # Get available years for year selector
    available_years = db.session.query(EcardDelivery.year).distinct().order_by(EcardDelivery.year.desc()).all()
    available_years = [y[0] for y in available_years]

    return render_template('ecard_messages.html',
                           deliveries=deliveries_with_messages,
                           selected_year=selected_year,
                           available_years=available_years)


@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True, port=7234)
