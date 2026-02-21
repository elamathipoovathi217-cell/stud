from extensions import db

class Semester(db.Model):
    __tablename__ = 'semesters'
    
    id = db.Column(db.Integer, primary_key=True)
    semester_number = db.Column(db.Integer, nullable=False)  # 1-8
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    # Relationships - use unique backref names
    subjects = db.relationship('Subject', backref='semester_info', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('course_id', 'semester_number', name='unique_course_semester'),)