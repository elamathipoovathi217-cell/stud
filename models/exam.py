from extensions import db
from datetime import datetime

class Exam(db.Model):
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Internal 1, Internal 2, Semester Exam
    exam_type = db.Column(db.String(20), nullable=False)  # internal, external
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    duration_minutes = db.Column(db.Integer)
    max_marks = db.Column(db.Integer, default=100)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)
    
    # Relationships - use unique backref names and add overlaps
    subject = db.relationship('Subject', foreign_keys=[subject_id], 
                             backref='exam_list', lazy=True, 
                             overlaps="exam_schedules,subject_info")
    semester = db.relationship('Semester', backref='exam_list', lazy=True)
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_exams', lazy=True)
    room_allocations = db.relationship('RoomAllocation', backref='exam_info', lazy=True, 
                                      cascade='all, delete-orphan', overlaps="exam")
    invigilator_allocations = db.relationship('InvigilatorAllocation', backref='exam_info', 
                                             lazy=True, cascade='all, delete-orphan', 
                                             overlaps="exam")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'exam_type': self.exam_type,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else '',
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'start_time': str(self.start_time) if self.start_time else None,
            'end_time': str(self.end_time) if self.end_time else None,
            'is_published': self.is_published
        }