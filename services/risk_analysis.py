from models import Attendance, Marks, Risk
from extensions import db


def evaluate_student_risk(student_id):
    attendance_rows = Attendance.query.filter_by(student_id=student_id).all()
    marks_rows = Marks.query.filter_by(student_id=student_id).all()

    attendance_pct = 0.0
    if attendance_rows:
        present = sum(1 for row in attendance_rows if (row.status or '').lower() == 'present')
        attendance_pct = (present / len(attendance_rows)) * 100

    mark_totals = [m.total_marks if m.total_marks is not None else m.calculate_total() for m in marks_rows]
    avg_total = (sum(mark_totals) / len(mark_totals)) if mark_totals else 0.0

    # Rule-based thresholds from requirement
    if attendance_pct < 70:
        level = 'Critical'
        score = 85
    elif avg_total < 10:
        level = 'High Risk'
        score = 80
    elif avg_total < 15:
        level = 'Average'
        score = 55
    else:
        level = 'Low'
        score = 20

    risk = Risk.query.filter_by(student_id=student_id).order_by(Risk.predicted_at.desc()).first()
    if not risk:
        risk = Risk(student_id=student_id)
        db.session.add(risk)

    risk.risk_level = level
    risk.risk_score = score
    risk.attendance_percentage = attendance_pct
    risk.internal_marks_avg = avg_total
    risk.improvement_suggestions = _suggestions(level, attendance_pct, avg_total)
    return risk


def _suggestions(level, attendance_pct, avg_total):
    suggestions = []
    if attendance_pct < 70:
        suggestions.append('Improve attendance to at least 75% in upcoming classes.')
    if avg_total < 15:
        suggestions.append('Revise internal topics weekly and attend remedial sessions.')
    if level in ('High Risk', 'Critical'):
        suggestions.append('Meet mentor/HOD for targeted intervention plan.')
    return ' '.join(suggestions) or 'Maintain consistent preparation and attendance.'
