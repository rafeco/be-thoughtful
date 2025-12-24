from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional, Email


# Person type choices
PERSON_TYPES = [
    ('Family', 'Family'),
    ('Close Friend', 'Close Friend'),
    ('Colleague - Direct Report', 'Colleague - Direct Report'),
    ('Colleague - Peer', 'Colleague - Peer'),
    ('Colleague - Other', 'Colleague - Other'),
    ('Professional', 'Professional'),
    ('Other', 'Other'),
]

# Card preference choices
CARD_PREFERENCES = [
    ('Handwritten', 'Handwritten'),
    ('E-card', 'E-card'),
    ('None', 'None'),
]


class PersonForm(FlaskForm):
    """Form for adding/editing a person."""
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email/Phone', validators=[Optional()])
    person_type = SelectField('Type', choices=PERSON_TYPES, default='Other')
    card_preference = SelectField('Card Preference', choices=CARD_PREFERENCES, default='E-card')
    gets_gift = BooleanField('Gets Gift')
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save')


class GiftIdeaForm(FlaskForm):
    """Form for adding a gift idea."""
    person_id = HiddenField('Person ID')
    idea = TextAreaField('Gift Idea', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Add Idea')


class QuickGiftIdeaForm(FlaskForm):
    """Quick form for adding a gift idea (with person selection)."""
    person_id = SelectField('Person', coerce=int, validators=[DataRequired()])
    idea = StringField('Gift Idea', validators=[DataRequired()])
    notes = StringField('Notes', validators=[Optional()])


class ImportCSVForm(FlaskForm):
    """Form for CSV file upload."""
    csv_file = FileField('CSV File', validators=[FileRequired()])
    submit = SubmitField('Upload')


class CompleteGiftForm(FlaskForm):
    """Form for marking a gift as given."""
    actual_gift = TextAreaField('What did you give?', validators=[Optional()])
    submit = SubmitField('Mark as Given')
