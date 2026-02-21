from extensions import db
from datetime import datetime

class TeacherSubject(db.Model):
    __tablename__ = 'teacher_subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'), nullable=False)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (db.UniqueConstraint('teacher_id', 'subject_id', 'academic_year_id', 
                                         name='unique_teacher_subject_year'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'subject_id': self.subject_id,
            'academic_year_id': self.academic_year_id,
            'semester_id': self.semester_id,
            'is_active': self.is_active
        }