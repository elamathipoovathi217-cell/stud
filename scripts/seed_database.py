# scripts/seed_coordinator_data.py
from app import create_app
from models import db, Exam, RoomAllocation, InvigilatorAllocation, User, Subject, Department
from models import Room, ExamSession
from datetime import datetime, date, time
import random

app = create_app('development')

def seed_coordinator_data():
    with app.app_context():
        print("Seeding coordinator data...")
        
        # Create exam sessions
        sessions = [
            ExamSession(name='Morning', start_time=time(10, 0), end_time=time(13, 0)),
            ExamSession(name='Afternoon', start_time=time(14, 0), end_time=time(17, 0)),
        ]
        
        for session in sessions:
            if not ExamSession.query.filter_by(name=session.name).first():
                db.session.add(session)
        
        # Create rooms
        blocks = ['A', 'B', 'C']
        rooms_data = []
        
        for block in blocks:
            for i in range(1, 11):  # 10 rooms per block
                room_number = f"{block}{100 + i}"
                capacity = 60 if block == 'A' else 45 if block == 'B' else 30
                
                room = Room(
                    room_number=room_number,
                    block=block,
                    capacity=capacity,
                    has_projector=random.choice([True, False]),
                    has_ac=block in ['A', 'B'],
                    is_lab=block == 'C' and i <= 3
                )
                
                if not Room.query.filter_by(room_number=room_number).first():
                    db.session.add(room)
        
        db.session.commit()
        
        # Create sample exams
        departments = Department.query.all()
        subjects = Subject.query.all()
        
        exam_dates = [
            date(2025, 3, 1),
            date(2025, 3, 3),
            date(2025, 3, 5),
            date(2025, 3, 8),
            date(2025, 3, 10),
        ]
        
        for dept in departments[:3]:  # First 3 departments
            dept_subjects = [s for s in subjects if s.department_id == dept.id][:4]
            
            for i, subject in enumerate(dept_subjects):
                exam_date = exam_dates[i % len(exam_dates)]
                session = random.choice(['Morning', 'Afternoon'])
                
                session_obj = ExamSession.query.filter_by(name=session).first()
                
                exam = Exam(
                    name=f"{subject.name} Internal Exam",
                    exam_type='Internal',
                    semester_id=subject.semester_id,
                    subject_id=subject.id,
                    session_id=session_obj.id if session_obj else None,
                    exam_date=exam_date,
                    start_time=session_obj.start_time if session_obj else time(10, 0),
                    end_time=session_obj.end_time if session_obj else time(13, 0),
                    duration_minutes=180,
                    max_marks=100,
                    created_by=1,  # Admin user
                    is_published=random.choice([True, False])
                )
                
                db.session.add(exam)
        
        db.session.commit()
        print("Coordinator data seeded successfully!")

if __name__ == '__main__':
    seed_coordinator_data()