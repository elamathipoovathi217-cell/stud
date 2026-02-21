from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from utils.decorators import hod_required
from extensions import db
from models import User, Student, Department, Subject, TeacherSubject, Attendance, Marks, Risk, Semester, Course
from datetime import datetime

hod_bp = Blueprint('hod', __name__)

@hod_bp.route('/dashboard')
@login_required
@hod_required
def dashboard():
    """HOD dashboard"""
    return render_template('hod/dashboard.html')

@hod_bp.route('/assign-teacher', methods=['GET', 'POST'])
@login_required
@hod_required
def assign_teacher():
    """Assign teachers to subjects"""
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        subject_id = request.form.get('subject_id')
        semester_id = request.form.get('semester_id')
        
        assignment = TeacherSubject(
            teacher_id=teacher_id,
            subject_id=subject_id,
            semester_id=semester_id,
            academic_year_id=1,  # Get current academic year
            assigned_date=datetime.utcnow()
        )
        db.session.add(assignment)
        db.session.commit()
        flash('Teacher assigned successfully', 'success')
        return redirect(url_for('hod.assign_teacher'))
    
    teachers = User.query.filter_by(role='teacher', department_id=current_user.department_id).all()
    subjects = Subject.query.filter_by(department_id=current_user.department_id).all()
    semesters = Semester.query.join(Course).filter(Course.department_id == current_user.department_id).all()
    
    return render_template('hod/assign_teacher.html', teachers=teachers, subjects=subjects, semesters=semesters)

@hod_bp.route('/timetable')
@login_required
@hod_required
def timetable():
    """View department timetable"""
    return render_template('hod/timetable.html')

@hod_bp.route('/analytics')
@login_required
@hod_required
def analytics():
    """Department analytics"""
    return render_template('hod/analytics.html')

@hod_bp.route('/subjects')
@login_required
@hod_required
def subjects():
    """View department subjects"""
    subjects = Subject.query.filter_by(department_id=current_user.department_id).all()
    return render_template('hod/subjects.html', subjects=subjects)

@hod_bp.route('/teachers')
@login_required
@hod_required
def teachers():
    """View department teachers"""
    teachers = User.query.filter_by(role='teacher', department_id=current_user.department_id).all()
    return render_template('hod/teachers.html', teachers=teachers)

@hod_bp.route('/students')
@login_required
@hod_required
def students():
    """View department students"""
    students = Student.query.filter_by(department_id=current_user.department_id).all()
    return render_template('hod/students.html', students=students)

@hod_bp.route('/attendance-report')
@login_required
@hod_required
def attendance_report():
    """View attendance report"""
    return render_template('hod/attendance_report.html')

@hod_bp.route('/marks-report')
@login_required
@hod_required
def marks_report():
    """View marks report"""
    return render_template('hod/marks_report.html')

@hod_bp.route('/risk-analysis')
@login_required
@hod_required
def risk_analysis():
    """View risk analysis"""
    return render_template('hod/risk_analysis.html')

@hod_bp.route('/ai-recommendations')
@login_required
@hod_required
def ai_recommendations():
    """View AI recommendations"""
    return render_template('hod/ai_recommendations.html')

@hod_bp.route('/department-settings')
@login_required
@hod_required
def department_settings():
    """Department settings"""
    return render_template('hod/department_settings.html')