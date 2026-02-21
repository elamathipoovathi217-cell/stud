#!/usr/bin/env python
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models import db, User, Department, Course, Student, Subject, Semester, AcademicYear
from models import TeacherSubject, Exam, RoomAllocation, InvigilatorAllocation, Room, ExamSession
from werkzeug.security import generate_password_hash
from datetime import datetime, date, time
import random
from utils.helpers import DEPARTMENTS, generate_registration_number, generate_student_id

app = create_app('development')

def seed_database():
    with app.app_context():
        print("=" * 60)
        print("SEEDING DATABASE - STUDENT PERFORMANCE ANALYSIS SYSTEM")
        print("=" * 60)
        
        # Check if already seeded
        if User.query.count() > 0:
            print("Database already has users. Skipping seed.")
            return
        
        # Step 1: Create Academic Years
        print("\n1. Creating Academic Years...")
        academic_years = [
            AcademicYear(year='2024-2025', start_date=date(2024, 6, 1), end_date=date(2025, 4, 30), is_current=True),
            AcademicYear(year='2023-2024', start_date=date(2023, 6, 1), end_date=date(2024, 4, 30), is_current=False),
        ]
        
        for year in academic_years:
            db.session.add(year)
        db.session.commit()
        print(f"✓ Created {len(academic_years)} academic years")
        
        # Step 2: Create Departments
        print("\n2. Creating Departments...")
        departments_data = {
            'BSC_CS': 'Computer Science',
            'BCA': 'Computer Applications',
            'BCOM_FIN': 'Commerce (Finance)',
            'BCOM_COOP': 'Commerce (Co-operation)',
            'BA_ENGLISH': 'English',
            'BA_ECONOMICS': 'Economics',
            'BA_HISTORY': 'History'
        }
        
        departments = {}
        for code, name in departments_data.items():
            dept = Department(code=code, name=name, description=f"Department of {name}")
            db.session.add(dept)
            db.session.flush()
            departments[code] = dept
            print(f"  ✓ {code} - {name}")
        
        db.session.commit()
        
        # Step 3: Create Courses
        print("\n3. Creating Courses...")
        courses = {}
        for dept_code, dept in departments.items():
            duration = 3 if dept_code in ['BCA', 'BCOM_FIN', 'BCOM_COOP'] else 4
            course = Course(
                name=dept.name,
                code=dept_code,
                duration_years=duration,
                department_id=dept.id
            )
            db.session.add(course)
            db.session.flush()
            courses[dept_code] = course
            print(f"  ✓ {dept_code} Course created")
        
        db.session.commit()
        
        # Step 4: Create Semesters
        print("\n4. Creating Semesters...")
        current_year = AcademicYear.query.filter_by(is_current=True).first()
        semester_count = 0
        
        for dept_code, course in courses.items():
            duration = course.duration_years
            for sem_num in range(1, duration * 2 + 1):
                if sem_num % 2 == 1:  # Odd semesters (Jun-Dec)
                    start_date = date(2024, 6, 1)
                    end_date = date(2024, 12, 31)
                else:  # Even semesters (Jan-Apr)
                    start_date = date(2025, 1, 1)
                    end_date = date(2025, 4, 30)
                
                semester = Semester(
                    semester_number=sem_num,
                    course_id=course.id,
                    academic_year_id=current_year.id,
                    start_date=start_date,
                    end_date=end_date
                )
                db.session.add(semester)
                semester_count += 1
        
        db.session.commit()
        print(f"✓ Created {semester_count} semesters")
        
        # Step 5: Create Subjects
        print("\n5. Creating Subjects...")
        subject_count = 0
        for dept_code, subjects_dict in DEPARTMENTS.items():
            dept = departments.get(dept_code)
            if not dept:
                continue
                
            course = courses.get(dept_code)
            if not course:
                continue
                
            for sem_num_str, subjects in subjects_dict.items():
                sem_num = int(sem_num_str)
                
                semester = Semester.query.filter_by(
                    course_id=course.id,
                    semester_number=sem_num
                ).first()
                
                if not semester:
                    continue
                    
                for idx, subject_name in enumerate(subjects):
                    subject_code = f"{dept_code}{sem_num:02d}{idx+1:02d}"
                    
                    subject = Subject(
                        name=subject_name,
                        code=subject_code,
                        credits=3,
                        semester_id=semester.id,
                        department_id=dept.id
                    )
                    db.session.add(subject)
                    subject_count += 1
        
        db.session.commit()
        print(f"✓ Created {subject_count} subjects")
        
        # Step 6: Create Users
        print("\n6. Creating Users...")
        
        # Principal
        principal = User(
            username='principal',
            email='principal@spas.edu',
            password_hash=generate_password_hash('admin123'),
            full_name='Dr. Principal Kumar',
            role='principal',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(principal)
        print("  ✓ Principal created (principal/admin123)")
        
        # Coordinator
        coordinator = User(
            username='coordinator',
            email='coordinator@spas.edu',
            password_hash=generate_password_hash('coord123'),
            full_name='Exam Coordinator',
            role='coordinator',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(coordinator)
        print("  ✓ Coordinator created (coordinator/coord123)")
        
        # HODs
        hod_count = 0
        for dept_code, dept in departments.items():
            hod_username = f"hod_{dept_code.lower()}"
            hod = User(
                username=hod_username,
                email=f"hod.{dept_code.lower()}@spas.edu",
                password_hash=generate_password_hash('hod123'),
                full_name=f"HOD of {dept.name}",
                role='hod',
                department_id=dept.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(hod)
            hod_count += 1
            dept.hod_id = hod.id
        
        db.session.commit()
        print(f"  ✓ Created {hod_count} HODs")
        
        # Teachers
        teacher_names = [
            ('Dr. A. Sharma', 'asharma'), ('Prof. B. Patel', 'bpatel'),
            ('Dr. C. Reddy', 'credddy'), ('Prof. D. Kumar', 'dkumar'),
        ]
        
        teacher_count = 0
        for dept_code, dept in departments.items():
            for i in range(5):  # 5 teachers per department
                name, base_username = teacher_names[i % len(teacher_names)]
                username = f"{base_username}_{dept_code.lower()}"
                
                teacher = User(
                    username=username,
                    email=f"{base_username}.{dept_code.lower()}@spas.edu",
                    password_hash=generate_password_hash('teacher123'),
                    full_name=f"{name} - {dept.name}",
                    role='teacher',
                    department_id=dept.id,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(teacher)
                teacher_count += 1
        
        db.session.commit()
        print(f"  ✓ Created {teacher_count} teachers")
        
        # Students
        batches = [2022, 2023, 2024, 2025]
        student_count = 0
        
        for dept_code, dept in departments.items():
            course = courses.get(dept_code)
            if not course:
                continue
            
            for batch in batches:
                if batch == 2022:
                    current_sem = 7
                elif batch == 2023:
                    current_sem = 5
                elif batch == 2024:
                    current_sem = 3
                else:
                    current_sem = 1
                
                for i in range(1, 31):  # 30 students per batch
                    reg_number = f"{str(batch)[2:]}{dept_code}{i:04d}"
                    student_id = f"{dept_code}{i:03d}"
                    username = f"student_{dept_code.lower()}_{batch}_{i}"
                    
                    student_user = User(
                        username=username,
                        email=f"{username}@spas.edu",
                        password_hash=generate_password_hash('student123'),
                        full_name=f"Student {i} - {dept.name}",
                        role='student',
                        department_id=dept.id,
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(student_user)
                    db.session.flush()
                    
                    student = Student(
                        registration_number=reg_number,
                        student_id=student_id,
                        name=f"Student {i} - {dept.name}",
                        email=f"{username}@spas.edu",
                        user_id=student_user.id,
                        course_id=course.id,
                        department_id=dept.id,
                        current_semester=current_sem,
                        batch_year=batch,
                        admission_date=date(batch, 6, 1),
                        is_active=True
                    )
                    db.session.add(student)
                    student_count += 1
        
        db.session.commit()
        print(f"  ✓ Created {student_count} students")
        
        # Step 7: Create Exam Sessions
        print("\n7. Creating Exam Sessions...")
        sessions = [
            ExamSession(name='Morning', start_time=time(10, 0), end_time=time(13, 0)),
            ExamSession(name='Afternoon', start_time=time(14, 0), end_time=time(17, 0)),
        ]
        
        for session in sessions:
            db.session.add(session)
        
        db.session.commit()
        print("  ✓ Created exam sessions")
        
        # Step 8: Create Rooms
        print("\n8. Creating Rooms...")
        blocks = ['A', 'B', 'C']
        room_count = 0
        
        for block in blocks:
            for i in range(1, 11):
                room_number = f"{block}{100 + i}"
                capacity = 60 if block == 'A' else 45 if block == 'B' else 30
                
                room = Room(
                    room_number=room_number,
                    block=block,
                    capacity=capacity,
                    has_projector=random.choice([True, False]),
                    has_ac=block in ['A', 'B'],
                    is_lab=block == 'C' and i <= 3,
                    is_active=True
                )
                db.session.add(room)
                room_count += 1
        
        db.session.commit()
        print(f"  Created {room_count} rooms")
        
        # Summary
        print("\n" + "=" * 60)
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nDATABASE SUMMARY:")
        print(f"  Departments    : {Department.query.count()}")
        print(f"  Courses        : {Course.query.count()}")
        print(f"  Semesters      : {Semester.query.count()}")
        print(f"  Subjects       : {Subject.query.count()}")
        print(f"  Users          : {User.query.count()}")
        print(f"  Students       : {Student.query.count()}")
        print(f"  Rooms          : {Room.query.count()}")
        
        print("\n" + "=" * 60)
        print("LOGIN CREDENTIALS:")
        print("=" * 60)
        print("Principal   : principal / admin123")
        print("Coordinator : coordinator / coord123")
        print("\nHODs:")
        for dept_code in departments.keys():
            print(f"  {dept_code} : hod_{dept_code.lower()} / hod123")
        print("\nTeachers    : [name]_[dept] / teacher123")
        print("Students    : student_[dept]_[batch]_[no] / student123")
        print("=" * 60)

if __name__ == '__main__':
    seed_database()