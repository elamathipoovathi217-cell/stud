from extensions import db
from datetime import datetime
import json

class AcademicCalendar(db.Model):
    __tablename__ = 'academic_calendar'
    
    id = db.Column(db.Integer, primary_key=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    event_name = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50))  # term_start, term_end, exam, holiday, event
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)
    
    # Applicability - store as JSON
    _applicable_courses = db.Column(db.Text, default='[]')  # JSON string of course ids
    _applicable_semesters = db.Column(db.Text, default='[]')  # JSON string of semester numbers
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    academic_year = db.relationship('AcademicYear', backref='calendar_events')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_calendar_events')
    
    @property
    def applicable_courses(self):
        """Get list of course ids"""
        if self._applicable_courses:
            return json.loads(self._applicable_courses)
        return []
    
    @applicable_courses.setter
    def applicable_courses(self, value):
        """Set list of course ids"""
        self._applicable_courses = json.dumps(value)
    
    @property
    def applicable_semesters(self):
        """Get list of semester numbers"""
        if self._applicable_semesters:
            return json.loads(self._applicable_semesters)
        return []
    
    @applicable_semesters.setter
    def applicable_semesters(self, value):
        """Set list of semester numbers"""
        self._applicable_semesters = json.dumps(value)
    
    def to_dict(self):
        return {
            'id': self.id,
            'academic_year_id': self.academic_year_id,
            'academic_year': self.academic_year.year if self.academic_year else '',
            'event_name': self.event_name,
            'event_type': self.event_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'description': self.description
        }