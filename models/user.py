from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # principal, hod, teacher, student, coordinator
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    profile_pic = db.Column(db.String(200))
    
    # Relationships - add overlaps parameter
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    department = db.relationship('Department', backref='users_list', foreign_keys=[department_id], 
                                overlaps="teacher_department")
    
    # For teachers - subjects they teach
    teacher_subjects = db.relationship('TeacherSubject', backref='teacher_info', 
                                      lazy=True, cascade='all, delete-orphan')
    
    # For students
    student_record = db.relationship('Student', backref='user_account', uselist=False, lazy=True)
    
    def has_role(self, role):
        return self.role == role
    
    def get_id(self):
        return str(self.id)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'phone': self.phone,
            'department_id': self.department_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }