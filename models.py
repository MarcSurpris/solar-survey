from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    owns_home = db.Column(db.String(10), nullable=False)
    electric_bill = db.Column(db.String(50), nullable=False)
    credit_score = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f'<SurveyResponse {self.email}>'