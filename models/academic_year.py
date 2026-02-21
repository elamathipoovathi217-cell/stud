from extensions import db

class AcademicYear(db.Model):
    __tablename__ = 'academic_years'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.String(9), unique=True, nullable=False)  # 2024-2025
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    
    # Relationships
    semesters = db.relationship('Semester', backref='academic_year', lazy=True)
    
    def __repr__(self):
        return f'<AcademicYear {self.year}>'