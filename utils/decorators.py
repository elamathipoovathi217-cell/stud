from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def _role_required(role_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role != role_name:
                flash('Access denied for this role.', 'danger')
                return redirect(url_for('auth.dashboard_redirect'))
            return func(*args, **kwargs)
        return wrapper
    return decorator


principal_required = _role_required('principal')
hod_required = _role_required('hod')
teacher_required = _role_required('teacher')
student_required = _role_required('student')
coordinator_required = _role_required('coordinator')
