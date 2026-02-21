from extensions import db
from datetime import datetime

class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    feedback_type = db.Column(db.String(50))  # teacher, course, system, suggestion
    
    # Target (if feedback about teacher/course)
    target_id = db.Column(db.Integer)  # teacher_id or course_id
    target_type = db.Column(db.String(50))  # teacher, course
    
    rating = db.Column(db.Integer)  # 1-5
    comments = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_anonymous = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='feedbacks')
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='resolved_feedbacks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'feedback_type': self.feedback_type,
            'rating': self.rating,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_resolved': self.is_resolved
        }