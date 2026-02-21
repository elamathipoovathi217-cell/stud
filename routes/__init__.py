# routes/__init__.py
from routes.auth_routes import auth_bp
from routes.principal_routes import principal_bp
from routes.hod_routes import hod_bp
from routes.teacher_routes import teacher_bp
from routes.student_routes import student_bp
from routes.coordinator_routes import coordinator_bp
from routes.public_routes import public_bp
from routes.api_routes import api_bp

__all__ = [
    'auth_bp', 'principal_bp', 'hod_bp', 'teacher_bp', 
    'student_bp', 'coordinator_bp', 'public_bp', 'api_bp'
]