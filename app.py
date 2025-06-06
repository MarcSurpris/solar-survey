from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField
from wtforms.validators import DataRequired, Email, Regexp, Optional
import os
from dotenv import load_dotenv  # Import python-dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Use environment variables for configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Use your original secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'  # Your database path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define the Survey model
class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    owns_home = db.Column(db.String(10), nullable=False)
    electric_bill = db.Column(db.String(50), nullable=False)
    credit_score = db.Column(db.String(20), nullable=True)

# Form for Step 1: Homeownership question
class HomeownerForm(FlaskForm):
    owns_home = RadioField('Are you the homeowner?', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
    submit = SubmitField('Next')

# Form for Step 2: Electric bill question
class ElectricBillForm(FlaskForm):
    electric_bill = RadioField('What is your average monthly electric bill?',
                               choices=[('$0-$99', '$0-$99'), ('$100-$199', '$100-$199'),
                                        ('$200-$299', '$200-$299'), ('$300-$399', '$300-$399'),
                                        ('$400+', '$400+')],
                               validators=[DataRequired()])
    submit = SubmitField('Next')

# Form for Step 3: Credit score question
class CreditScoreForm(FlaskForm):
    credit_score = StringField('Credit Score (300-850)', validators=[Optional(), Regexp(r'^\d{3,4}$', message="Credit score must be a number between 300 and 850")])
    submit = SubmitField('Next')

# Form for Step 4: Remaining fields
class SurveyForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Regexp(r'^\+?1?\d{10,15}$', message="Invalid phone number")])
    address = StringField('Address', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    zip_code = StringField('Zip Code', validators=[DataRequired(), Regexp(r'^\d{5}$', message="Invalid ZIP code")])
    submit = SubmitField('Submit')

# Create the database and verify schema
with app.app_context():
    try:
        db.create_all()
        # Verify the credit_score column exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('survey')]
        if 'credit_score' not in columns:
            print("Warning: 'credit_score' column missing in 'survey' table. Run migrations after deployment.")
    except Exception as e:
        print(f"Database setup error: {str(e)}")

# Route for Step 1: Homeownership question
@app.route('/', methods=['GET', 'POST'])
def survey_step1():
    form = HomeownerForm()
    if form.validate_on_submit():
        session['owns_home'] = form.owns_home.data
        return redirect(url_for('survey_step2'))
    return render_template('survey_step1.html', form=form)

# Route for Step 2: Electric bill question
@app.route('/survey_step2', methods=['GET', 'POST'])
def survey_step2():
    form = ElectricBillForm()
    if form.validate_on_submit():
        session['electric_bill'] = form.electric_bill.data
        return redirect(url_for('survey_step3'))
    return render_template('survey_step2.html', form=form)

# Route for Step 3: Credit score question
@app.route('/survey_step3', methods=['GET', 'POST'])
def survey_step3():
    form = CreditScoreForm()
    if form.validate_on_submit():
        session['credit_score'] = form.credit_score.data if form.credit_score.data else 'Unknown'
        return redirect(url_for('survey_step4'))
    return render_template('survey_step3.html', form=form)

# Route for Step 4: Remaining survey questions
@app.route('/survey_step4', methods=['GET', 'POST'])
def survey_step4():
    form = SurveyForm()
    if form.validate_on_submit():
        try:
            new_survey = Survey(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data,
                city=form.city.data,
                zip_code=form.zip_code.data,
                owns_home=session.get('owns_home', 'No'),
                electric_bill=session.get('electric_bill', '$0-$99'),
                credit_score=session.get('credit_score', 'Unknown')
            )
            db.session.add(new_survey)
            db.session.commit()
            session.pop('owns_home', None)
            session.pop('electric_bill', None)
            session.pop('credit_score', None)
            flash('Survey submitted successfully!', 'success')
            return redirect(url_for('submissions'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving survey: {str(e)}", 'danger')
    elif form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", 'danger')
    return render_template('survey_step4.html', form=form)

# Route to view and filter submissions
@app.route('/submissions')
def submissions():
    if os.getenv('FREEZE') == 'true':
        mock_submissions = [
            Survey(id=1, first_name='John', last_name='Doe', email='john.doe@example.com', phone='1234567890',
                   address='123 Main St', city='Springfield', zip_code='12345', owns_home='Yes',
                   electric_bill='$200-$299', credit_score='720')
        ]
        return render_template('submissions.html', submissions=mock_submissions)
    # Normal database query for dynamic app
    city_filter = request.args.get('city', '')
    owns_home_filter = request.args.get('owns_home', '')
    query = Survey.query
    if city_filter:
        query = query.filter_by(city=city_filter)
    if owns_home_filter:
        query = query.filter_by(owns_home=owns_home_filter)
    submissions = query.all()
    return render_template('submissions.html', submissions=submissions)
# Route to restart the survey
@app.route('/restart')
def restart():
    session.clear()
    return redirect(url_for('survey_step1'))

@app.route('/init_db')
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
    return "Database initialized successfully!"

# Route to reset the database
@app.route('/reset_db')
def reset_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
    flash('Database reset successfully.', 'success')
    return redirect(url_for('survey_step1'))

# Custom 500 error handler
@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')