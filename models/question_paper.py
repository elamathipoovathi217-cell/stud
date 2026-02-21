from extensions import db
from datetime import datetime

class QuestionPaper(db.Model):
    __tablename__ = 'question_papers'
    
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    
    # Metadata
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'))
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'))
    
    # Access control
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    
    # Relationships
    subject = db.relationship('Subject', backref='question_papers')
    exam = db.relationship('Exam', backref='question_papers')
    uploader = db.relationship('User', foreign_keys=[uploaded_by], backref='uploaded_question_papers')
    academic_year = db.relationship('AcademicYear', backref='question_papers')
    semester = db.relationship('Semester', backref='question_papers')
    
    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else '',
            'exam_id': self.exam_id,
            'exam_name': self.exam.name if self.exam else '',
            'title': self.title,
            'file_path': self.file_path,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'is_published': self.is_published
        }