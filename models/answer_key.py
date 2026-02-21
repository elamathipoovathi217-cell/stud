from extensions import db
from datetime import datetime

class AnswerKey(db.Model):
    __tablename__ = 'answer_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    question_paper_id = db.Column(db.Integer, db.ForeignKey('question_papers.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    
    # Metadata
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    
    # Relationships
    question_paper = db.relationship('QuestionPaper', backref='answer_keys')
    uploader = db.relationship('User', foreign_keys=[uploaded_by], backref='uploaded_answer_keys')
    
    def to_dict(self):
        return {
            'id': self.id,
            'question_paper_id': self.question_paper_id,
            'title': self.title,
            'file_path': self.file_path,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'is_published': self.is_published
        }