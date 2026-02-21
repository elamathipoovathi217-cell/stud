from extensions import db
from datetime import datetime

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # BSC_CS, BCA, etc.
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    hod_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - add overlaps parameter to fix warnings
    hod = db.relationship('User', foreign_keys=[hod_id], lazy=True, overlaps="department,users")
    courses = db.relationship('Course', backref='department_info', lazy=True, cascade='all, delete-orphan')
    subjects = db.relationship('Subject', backref='department_info', lazy=True, cascade='all, delete-orphan')
    teachers = db.relationship('User', backref='teacher_department', lazy=True, 
                              foreign_keys='User.department_id', overlaps="department,users")
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'hod_id': self.hod_id
        }