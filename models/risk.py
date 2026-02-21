from extensions import db
from datetime import datetime

class Risk(db.Model):
    __tablename__ = 'risk_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # Risk metrics
    risk_level = db.Column(db.String(20), nullable=False)  # Critical, High, Medium, Low
    risk_score = db.Column(db.Float)  # 0-100
    
    # Contributing factors
    attendance_percentage = db.Column(db.Float)
    internal_marks_avg = db.Column(db.Float)
    seminar_marks = db.Column(db.Float)
    assignment_marks = db.Column(db.Float)
    
    # ML prediction details
    prediction_probability = db.Column(db.Float)
    model_version = db.Column(db.String(50))
    
    # Recommendations
    improvement_suggestions = db.Column(db.Text)
    focus_areas = db.Column(db.Text)
    
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'))
    
    # Relationships - use unique backref names and add overlaps
    student = db.relationship('Student', foreign_keys=[student_id], 
                             backref='risk_predictions_list', lazy=True, 
                             overlaps="risk_records,student_info")
    semester = db.relationship('Semester', backref='risk_predictions_list', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'risk_level': self.risk_level,
            'risk_score': self.risk_score,
            'attendance_percentage': self.attendance_percentage,
            'internal_marks_avg': self.internal_marks_avg,
            'predicted_at': self.predicted_at.isoformat() if self.predicted_at else None
        }