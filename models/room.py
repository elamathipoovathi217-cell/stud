# models/room.py
from extensions import db
from datetime import datetime

class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    block = db.Column(db.String(10), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    has_projector = db.Column(db.Boolean, default=False)
    has_ac = db.Column(db.Boolean, default=False)
    is_lab = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - Fix the foreign key reference
    allocations = db.relationship('RoomAllocation', backref='room_details', lazy=True, 
                                 foreign_keys='RoomAllocation.room_id')
    
    def to_dict(self):
        return {
            'id': self.id,
            'room_number': self.room_number,
            'block': self.block,
            'capacity': self.capacity,
            'has_projector': self.has_projector,
            'has_ac': self.has_ac,
            'is_lab': self.is_lab,
            'is_active': self.is_active
        }