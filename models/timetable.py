from extensions import db
from datetime import datetime

class Timetable(db.Model):
    __tablename__ = 'timetable'
    
    id = db.Column(db.Integer, primary_key=True)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    day_of_week = db.Column(db.String(10), nullable=False)  # Monday, Tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room_number = db.Column(db.String(20))
    
    # Academic details
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # AI allocation metadata
    allocation_method = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    semester = db.relationship('Semester', backref='timetable_entries')
    subject = db.relationship('Subject', backref='timetable_entries')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='timetable_entries')
    academic_year = db.relationship('AcademicYear', backref='timetable_entries')
    
    def to_dict(self):
        return {
            'id': self.id,
            'semester_id': self.semester_id,
            'semester_number': self.semester.semester_number if self.semester else '',
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else '',
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.full_name if self.teacher else '',
            'day_of_week': self.day_of_week,
            'start_time': str(self.start_time),
            'end_time': str(self.end_time),
            'room_number': self.room_number
        }