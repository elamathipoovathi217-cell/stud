from extensions import db
from datetime import datetime

class Marks(db.Model):
    __tablename__ = 'marks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_type = db.Column(db.String(20), nullable=False)  # internal, external, assignment
    
    # Marks components (total out of 20)
    internal1 = db.Column(db.Float, default=0)  # 5 marks
    internal2 = db.Column(db.Float, default=0)  # 5 marks
    seminar = db.Column(db.Float, default=0)    # 3 marks
    assignment = db.Column(db.Float, default=0)  # 3 marks
    attendance_mark = db.Column(db.Float, default=0)  # 4 marks (based on attendance %)
    
    # Calculated fields
    total_marks = db.Column(db.Float, default=0)
    grade = db.Column(db.String(2))
    
    exam_date = db.Column(db.Date)
    entered_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def calculate_total(self):
        """Calculate total marks out of 20"""
        self.total_marks = (self.internal1 + self.internal2 + self.seminar + 
                           self.assignment + self.attendance_mark)
        return self.total_marks
    
    def calculate_grade(self):
        """Calculate grade based on total marks"""
        total = self.total_marks or self.calculate_total()
        if total >= 17:
            self.grade = 'A'
        elif total >= 14:
            self.grade = 'B'
        elif total >= 10:
            self.grade = 'C'
        elif total >= 7:
            self.grade = 'D'
        else:
            self.grade = 'F'
        return self.grade
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'internal1': self.internal1,
            'internal2': self.internal2,
            'seminar': self.seminar,
            'assignment': self.assignment,
            'attendance_mark': self.attendance_mark,
            'total_marks': self.total_marks,
            'grade': self.grade
        }