from extensions import db
from datetime import datetime
import json

class Holiday(db.Model):
    __tablename__ = 'holidays'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    holiday_type = db.Column(db.String(50))  # public, academic, religious
    description = db.Column(db.Text)
    
    # Applicable to - store as JSON
    _applicable_departments = db.Column(db.Text, default='[]')  # JSON string of department ids
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_holidays')
    
    __table_args__ = (db.UniqueConstraint('date', 'name', name='unique_holiday'),)
    
    @property
    def applicable_departments(self):
        """Get list of department ids"""
        if self._applicable_departments:
            return json.loads(self._applicable_departments)
        return []
    
    @applicable_departments.setter
    def applicable_departments(self, value):
        """Set list of department ids"""
        self._applicable_departments = json.dumps(value)
    
    def is_applicable_to(self, department_id):
        """Check if holiday applies to department"""
        if not self._applicable_departments or self._applicable_departments == '[]':
            return True  # Applicable to all
        return department_id in self.applicable_departments
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date.isoformat() if self.date else None,
            'holiday_type': self.holiday_type,
            'description': self.description,
            'applicable_departments': self.applicable_departments
        }