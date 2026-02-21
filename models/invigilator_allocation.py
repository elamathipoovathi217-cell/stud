from extensions import db
from datetime import datetime

class InvigilatorAllocation(db.Model):
    __tablename__ = 'invigilator_allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_allocation_id = db.Column(db.Integer, db.ForeignKey('room_allocations.id'))
    
    # Duty details
    duty_date = db.Column(db.Date, nullable=False)
    duty_time = db.Column(db.String(50))  # morning, afternoon, full day
    
    # Status
    is_confirmed = db.Column(db.Boolean, default=False)
    confirmed_at = db.Column(db.DateTime)
    
    # Allocation metadata
    allocated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    allocated_at = db.Column(db.DateTime, default=datetime.utcnow)
    allocation_method = db.Column(db.String(50))  # manual, genetic, etc.
    
    # Relationships - use unique backref names
    exam = db.relationship('Exam', foreign_keys=[exam_id], backref='invigilator_allocations_list', 
                          lazy=True, overlaps="exam_info")
    teacher = db.relationship('User', foreign_keys=[teacher_id], 
                             backref='invigilation_duties_list', lazy=True)
    room_allocation = db.relationship('RoomAllocation', foreign_keys=[room_allocation_id], 
                                     backref='invigilator_allocations_list', lazy=True, 
                                     overlaps="room_info")
    allocator = db.relationship('User', foreign_keys=[allocated_by], 
                               backref='assigned_invigilations_list', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('exam_id', 'teacher_id', 'room_allocation_id', 
                                         name='unique_invigilator_allocation'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'exam_name': self.exam.name if self.exam else '',
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.full_name if self.teacher else '',
            'room_allocation_id': self.room_allocation_id,
            'room_number': self.room_allocation.room_number if self.room_allocation else '',
            'duty_date': self.duty_date.isoformat() if self.duty_date else None,
            'duty_time': self.duty_time,
            'is_confirmed': self.is_confirmed
        }