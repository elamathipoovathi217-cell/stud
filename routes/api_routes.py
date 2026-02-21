from flask import Blueprint, jsonify, request
from models import User, Student, Department, Subject, Attendance, Marks, Notification, Exam
from extensions import db
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func

api_bp = Blueprint('api', __name__)

@api_bp.route('/public/stats')
def public_stats():
    """Get public statistics"""
    total_students = Student.query.count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_departments = Department.query.count()
    total_subjects = Subject.query.count()
    
    return jsonify({
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_departments': total_departments,
        'total_subjects': total_subjects
    })

@api_bp.route('/public/announcements')
def public_announcements():
    """Get public announcements"""
    notifications = Notification.query.filter_by(
        is_published=True
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    return jsonify([{
        'title': n.title,
        'message': n.message,
        'date': n.created_at.strftime('%Y-%m-%d')
    } for n in notifications])

@api_bp.route('/user/activity')
@login_required
def user_activity():
    """Get user activity log"""
    # This would come from an ActivityLog model
    activities = []
    
    # Sample activities
    if current_user.role == 'student':
        # Get recent marks and attendance
        recent_marks = Marks.query.filter_by(student_id=current_user.student_record.id)\
            .order_by(Marks.created_at.desc()).limit(3).all()
        
        for mark in recent_marks:
            activities.append({
                'icon': 'chart-line',
                'description': f'Marks updated for {mark.subject.name}',
                'time': mark.created_at.strftime('%d %b, %H:%M')
            })
    
    return jsonify(activities)

@api_bp.route('/departments/<int:dept_id>/courses')
def get_department_courses(dept_id):
    """Get courses for a department"""
    from models import Course
    courses = Course.query.filter_by(department_id=dept_id).all()
    return jsonify([{'id': c.id, 'name': c.name, 'code': c.code} for c in courses])

@api_bp.route('/subjects/semester/<int:semester_id>')
def get_semester_subjects(semester_id):
    """Get subjects for a semester"""
    subjects = Subject.query.filter_by(semester_id=semester_id).all()
    return jsonify([{'id': s.id, 'name': s.name, 'code': s.code} for s in subjects])

@api_bp.route('/check-username/<username>')
def check_username(username):
    """Check if username exists"""
    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({'exists': exists})

@api_bp.route('/check-email/<email>')
def check_email(email):
    """Check if email exists"""
    exists = User.query.filter_by(email=email).first() is not None
    return jsonify({'exists': exists})