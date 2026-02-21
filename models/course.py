from extensions import db
from datetime import datetime

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    duration_years = db.Column(db.Integer, default=3)  # 3 or 4 years
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - use different backref names to avoid conflicts
    students = db.relationship('Student', backref='enrolled_course', lazy=True)
    semesters = db.relationship('Semester', backref='parent_course', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'duration_years': self.duration_years,
            'department_id': self.department_id
        }