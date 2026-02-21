# models/room_allocation.py
from extensions import db
from datetime import datetime

class RoomAllocation(db.Model):
    __tablename__ = 'room_allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)  # Add this line
    room_number = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer)
    allocated_students = db.Column(db.Integer, default=0)
    
    # Allocation details
    allocated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    allocated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # AI allocation metadata
    allocation_method = db.Column(db.String(50))  # manual, genetic, ant_colony, etc.
    allocation_score = db.Column(db.Float)  # Optimization score
    
    # Relationships - use unique backref names
    exam = db.relationship('Exam', foreign_keys=[exam_id], backref='room_allocations_list', 
                          lazy=True, overlaps="exam_info")
    room = db.relationship('Room', foreign_keys=[room_id], backref='allocations_list', lazy=True)
    allocator = db.relationship('User', foreign_keys=[allocated_by], 
                               backref='room_allocations_made', lazy=True)
    invigilator_allocations = db.relationship('InvigilatorAllocation', backref='room_info', 
                                             lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'exam_name': self.exam.name if self.exam else '',
            'room_id': self.room_id,
            'room_number': self.room_number,
            'capacity': self.capacity,
            'allocated_students': self.allocated_students,
            'allocation_method': self.allocation_method
        }