from extensions import db
from datetime import datetime

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    credits = db.Column(db.Integer, default=3)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - Use unique backref names and add overlaps
    teacher_assignments = db.relationship('TeacherSubject', backref='subject_info', 
                                         lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='subject_info', lazy=True)
    marks_records = db.relationship('Marks', backref='subject_info', lazy=True)
    exam_schedules = db.relationship('Exam', backref='subject_schedules', lazy=True, 
                                    overlaps="exam_list,subject_info")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'credits': self.credits,
            'semester_id': self.semester_id,
            'department_id': self.department_id
        }