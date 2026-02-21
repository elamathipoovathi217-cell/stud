from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from utils.decorators import teacher_required
from extensions import db
from models import User, Student, Subject, TeacherSubject, Attendance, Marks, Risk, Exam, RoomAllocation
from datetime import datetime, date
from sqlalchemy import and_
from services.risk_analysis import evaluate_student_risk

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    """Teacher dashboard"""
    teacher_subjects = TeacherSubject.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    subject_ids = [ts.subject_id for ts in teacher_subjects]
    marks_rows = Marks.query.filter(Marks.subject_id.in_(subject_ids)).all() if subject_ids else []
    avg_score = (sum((m.total_marks or 0) for m in marks_rows) / len(marks_rows)) if marks_rows else 0
    return render_template('teacher/dashboard.html', teacher_subjects=teacher_subjects, avg_score=avg_score)

@teacher_bp.route('/mark-attendance', methods=['GET', 'POST'])
@login_required
@teacher_required
def mark_attendance():
    """Mark attendance for students"""
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        attendance_date = request.form.get('date')
        students = request.form.getlist('students[]')
        status = request.form.getlist('status[]')
        
        for i, student_id in enumerate(students):
            attendance = Attendance(
                student_id=student_id,
                subject_id=subject_id,
                date=datetime.strptime(attendance_date, '%Y-%m-%d').date(),
                status=status[i],
                marked_by=current_user.id
            )
            db.session.add(attendance)
        
        db.session.commit()
        flash('Attendance marked successfully', 'success')
        return redirect(url_for('teacher.mark_attendance'))
    
    # Get subjects taught by current teacher
    teacher_subjects = TeacherSubject.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    return render_template('teacher/mark_attendance.html', teacher_subjects=teacher_subjects)

@teacher_bp.route('/add-marks', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_marks():
    """Add marks for students"""
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        exam_type = request.form.get('exam_type')
        student_ids = request.form.getlist('student_ids[]')
        internal1 = request.form.getlist('internal1[]')
        internal2 = request.form.getlist('internal2[]')
        seminar = request.form.getlist('seminar[]')
        assignment = request.form.getlist('assignment[]')
        attendance_mark = request.form.getlist('attendance_mark[]')
        
        for i, student_id in enumerate(student_ids):
            marks = Marks.query.filter_by(
                student_id=student_id,
                subject_id=subject_id,
                exam_type=exam_type
            ).first()
            
            if not marks:
                marks = Marks(
                    student_id=student_id,
                    subject_id=subject_id,
                    exam_type=exam_type,
                    entered_by=current_user.id
                )
            
            marks.internal1 = float(internal1[i]) if internal1[i] else 0
            marks.internal2 = float(internal2[i]) if internal2[i] else 0
            marks.seminar = float(seminar[i]) if seminar[i] else 0
            marks.assignment = float(assignment[i]) if assignment[i] else 0
            marks.attendance_mark = float(attendance_mark[i]) if attendance_mark[i] else 0
            marks.calculate_total()
            marks.calculate_grade()
            
            if not marks.id:
                db.session.add(marks)
            evaluate_student_risk(student_id)

        db.session.commit()
        flash('Marks added successfully', 'success')
        return redirect(url_for('teacher.add_marks'))
    
    teacher_subjects = TeacherSubject.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    return render_template('teacher/add_marks.html', teacher_subjects=teacher_subjects)

@teacher_bp.route('/subject-students/<int:subject_id>')
@login_required
@teacher_required
def subject_students(subject_id):
    """View students in a subject"""
    subject = Subject.query.get_or_404(subject_id)
    students = Student.query.filter_by(
        department_id=subject.department_id,
        current_semester=subject.semester_id
    ).all()
    return render_template('teacher/subject_students.html', subject=subject, students=students)

@teacher_bp.route('/performance-chart')
@login_required
@teacher_required
def performance_chart():
    """View performance charts"""
    return render_template('teacher/performance_chart.html')

@teacher_bp.route('/excel-report')
@login_required
@teacher_required
def excel_report():
    """Generate Excel report"""
    return render_template('teacher/excel_report.html')

@teacher_bp.route('/ai-risk-alerts')
@login_required
@teacher_required
def ai_risk_alerts():
    """View AI risk alerts"""
    return render_template('teacher/ai_risk_alerts.html')

@teacher_bp.route('/student-analysis/<int:student_id>')
@login_required
@teacher_required
def student_analysis(student_id):
    """Analyze individual student"""
    student = Student.query.get_or_404(student_id)
    marks = Marks.query.filter_by(student_id=student_id).all()
    risk = Risk.query.filter_by(student_id=student_id).order_by(Risk.predicted_at.desc()).first()
    return render_template('teacher/student_analysis.html', student=student, marks=marks, risk=risk)

@teacher_bp.route('/class-performance')
@login_required
@teacher_required
def class_performance():
    """View class performance"""
    return render_template('teacher/class_performance.html')

@teacher_bp.route('/subject-analysis/<int:subject_id>')
@login_required
@teacher_required
def subject_analysis(subject_id):
    """Analyze subject performance"""
    subject = Subject.query.get_or_404(subject_id)
    marks = Marks.query.filter_by(subject_id=subject_id).all()
    avg = (sum((m.total_marks or 0) for m in marks) / len(marks)) if marks else 0
    return render_template('teacher/subject_analysis.html', subject=subject, marks=marks, avg=avg)

@teacher_bp.route('/improvement-suggestions')
@login_required
@teacher_required
def improvement_suggestions():
    """View improvement suggestions"""
    return render_template('teacher/improvement_suggestions.html')

@teacher_bp.route('/notifications')
@login_required
@teacher_required
def notifications():
    """View notifications"""
    return render_template('teacher/notifications.html')

@teacher_bp.route('/profile')
@login_required
@teacher_required
def profile():
    """Teacher profile"""
    return render_template('teacher/profile.html')