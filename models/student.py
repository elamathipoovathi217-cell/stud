from extensions import db
from datetime import datetime
from .attendance import Attendance
from .subject import Subject
from .marks import Marks
from .risk import Risk

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(50), unique=True, nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    current_semester = db.Column(db.Integer, default=1)
    
    # Academic
    batch_year = db.Column(db.Integer)  # 2022, 2023, 2024, 2025
    admission_date = db.Column(db.Date, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships - use unique backref names
    attendance = db.relationship('Attendance', backref='student_info', lazy=True, cascade='all, delete-orphan')
    marks = db.relationship('Marks', backref='student_info', lazy=True, cascade='all, delete-orphan')
    risk_records = db.relationship('Risk', backref='student_info', lazy=True, cascade='all, delete-orphan')
    
    def get_attendance_percentage(self, subject_id=None, semester=None):
        """Calculate attendance percentage"""
        query = Attendance.query.filter_by(student_id=self.id)
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        if semester:
            query = query.join(Subject).filter(Subject.semester_id == semester)
        
        total_classes = query.count()
        if total_classes == 0:
            return 0
        
        present_classes = query.filter_by(status='present').count()
        return (present_classes / total_classes) * 100
    
    def get_total_marks(self, exam_type='internal'):
        """Calculate total marks (out of 20)"""
        marks = Marks.query.filter_by(student_id=self.id, exam_type=exam_type).all()
        if not marks:
            return 0
        
        total = 0
        for mark in marks:
            total += (mark.internal1 or 0) + (mark.internal2 or 0) + (mark.seminar or 0) + (mark.assignment or 0) + (mark.attendance_mark or 0)
        
        return total
    
    def get_risk_status(self):
        """Get current risk status"""
        latest_risk = Risk.query.filter_by(student_id=self.id).order_by(Risk.predicted_at.desc()).first()
        return latest_risk.risk_level if latest_risk else 'Unknown'
    
    def to_dict(self):
        return {
            'id': self.id,
            'registration_number': self.registration_number,
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email,
            'course_id': self.course_id,
            'department_id': self.department_id,
            'current_semester': self.current_semester,
            'batch_year': self.batch_year
        }