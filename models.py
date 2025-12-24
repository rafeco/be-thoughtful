from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Person(db.Model):
    __tablename__ = 'people'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    person_type = db.Column(db.String(50), default='Other')
    card_preference = db.Column(db.String(20), default='E-card')
    gets_gift = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    gift_ideas = db.relationship('GiftIdea', backref='person', cascade='all, delete-orphan', lazy=True)
    tasks = db.relationship('Task', backref='person', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Person {self.name}>'


class GiftIdea(db.Model):
    __tablename__ = 'gift_ideas'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=False)
    idea = db.Column(db.Text, nullable=False)
    added_date = db.Column(db.Date, default=date.today)
    used_year = db.Column(db.Integer)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<GiftIdea {self.idea[:30]}>'


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=True)
    task_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.Date)
    year = db.Column(db.Integer, nullable=False)
    actual_gift = db.Column(db.Text)

    def __repr__(self):
        return f'<Task {self.task_type} - Year {self.year}>'


class Milestone(db.Model):
    __tablename__ = 'milestones'

    id = db.Column(db.Integer, primary_key=True)
    phase = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.Date)
    year = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint('phase', 'year', name='unique_phase_year'),)

    def __repr__(self):
        return f'<Milestone {self.phase} {self.year}>'


class AnnualSummary(db.Model):
    __tablename__ = 'annual_summary'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False, unique=True)
    total_people = db.Column(db.Integer)
    gifts_given = db.Column(db.Integer)
    handwritten_cards = db.Column(db.Integer)
    ecards_sent = db.Column(db.Integer)
    total_budget = db.Column(db.Float)
    completed_date = db.Column(db.Date)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<AnnualSummary {self.year}>'
