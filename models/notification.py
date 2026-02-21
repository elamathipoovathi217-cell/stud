from extensions import db
from datetime import datetime
import json

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # exam, result, meeting, announcement
    
    # Target audience
    target_role = db.Column(db.String(50))  # all, principal, hod, teacher, student
    target_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    target_course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    target_semester = db.Column(db.Integer)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_for = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    
    # Status
    is_published = db.Column(db.Boolean, default=False)
    
    # Read tracking - store as JSON string
    _read_by = db.Column(db.Text, default='[]')  # JSON string of user ids who read
    
    # Links
    action_url = db.Column(db.String(200))
    attachment = db.Column(db.String(200))
    
    # Relationships
    department = db.relationship('Department', foreign_keys=[target_department_id], backref='notifications')
    course = db.relationship('Course', foreign_keys=[target_course_id], backref='notifications')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_notifications')
    
    @property
    def read_by(self):
        """Get list of user ids who read this notification"""
        if self._read_by:
            return json.loads(self._read_by)
        return []
    
    @read_by.setter
    def read_by(self, value):
        """Set list of user ids who read this notification"""
        self._read_by = json.dumps(value)
    
    def mark_as_read(self, user_id):
        """Mark notification as read by user"""
        read_list = self.read_by
        if user_id not in read_list:
            read_list.append(user_id)
            self.read_by = read_list
            db.session.commit()
    
    def is_read_by(self, user_id):
        """Check if notification is read by user"""
        return user_id in self.read_by
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_published': self.is_published,
            'read_count': len(self.read_by)
        }