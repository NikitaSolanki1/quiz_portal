# StudentPortal - college exam and viva booking system
from datetime import datetime, date, timedelta
from celery.schedules import crontab
from flask_mail import Mail, Message
import csv
import jwt
import os
from datetime import datetime
from celery import Celery
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///student_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'student-portal-secret-key'
db = SQLAlchemy(app)
from flask_caching import Cache
CORS(app)
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/1'
cache = Cache(app)



def setup_background_tasks(app):
    celery_app = Celery(
        app.import_name,
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )
    celery_app.conf.update(app.config)
    celery_app.conf.timezone = "Asia/Kolkata"
    celery_app.conf.enable_utc = False
    celery_app.conf.beat_schedule = {
        "daily-portal-reminder": {
            "task": "app.send_viva_reminders",
            "schedule": timedelta(seconds=10),
        },
        "monthly-portal-report": {
    "task": "app.send_admin_month_mail",
    "schedule": timedelta(seconds=10),
},
    }
    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery_app.Task = ContextTask
    return celery_app
celery = setup_background_tasks(app)

app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@studentportal.local")
mail = Mail(app)



class CampusUser(db.Model):
    __tablename__ = 'campus_users'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),nullable=False)
    email = db.Column(db.String(100),nullable=False)
    password = db.Column(db.String(100),nullable=False)
    role = db.Column(db.String(100),nullable=False)  # admin / examinor / user
    is_blocked = db.Column(db.Boolean,default=False)



class StudentDetail(db.Model):
    __tablename__ = 'student_details'
    id = db.Column(db.Integer,primary_key=True)
    address = db.Column(db.String(100),nullable=False)
    phone = db.Column(db.String(100),nullable=False)
    past_experience = db.Column(db.String(100),nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('campus_users.id'),nullable=False,unique=True)


class ExaminerDetail(db.Model):
    __tablename__ = 'examiner_details'
    id = db.Column(db.Integer,primary_key=True)
    address = db.Column(db.String(100),nullable=False)
    phone = db.Column(db.String(100),nullable=False)
    past_experience = db.Column(db.String(100),nullable=False)
    department = db.Column(db.String(100), nullable=False, default='')
    user_id = db.Column(db.Integer,db.ForeignKey('campus_users.id'),nullable=False,unique=True)



class SubjectCourse(db.Model):
    __tablename__ = 'subject_courses'
    id = db.Column(db.Integer,primary_key=True)
    course_code = db.Column(db.String(50), nullable=False, default='')
    coures_name = db.Column(db.String(100),nullable=False)
    coures_description = db.Column(db.String(100),nullable=False)
    course_duration = db.Column(db.Integer,nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Active')




class VivaExam(db.Model):
    __tablename__ = 'viva_exams'
    id = db.Column(db.Integer, primary_key=True)
    exam_name = db.Column(db.String(100), nullable=False)
    exam_description = db.Column(db.String(100), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False, default='Viva')
    duration = db.Column(db.Integer, nullable=False, default=30)
    max_marks = db.Column(db.Integer, nullable=False, default=100)
    examinor_slot_create_start_date = db.Column(db.String(100), nullable=False)
    examinor_slot_create_end_date = db.Column(db.String(100), nullable=False)
    booking_start_time = db.Column(db.String(100), nullable=False)
    booking_end_time = db.Column(db.String(100), nullable=False)
    exam_start_date = db.Column(db.String(100), nullable=False)
    exam_end_date = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('subject_courses.id', ondelete='CASCADE'), nullable=False)
    examinor_id = db.Column(db.Integer, db.ForeignKey('campus_users.id'), nullable=False)
    slot_open = db.Column(db.Boolean, default=False)
    booking_open = db.Column(db.Boolean, default=False)
    results_published = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(30), nullable=False, default='Draft')

class VivaQuestion(db.Model):
    __tablename__ = 'viva_questions'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False, default='')
    marks = db.Column(db.Integer, nullable=False)
    weightage = db.Column(db.Integer, nullable=False, default=0)
    exam_id = db.Column(db.Integer, db.ForeignKey('viva_exams.id', ondelete='CASCADE'), nullable=False)


class BookingSlot(db.Model):
    __tablename__ = 'booking_slots'
    id = db.Column(db.Integer, primary_key=True)
    slot_date = db.Column(db.String(100), nullable=False)
    slot_time = db.Column(db.String(100), nullable=False)
    end_time = db.Column(db.String(20), nullable=False, default='')
    capacity = db.Column(db.Integer, nullable=False)
    meeting_link = db.Column(db.String(200), nullable=False, default='')
    status = db.Column(db.String(20), nullable=False, default='Available')
    exam_id = db.Column(db.Integer, db.ForeignKey('viva_exams.id', ondelete='CASCADE'), nullable=False)
    examinor_id = db.Column(db.Integer, db.ForeignKey('campus_users.id'), nullable=False)


class StudentBooking(db.Model):
    __tablename__ = 'student_bookings'
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('booking_slots.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('campus_users.id'), nullable=False)
    booking_date = db.Column(db.String(30), nullable=False, default='')
    status = db.Column(db.String(20), nullable=False, default='Booked')
    assigned_examinor_id = db.Column(db.Integer, db.ForeignKey('campus_users.id'))


class ScoreRecord(db.Model):
    __tablename__ = 'score_records'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('student_bookings.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('viva_questions.id', ondelete='CASCADE'), nullable=False)
    marks = db.Column(db.Integer, nullable=False)


class VivaResult(db.Model):
    __tablename__ = 'viva_results'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('student_bookings.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('campus_users.id'), nullable=False)
    examinor_id = db.Column(db.Integer, db.ForeignKey('campus_users.id'), nullable=False)
    total_marks = db.Column(db.Integer, nullable=False, default=0)
    remarks = db.Column(db.String(500), nullable=False, default='')
    evaluation_date = db.Column(db.String(30), nullable=False, default='')
    status = db.Column(db.String(30), nullable=False, default='Submitted')

class DataExport(db.Model):
    __tablename__ = 'data_exports'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('campus_users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    file_name = db.Column(db.String(200), nullable=False, default='')
    message = db.Column(db.String(300), nullable=False, default='')
    created_at = db.Column(db.String(30), nullable=False, default='')

class PortalNotice(db.Model):
    __tablename__ = 'portal_notices'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('campus_users.id'), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.String(30), nullable=False, default='')

@celery.task(name="app.send_viva_reminders")
def send_viva_reminders():
    sent = 0

    bookings = StudentBooking.query.filter_by(status="Booked").all()
    for booking in bookings:
        slot = BookingSlot.query.filter_by(id=booking.slot_id).first()
        if not slot:
            continue

        student = CampusUser.query.filter_by(id=booking.user_id).first()
        exam = VivaExam.query.filter_by(id=slot.exam_id).first()
        if not student or not student.email or not exam:
            continue

        examiner_id = booking.assigned_examinor_id or slot.examinor_id or exam.examinor_id
        examiner = CampusUser.query.filter_by(id=examiner_id).first() if examiner_id else None

        msg = Message(
            subject=f"Reminder: {exam.exam_name}",
            recipients=[student.email],
            body=(
                f"Hi {student.name},\n\n"
                f"VivaExam: {exam.exam_name}\n"
                f"Date: {slot.slot_date}\n"
                f"Time: {slot.slot_time}\n"
                f"Examiner: {examiner.name if examiner else 'Not assigned'}\n"
                f"Instructions: {exam.exam_description}\n"
            ),
        )
        mail.send(msg)
        sent += 1

    return f"Sent {sent} examination reminder(s)"

EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
CSV_FIELDS = [
    'Student ID',
    'VivaExam Name',
    'Course',
    'VivaExam Date',
    'Examiner',
    'Marks Obtained',
    'Booking Status'
]


def collect_booking_history(user_id):
    rows = []
    for booking in StudentBooking.query.filter_by(user_id=user_id).all():
        slot = BookingSlot.query.filter_by(id=booking.slot_id).first()
        exam = VivaExam.query.filter_by(id=slot.exam_id).first() if slot else None
        course = SubjectCourse.query.filter_by(id=exam.course_id).first() if exam else None
        examiner_id = booking.assigned_examinor_id
        if not examiner_id and slot:
            examiner_id = slot.examinor_id
        if not examiner_id and exam:
            examiner_id = exam.examinor_id
        examiner = CampusUser.query.filter_by(id=examiner_id).first() if examiner_id else None
        evaluation = VivaResult.query.filter_by(booking_id=booking.id).first()
        rows.append({
            'Student ID': user_id,
            'VivaExam Name': exam.exam_name if exam else '',
            'Course': course.coures_name if course else '',
            'VivaExam Date': slot.slot_date if slot else '',
            'Examiner': examiner.name if examiner else '',
            'Marks Obtained': evaluation.total_marks if evaluation else '',
            'Booking Status': booking.status
        })
    return rows

@celery.task(name='app.write_student_csv')
def write_student_csv(job_id, user_id):
    job = DataExport.query.filter_by(id=job_id).first()
    try:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        file_name = 'examination_history_' + str(user_id) + '_' + str(job_id) + '.csv'
        path = os.path.join(EXPORT_DIR, file_name)
        with open(path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(collect_booking_history(user_id))
        job.status = 'completed'
        job.file_name = file_name
        job.message = 'VivaExam history CSV is ready'
        alert = PortalNotice(
            user_id=user_id,
            message='Your examination history export is ready. Download the CSV from the dashboard.',
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(alert)
        db.session.commit()
    except Exception:
        db.session.rollback()
        job = DataExport.query.filter_by(id=job_id).first()
        if job:
            job.status = 'failed'
            job.message = 'Export failed'
        db.session.add(PortalNotice(
            user_id=user_id,
            message='VivaExam history export failed.',
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        db.session.commit()


@app.route('/start_history_download', methods=['POST'])
def start_history_download():
    data = request.json
    user = CampusUser.query.filter_by(id=data['user_id']).first()
    if not user or user.role != 'user':
        return jsonify({'message': 'Only a student can export examination history'})
    job = DataExport(
        user_id=user.id,
        status='pending',
        message='Export started',
        created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    db.session.add(job)
    db.session.commit()
    write_student_csv.delay(job.id, user.id)
    return jsonify({
        'message': 'Export started. You will get an alert when the CSV is ready.',
        'job_id': job.id
    })



@app.route('/history_download_status', methods=['POST'])
def history_download_status():
    data = request.json
    job = DataExport.query.filter_by(id=data['job_id'], user_id=data['user_id']).first()
    if not job:
        return jsonify({'message': 'Export not found'})
    return jsonify({
        'status': job.status,
        'message': job.message,
        'file_name': job.file_name,
        'job_id': job.id
    })

@app.route('/list_portal_notices', methods=['POST'])
def list_portal_notices():
    data = request.json
    alerts = []
    for alert in PortalNotice.query.filter_by(user_id=data['user_id']).order_by(PortalNotice.id.desc()).all():
        alerts.append({
            'id': alert.id,
            'message': alert.message,
            'created_at': alert.created_at,
            'is_read': alert.is_read
        })
    return jsonify({'data': alerts})
@celery.task(name="app.send_admin_month_mail")
def send_admin_month_mail():
    exams = VivaExam.query.filter(VivaExam.status.in_(["Closed", "Completed"])).all()
    bookings = StudentBooking.query.all()
    evaluations = VivaResult.query.all()

    evaluated_students = {item.student_id for item in evaluations}
    evaluated_booking_ids = {item.booking_id for item in evaluations}
    completed_bookings = [item for item in bookings if item.id in evaluated_booking_ids]
    pending = [
        item for item in bookings
        if item.status == "Booked" and item.id not in evaluated_booking_ids
    ]

    examiner_counts = {}
    for item in evaluations:
        examiner_counts[item.examinor_id] = examiner_counts.get(item.examinor_id, 0) + 1
    active = sorted(examiner_counts.items(), key=lambda pair: pair[1], reverse=True)[:5]

    if active:
        rows = ""
        for examiner_id, count in active:
            examiner = CampusUser.query.filter_by(id=examiner_id).first()
            name = examiner.name if examiner else "Unknown"
            rows += f"<li>{name} — {count} evaluation(s)</li>"
    else:
        rows = "<li>No evaluations yet</li>"

    html_body = f"""
    <h2>Monthly examination report</h2>
    <ul>
        <li><strong>Examinations conducted:</strong> {len(exams)}</li>
        <li><strong>Students evaluated:</strong> {len(evaluated_students)}</li>
        <li><strong>Completed bookings:</strong> {len(completed_bookings)}</li>
        <li><strong>Pending evaluations:</strong> {len(pending)}</li>
    </ul>
    <h3>Most active examiners</h3>
    <ul>{rows}</ul>
    """

    admins = CampusUser.query.filter_by(role="admin").all()
    sent = 0
    for admin in admins:
        if not admin.email:
            continue
        msg = Message(
            subject="Monthly examination report",
            recipients=[admin.email],
            html=html_body,
        )
        mail.send(msg)
        sent += 1

    return f"Monthly report sent to {sent} admin(s)"
@app.route('/register_new_student',methods=['POST'])
def register_new_student():
    data = request.json
    old_user = CampusUser.query.filter_by(email=data['email']).first()
    if old_user:
        return jsonify({'message': 'User already exists'})
    new_user = CampusUser(name=data['username'], email=data['email'], password=data['password'], role='user')
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registered successfully'})



@app.route('/portal_login',methods=['POST'])
def portal_login():
    data = request.json
    user = CampusUser.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'message': 'User not found'})
    if user.password != data['password']:
        return jsonify({'message': 'Invalid password'})
    if user.is_blocked:
        return jsonify({'message': 'User is blocked'})

    token = jwt.encode(
        {
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
          
        },
        app.config['SECRET_KEY'],
       
    )
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'role': user.role,
        'name': user.name,
        'user_id': user.id
    })


@app.route('/create_subject_course',methods=['POST'])
def create_subject_course():
    data = request.json
    print(data)
    new_course = SubjectCourse(course_code=data['courseCode'], coures_name=data['courseName'], coures_description=data['courseDescription'], course_duration=data['courseDuration'], status=data['status'])
    db.session.add(new_course)
    db.session.commit()
    return jsonify({'message': 'Course created successfully'})

@app.route('/fetch_examiner_list',methods=['POST','GET'])
def fetch_examiner_list():
    all_examinors_list = []

    all_examinors = CampusUser.query.filter_by(role='examinor').all()             # i hve to fixed it latae i have to use.filter_by(role='examinor')
    for examinor in all_examinors:
            profile = ExaminerDetail.query.filter_by(user_id=examinor.id).first()
            all_examinors_list.append(
                {
                    'id': examinor.id,
                    'name': examinor.name,
                    'email': examinor.email,
                    'role': examinor.role,
                    'is_blocked': examinor.is_blocked,
                    'phone': profile.phone if profile else '',
                    'department': profile.department if profile else ''
                }
            )
    return jsonify({'data': all_examinors_list})




@app.route('/fetch_one_course_list',methods=['POST'])
def fetch_course_list():
    all_courses_list = []
    all_courses = SubjectCourse.query.all()
    for course in all_courses:
        all_courses_list.append(
            {
                'id': course.id,
                'course_code': course.course_code,
                'name': course.coures_name,
                'description': course.coures_description,
                'duration': course.course_duration,
                'status': course.status
            }
        )
    return jsonify({'data': all_courses_list})

@app.route('/fetch_one_course/<int:id>',methods=['POST'])
def fetch_one_course(id):
   
    course = SubjectCourse.query.filter_by(id=id).first()
   
    return jsonify({'data': {
        'course_code': course.course_code,
        'name': course.coures_name,
        'description': course.coures_description,
        'duration': course.course_duration,
        'status': course.status
    }}) 



@app.route('/update_subject_course/<int:id>',methods=['POST'])
def update_subject_course(id):
    data = request.json
    course = SubjectCourse.query.filter_by(id=id).first()
    course.course_code = data['course_code']
    course.coures_name = data['name']
    course.coures_description = data['description']
    course.course_duration = data['duration']
    course.status = data['status']
    db.session.commit()
    return jsonify({'message': 'Course updated successfully'})


from datetime import date, time

def is_viva_finished(exam):
    if not exam:
        return False
    if exam.status == 'Completed':
        return True
    if not exam.exam_end_date:
        return False
    try:
        exam_end = date.fromisoformat(str(exam.exam_end_date)[:10])
    except ValueError:
        return False
    return date.today() > exam_end

def are_viva_dates_locked(exam):
    if not exam:
        return False
    if exam.status in ('Closed', 'Completed'):
        return True
    slot_ids = [slot.id for slot in BookingSlot.query.filter_by(exam_id=exam.id).all()]
    if not slot_ids:
        return False
    return StudentBooking.query.filter(
        StudentBooking.slot_id.in_(slot_ids),
        StudentBooking.status != 'Cancelled'
    ).count() > 0

@app.route('/create_viva_exam', methods=['POST'])
def create_viva_exam():
    data = request.json
    print(data)

    exam_name = data['exam_name'].strip()
    old_exam = VivaExam.query.filter(db.func.lower(VivaExam.exam_name) == exam_name.lower()).first()
    if old_exam:
        return jsonify({'message': 'Exam already exists'})

    new_exam = VivaExam(
        exam_name=exam_name,
        exam_description=data['exam_description'],
        exam_type=data['exam_type'],
        duration=data['duration'],
        max_marks=data['max_marks'],
        examinor_slot_create_start_date=data['examinor_slot_create_start_date'],
        examinor_slot_create_end_date=data['examinor_slot_create_end_date'],
        booking_start_time=data['booking_start_time'],
        booking_end_time=data['booking_end_time'],
        exam_start_date=data['exam_start_date'],
        exam_end_date=data['exam_end_date'],
        course_id=data['course_id'],
        examinor_id=data['examinor_id']
    )

    db.session.add(new_exam)
    db.session.commit()

    return jsonify({'message': 'Exam created successfully'})



@app.route('/create_examiner_detail', methods=['POST'])
def create_examiner_detail():
    data = request.json
    old_profile = ExaminerDetail.query.filter_by(user_id=data['user_id']).first()
    if old_profile:
        return jsonify({'message': 'Profile already exists'})
    new_profile = ExaminerDetail(
        address=data['address'],
        phone=data['phone'],
        past_experience=data['past_experience'],
        department=data['department'],
        user_id=data['user_id']
    )
    db.session.add(new_profile)
    db.session.commit()
    return jsonify({'message': 'Profile created successfully'})

@app.route('/register_new_examiner',methods=['POST'])
def register_new_examiner():
    data = request.json
    print(data)
    old_user = CampusUser.query.filter_by(email=data['email']).first()
    if old_user:
        return jsonify({'message': 'Examinor already exists'})
    new_examinor = CampusUser(name=data['username'], email=data['email'], password=data['password'], role='examinor')
    db.session.add(new_examinor)
    db.session.commit()
    new_profile = ExaminerDetail(address=data['address'], phone=data['phone'], past_experience=data['past_experience'], department=data['department'], user_id=new_examinor.id)
    db.session.add(new_profile)
    db.session.commit()
    return jsonify({'message': 'Examinor registered successfully'})

@app.route('/delete_subject_course/<int:id>',methods=['POST'])
def delete_subject_course(id):
    course = SubjectCourse.query.filter_by(id=id).first()
    exams = VivaExam.query.filter_by(course_id=id).all()
    for exam in exams:
        VivaQuestion.query.filter_by(exam_id=exam.id).delete()
        slots = BookingSlot.query.filter_by(exam_id=exam.id).all()
        for slot in slots:
            bookings = StudentBooking.query.filter_by(slot_id=slot.id).all()
            for booking in bookings:
                ScoreRecord.query.filter_by(booking_id=booking.id).delete()
                VivaResult.query.filter_by(booking_id=booking.id).delete()
            StudentBooking.query.filter_by(slot_id=slot.id).delete()
        BookingSlot.query.filter_by(exam_id=exam.id).delete()
    VivaExam.query.filter_by(course_id=id).delete()
    db.session.delete(course)
    db.session.commit()
    return jsonify({'message': 'Course deleted successfully'})

@app.route('/block_examiner_access/<int:id>',methods=['POST'])
def block_examiner_access(id):
    examinor = CampusUser.query.filter_by(id=id).first()
    examinor.is_blocked = True
    db.session.commit()
    return jsonify({'message': 'Examinor blocked successfully'})

@app.route('/unblock_examiner_access/<int:id>',methods=['POST'])
def unblock_examiner_access(id):
    examinor = CampusUser.query.filter_by(id=id).first()
    examinor.is_blocked = False
    db.session.commit()
    return jsonify({'message': 'Examinor unblocked successfully'})

@app.route('/fetch_viva_list',methods=['POST','GET'])
def fetch_viva_list():
    all_examinations_list = []
    all_examinations = VivaExam.query.all()
    for examination in all_examinations:
        all_examinations_list.append(
            {
                'id': examination.id,
                'name': examination.exam_name,
                'description': examination.exam_description,
                'examinor_slot_create_start_date': examination.examinor_slot_create_start_date,
                'examinor_slot_create_end_date': examination.examinor_slot_create_end_date,
                'booking_start_time': examination.booking_start_time,
                'booking_end_time': examination.booking_end_time,
                'exam_start_date': examination.exam_start_date,
                'exam_end_date': examination.exam_end_date,
                'course_id': examination.course_id,
                'examinor_id': examination.examinor_id,
                'slot_open': bool(examination.slot_open),
                'booking_open': bool(examination.booking_open),
                'results_published': bool(examination.results_published),
                'exam_type': examination.exam_type,
                'duration': examination.duration,
                'max_marks': examination.max_marks,
                'status': examination.status,
                'exam_date_locked': are_viva_dates_locked(examination)
            }
        )
    return jsonify({'data': all_examinations_list})

@app.route('/admin_viva_details/<int:exam_id>', methods=['GET', 'POST'])
def admin_viva_details(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    course = SubjectCourse.query.filter_by(id=exam.course_id).first()
    examinor = CampusUser.query.filter_by(id=exam.examinor_id).first()
    slots = []
    for slot in BookingSlot.query.filter_by(exam_id=exam_id).all():
        booked_names = []
        evaluated = False
        for booking in StudentBooking.query.filter_by(slot_id=slot.id).all():
            student = CampusUser.query.filter_by(id=booking.user_id).first()
            if student:
                booked_names.append(student.name)
            if VivaResult.query.filter_by(booking_id=booking.id).first() or ScoreRecord.query.filter_by(booking_id=booking.id).first():
                evaluated = True
                if booking.status == 'Booked':
                    booking.status = 'Evaluated'
        slots.append({
            'id': slot.id,
            'slot_date': slot.slot_date,
            'slot_time': slot.slot_time,
            'end_time': slot.end_time,
            'capacity': slot.capacity,
            'meeting_link': slot.meeting_link,
            'status': slot.status,
            'booked_by': ', '.join(booked_names),
            'evaluated': evaluated
        })
    db.session.commit()
    return jsonify({'data': {
        'id': exam.id,
        'name': exam.exam_name,
        'description': exam.exam_description,
        'examinor_slot_create_start_date': exam.examinor_slot_create_start_date,
        'examinor_slot_create_end_date': exam.examinor_slot_create_end_date,
        'booking_start_time': exam.booking_start_time,
        'booking_end_time': exam.booking_end_time,
        'exam_start_date': exam.exam_start_date,
        'exam_end_date': exam.exam_end_date,
        'course_name': course.coures_name if course else '',
        'examinor_name': examinor.name if examinor else '',
        'examinor_id': exam.examinor_id,
        'slot_open': bool(exam.slot_open),
        'booking_open': bool(exam.booking_open),
        'results_published': bool(exam.results_published),
        'exam_type': exam.exam_type,
        'duration': exam.duration,
        'max_marks': exam.max_marks,
        'status': exam.status,
        'slots': slots
    }})

@app.route('/save_question_bank/<int:exam_id>',methods=['POST'])
def save_question_bank(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    if is_viva_finished(exam):
        return jsonify({'message': 'Questions cannot be edited after the exam is finished'})
    data = request.json
    print(data)
    new_question = VivaQuestion(
        question=data['question'],
        description=data.get('description') or '',
        marks=data['marks'],
        exam_id=exam_id
    )
    db.session.add(new_question)
    db.session.commit()
    return jsonify({'message': 'Question bank created successfully'})

@app.route('/fetch_viva_questions/<int:exam_id>', methods=['GET', 'POST'])
def fetch_viva_questions(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    questions = VivaQuestion.query.filter_by(exam_id=exam_id).all()
    rubric_list = []
    for question in questions:
        rubric_list.append({
            'id': question.id,
            'criterion': question.question,
            'description': question.description,
            'marks': question.marks,
            'weightage': question.weightage,
            'exam_id': question.exam_id
        })
    return jsonify({
        'data': rubric_list,
        'exam_name': exam.exam_name if exam else '',
        'exam_end_date': exam.exam_end_date if exam else '',
        'status': exam.status if exam else '',
        'can_edit': not is_viva_finished(exam)
    })

@app.route('/create_viva_question/<int:exam_id>', methods=['POST'])
def create_viva_question(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    if is_viva_finished(exam):
        return jsonify({'message': 'Questions cannot be edited after the exam is finished'})
    data = request.json
    new_question = VivaQuestion(
        question=data['criterion'],
        description=data['description'],
        marks=data['marks'],
        weightage=data.get('weightage', 0),
        exam_id=exam_id
    )
    db.session.add(new_question)
    db.session.commit()
    return jsonify({'message': 'Rubric created successfully'})

@app.route('/update_viva_question/<int:id>', methods=['POST'])
def update_viva_question(id):
    data = request.json
    question = VivaQuestion.query.filter_by(id=id).first()
    exam = VivaExam.query.filter_by(id=question.exam_id).first()
    if is_viva_finished(exam):
        return jsonify({'message': 'Questions cannot be edited after the exam is finished'})
    question.question = data['criterion']
    question.description = data['description']
    question.marks = data['marks']
    question.weightage = data.get('weightage', 0)
    db.session.commit()
    return jsonify({'message': 'Rubric updated successfully'})

@app.route('/delete_viva_question/<int:id>', methods=['POST'])
def delete_viva_question(id):
    question = VivaQuestion.query.filter_by(id=id).first()
    exam = VivaExam.query.filter_by(id=question.exam_id).first()
    if is_viva_finished(exam):
        return jsonify({'message': 'Questions cannot be edited after the exam is finished'})
    ScoreRecord.query.filter_by(question_id=id).delete()
    db.session.delete(question)
    db.session.commit()
    return jsonify({'message': 'Rubric deleted successfully'})

@app.route('/create_booking_slot/<int:exam_id>', methods=['POST'])
def create_booking_slot(exam_id):
    data = request.json
    exam = VivaExam.query.filter_by(id=exam_id).first()
    if not exam:
        return jsonify({'message': 'VivaExam not found'})

    today = date.today()
    slot_start = date.fromisoformat(str(exam.examinor_slot_create_start_date)[:10])
    slot_end = date.fromisoformat(str(exam.examinor_slot_create_end_date)[:10])
    in_window = slot_start <= today <= slot_end
    opened_by_admin = exam.slot_open or exam.status == 'Slot Creation'
    if not in_window and not opened_by_admin:
        return jsonify({'message': 'You can only create a slot between the slot start date and the slot end date'})

    slot_date = date.fromisoformat(str(data['slot_date'])[:10])
    exam_start = date.fromisoformat(str(exam.exam_start_date)[:10])
    exam_end = date.fromisoformat(str(exam.exam_end_date)[:10])
    if slot_date < exam_start or slot_date > exam_end:
        return jsonify({'message': 'Give the slot on an examination date, from the exam start date to the exam end date'})

    new_slot = BookingSlot(
        slot_date=data['slot_date'],
        slot_time=data['slot_time'],
        end_time=data['end_time'],
        capacity=1,
        meeting_link=data['meeting_link'],
        status='Available',
        exam_id=exam_id,
        examinor_id=data['examinor_id']
    )
    db.session.add(new_slot)
    db.session.commit()
    return jsonify({'message': 'Slot created successfully'})

@app.route('/fetch_booking_slots/<int:exam_id>', methods=['GET', 'POST'])
def fetch_booking_slots(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    slots = BookingSlot.query.filter_by(exam_id=exam_id).all()
    slot_list = []
    for slot in slots:
        examinor = CampusUser.query.filter_by(id=slot.examinor_id).first()
        taken = StudentBooking.query.filter(StudentBooking.slot_id == slot.id, StudentBooking.status != 'Cancelled').count()
        slot_list.append({
            'id': slot.id,
            'slot_date': slot.slot_date,
            'slot_time': slot.slot_time,
            'end_time': slot.end_time,
            'capacity': slot.capacity,
            'available': slot.capacity - taken,
            'meeting_link': slot.meeting_link,
            'status': slot.status,
            'examinor_id': slot.examinor_id,
            'examinor_name': examinor.name if examinor else ''
        })
    today = date.today().isoformat()
    booking_started = False
    if exam and (exam.booking_open or exam.status in ('Booking Open', 'Closed', 'Completed') or today >= exam.booking_start_time):
        booking_started = True
    return jsonify({
        'data': slot_list,
        'exam_name': exam.exam_name if exam else '',
        'booking_started': booking_started
    })

@app.route('/fetch_assigned_vivas', methods=['POST'])
def fetch_assigned_vivas():
    data = request.json
    examinor_id = data['examinor_id']

    exams = VivaExam.query.filter_by(examinor_id=examinor_id).all()
    assigned = []
    for examination in exams:
        course = SubjectCourse.query.filter_by(id=examination.course_id).first()
        assigned.append({
            'id': examination.id,
            'name': examination.exam_name,
            'description': examination.exam_description,
            'examinor_slot_create_start_date': examination.examinor_slot_create_start_date,
            'examinor_slot_create_end_date': examination.examinor_slot_create_end_date,
            'booking_start_time': examination.booking_start_time,
            'booking_end_time': examination.booking_end_time,
            'exam_start_date': examination.exam_start_date,
            'exam_end_date': examination.exam_end_date,
            'course_id': examination.course_id,
            'course_name': course.coures_name if course else '',
            'examinor_id': examination.examinor_id,
            'slot_open': bool(examination.slot_open),
            'booking_open': bool(examination.booking_open),
            'exam_type': examination.exam_type,
            'status': examination.status
        })
    return jsonify({'data': assigned, 'message': 'Assigned examinations'})

@app.route('/open_slot_window/<int:exam_id>', methods=['POST'])
def open_slot_window(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    if not exam:
        return jsonify({'message': 'VivaExam not found'})
    exam.slot_open = True
    if exam.status == 'Draft' or exam.status == 'Closed':
        exam.status = 'Slot Creation'
    db.session.commit()
    return jsonify({'message': 'Slot creation opened'})

@app.route('/close_slot_window/<int:exam_id>', methods=['POST'])
def close_slot_window(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    if not exam:
        return jsonify({'message': 'VivaExam not found'})
    exam.slot_open = False
    if exam.status == 'Slot Creation':
        exam.status = 'Draft'
    db.session.commit()
    return jsonify({'message': 'Slot creation closed'})


@app.route('/create_student_detail', methods=['POST'])
def create_student_detail():
    data = request.json
    old_profile = StudentDetail.query.filter_by(user_id=data['user_id']).first()
    if old_profile:
        return jsonify({'message': 'Profile already exists'})
    new_user_profile = StudentDetail(
        address=data['address'],
        phone=data['phone'],
        past_experience=data['past_experience'],
        user_id=data['user_id']
    )
    db.session.add(new_user_profile)
    db.session.commit()
    return jsonify({'message': 'User profile created successfully'})

@app.route('/get_student_detail', methods=['POST'])
def get_student_detail():
    data = request.json
    profile = StudentDetail.query.filter_by(user_id=data['user_id']).first()
    if not profile:
        return jsonify({'data': None})
    return jsonify({'data': {
        'id': profile.id,
        'address': profile.address,
        'phone': profile.phone,
        'past_experience': profile.past_experience,
        'user_id': profile.user_id
    }})

@app.route('/update_student_detail', methods=['POST'])
def update_student_detail():
    data = request.json
    profile = StudentDetail.query.filter_by(user_id=data['user_id']).first()
    profile.address = data['address']
    profile.phone = data['phone']
    profile.past_experience = data['past_experience']
    db.session.commit()
    return jsonify({'message': 'User profile updated successfully'})

@app.route('/fetch_open_vivas', methods=['POST','GET'])
def fetch_open_vivas():
    all_examinations_list = []
    slots = BookingSlot.query.all()
    for slot in slots:
        examination = VivaExam.query.filter_by(id=slot.exam_id).first()
        if slot.status == 'Cancelled':
            continue
        course = SubjectCourse.query.filter_by(id=examination.course_id).first() if examination else None
        taken = StudentBooking.query.filter(StudentBooking.slot_id == slot.id, StudentBooking.status != 'Cancelled').count()
        all_examinations_list.append({
            'id': slot.id,
            'exam_id': slot.exam_id,
            'name': examination.exam_name if examination else '',
            'exam_type': examination.exam_type if examination else '',
            'course_name': course.coures_name if course else '',
            'status': examination.status if examination else '',
            'slot_date': slot.slot_date,
            'slot_time': slot.slot_time,
            'end_time': slot.end_time,
            'available': slot.capacity - taken,
            'meeting_link': slot.meeting_link
        })
    return jsonify({'data1': all_examinations_list})

@app.route('/book_viva_slot/<int:slot_id>', methods=['POST'])
def book_viva_slot(slot_id):
    data = request.json
    slot = BookingSlot.query.filter_by(id=slot_id).first()
    exam = VivaExam.query.filter_by(id=slot.exam_id).first()
    today = date.today().isoformat()
    if exam.status == 'Closed' or exam.status == 'Completed':
        return jsonify({'message': 'Booking is closed'})
    opened_by_admin = exam.booking_open or exam.status == 'Booking Open'
    if not opened_by_admin and (today < exam.booking_start_time or today > exam.booking_end_time):
        return jsonify({'message': 'Booking is closed'})
    old_booking = StudentBooking.query.filter_by(slot_id=slot_id, user_id=data['user_id'], status='Booked').first()
    if old_booking:
        return jsonify({'message': 'Slot already booked'})
    booked_count = StudentBooking.query.filter(StudentBooking.slot_id == slot_id, StudentBooking.status != 'Cancelled').count()
    if booked_count >= slot.capacity:
        return jsonify({'message': 'Slot is full'})
    new_booking = StudentBooking(slot_id=slot_id, user_id=data['user_id'], booking_date=today, status='Booked')
    db.session.add(new_booking)
    db.session.commit()
    booked_count = StudentBooking.query.filter(StudentBooking.slot_id == slot_id, StudentBooking.status != 'Cancelled').count()
    if booked_count >= slot.capacity:
        slot.status = 'Full'
    else:
        slot.status = 'Available'
    db.session.commit()
    return jsonify({'message': 'Slot booked successfully'})

@app.route('/get_viva_details/<int:exam_id>', methods=['POST'])
def get_viva_details(exam_id):
    data = request.json
    exam = VivaExam.query.filter_by(id=exam_id).first()
    course = SubjectCourse.query.filter_by(id=exam.course_id).first()
    examinor = CampusUser.query.filter_by(id=exam.examinor_id).first()
    today = date.today().isoformat()
    if exam.status == 'Closed' or exam.status == 'Completed':
        booking_open = False
    elif exam.booking_open or exam.status == 'Booking Open':
        booking_open = True
    else:
        booking_open = exam.booking_start_time <= today <= exam.booking_end_time
    slots = []
    for slot in BookingSlot.query.filter_by(exam_id=exam_id).all():
        if slot.status == 'Cancelled':
            continue
        booking = StudentBooking.query.filter_by(slot_id=slot.id, user_id=data['user_id'], status='Booked').first()
        taken = StudentBooking.query.filter(StudentBooking.slot_id == slot.id, StudentBooking.status != 'Cancelled').count()
        slots.append({
            'id': slot.id,
            'slot_date': slot.slot_date,
            'slot_time': slot.slot_time,
            'end_time': slot.end_time,
            'capacity': slot.capacity,
            'available': slot.capacity - taken,
            'meeting_link': slot.meeting_link,
            'status': slot.status,
            'booked': booking is not None
        })
    return jsonify({'data': {
        'id': exam.id,
        'name': exam.exam_name,
        'description': exam.exam_description,
        'examinor_slot_create_start_date': exam.examinor_slot_create_start_date,
        'examinor_slot_create_end_date': exam.examinor_slot_create_end_date,
        'booking_start_time': exam.booking_start_time,
        'booking_end_time': exam.booking_end_time,
        'exam_start_date': exam.exam_start_date,
        'exam_end_date': exam.exam_end_date,
        'course_name': course.coures_name if course else '',
        'examinor_name': examinor.name if examinor else '',
        'exam_type': exam.exam_type,
        'duration': exam.duration,
        'max_marks': exam.max_marks,
        'status': exam.status,
        'booking_open': booking_open,
        'slots': slots
    }})

@app.route('/cancel_viva_booking/<int:slot_id>', methods=['POST'])
def cancel_viva_booking(slot_id):
    data = request.json
    slot = BookingSlot.query.filter_by(id=slot_id).first()
    exam = VivaExam.query.filter_by(id=slot.exam_id).first()
    today = date.today().isoformat()
    opened_by_admin = exam.booking_open or exam.status == 'Booking Open'
    if exam.status == 'Closed' or exam.status == 'Completed':
        return jsonify({'message': 'Booking period is closed'})
    if not opened_by_admin and (today < exam.booking_start_time or today > exam.booking_end_time):
        return jsonify({'message': 'Booking period is closed'})
    booking = StudentBooking.query.filter_by(slot_id=slot_id, user_id=data['user_id'], status='Booked').first()
    if not booking:
        return jsonify({'message': 'Slot is not booked'})
    booking.status = 'Cancelled'
    taken = StudentBooking.query.filter(StudentBooking.slot_id == slot_id, StudentBooking.status != 'Cancelled').count()
    if taken >= slot.capacity:
        slot.status = 'Full'
    else:
        slot.status = 'Available'
    db.session.commit()
    return jsonify({'message': 'Slot cancelled successfully'})

@app.route('/fetch_my_bookings', methods=['POST'])
def fetch_my_bookings():
    data = request.json
    today = date.today().isoformat()
    bookings = StudentBooking.query.filter_by(user_id=data['user_id']).all()
    booking_list = []
    for booking in bookings:
        slot = BookingSlot.query.filter_by(id=booking.slot_id).first()
        exam = VivaExam.query.filter_by(id=slot.exam_id).first()
        evaluation = VivaResult.query.filter_by(booking_id=booking.id).first()
        booking_open = False
        if exam and exam.status != 'Closed' and exam.status != 'Completed':
            if exam.booking_open or exam.status == 'Booking Open':
                booking_open = True
            else:
                booking_open = exam.booking_start_time <= today <= exam.booking_end_time
        booking_list.append({
            'id': booking.id,
            'slot_id': slot.id,
            'exam_id': exam.id if exam else '',
            'name': exam.exam_name if exam else '',
            'slot_date': slot.slot_date,
            'slot_time': slot.slot_time,
            'booking_date': booking.booking_date,
            'status': booking.status,
            'booking_open': booking_open,
            'results_published': bool(exam.results_published) if exam else False,
            'marks': evaluation.total_marks if evaluation and exam and exam.results_published else '',
            'remarks': evaluation.remarks if evaluation and exam and exam.results_published else ''
        })
    return jsonify({'data': booking_list})

@app.route('/fetch_examiner_bookings', methods=['POST'])
def fetch_examiner_bookings():
    data = request.json
    examinor_id = str(data['examinor_id'])
    booking_list = []
    bookings = StudentBooking.query.all()
    for booking in bookings:
        slot = BookingSlot.query.filter_by(id=booking.slot_id).first()
        if not slot:
            continue
        exam = VivaExam.query.filter_by(id=slot.exam_id).first()
        if not exam:
            continue
        if booking.status == 'Cancelled':
            continue
        effective_id = booking.assigned_examinor_id if booking.assigned_examinor_id else slot.examinor_id
        if str(effective_id) != examinor_id:
            continue
        student = CampusUser.query.filter_by(id=booking.user_id).first()
        evaluation = VivaResult.query.filter_by(booking_id=booking.id).first()
        given_marks = ScoreRecord.query.filter_by(booking_id=booking.id).all()
        total_marks = sum(mark.marks for mark in given_marks)
        booking_list.append({
            'id': booking.id,
            'name': exam.exam_name,
            'student_name': student.name if student else '',
            'slot_date': slot.slot_date,
            'slot_time': slot.slot_time,
            'marks': evaluation.total_marks if evaluation else (total_marks if given_marks else ''),
            'remarks': evaluation.remarks if evaluation else '',
            'evaluation_status': evaluation.status if evaluation else 'Pending'
        })
    return jsonify({'data': booking_list})

@app.route('/submit_viva_marks/<int:booking_id>', methods=['GET', 'POST'])
def submit_viva_marks(booking_id):
    booking = StudentBooking.query.filter_by(id=booking_id).first()
    slot = BookingSlot.query.filter_by(id=booking.slot_id).first()
    exam = VivaExam.query.filter_by(id=slot.exam_id).first()
    student = CampusUser.query.filter_by(id=booking.user_id).first()
    if request.method == 'GET':
        questions = []
        for question in VivaQuestion.query.filter_by(exam_id=exam.id).all():
            given = ScoreRecord.query.filter_by(booking_id=booking_id, question_id=question.id).first()
            questions.append({
                'id': question.id,
                'criterion': question.question,
                'description': question.description,
                'max_marks': question.marks,
                'weightage': question.weightage,
                'marks': given.marks if given else ''
            })
        evaluation = VivaResult.query.filter_by(booking_id=booking_id).first()
        return jsonify({'data': {
            'booking_id': booking.id,
            'exam_name': exam.exam_name if exam else '',
            'student_name': student.name if student else '',
            'remarks': evaluation.remarks if evaluation else '',
            'rubrics': questions
        }})
    data = request.json
    total = 0
    for item in data['rubrics']:
        question = VivaQuestion.query.filter_by(id=item['question_id']).first()
        if int(item['marks']) > question.marks:
            return jsonify({'message': 'Marks cannot be more than rubric marks'})
        given = ScoreRecord.query.filter_by(booking_id=booking_id, question_id=item['question_id']).first()
        if given:
            given.marks = item['marks']
        else:
            db.session.add(ScoreRecord(booking_id=booking_id, question_id=item['question_id'], marks=item['marks']))
        total = total + int(item['marks'])
    evaluation = VivaResult.query.filter_by(booking_id=booking_id).first()
    examinor_id = booking.assigned_examinor_id if booking.assigned_examinor_id else slot.examinor_id
    if evaluation:
        evaluation.total_marks = total
        evaluation.remarks = data['remarks']
        evaluation.evaluation_date = str(date.today())
        evaluation.status = 'Submitted'
        evaluation.examinor_id = examinor_id
    else:
        db.session.add(VivaResult(booking_id=booking.id, student_id=booking.user_id, examinor_id=examinor_id, total_marks=total, remarks=data['remarks'], evaluation_date=str(date.today()), status='Submitted'))
    if booking.status == 'Booked':
        booking.status = 'Evaluated'
    db.session.commit()
    return jsonify({'message': 'Marks saved successfully'})


@app.route('/portal_admin_stats', methods=['POST', 'GET'])
@cache.cached(timeout=60)
def portal_admin_stats():
    print("Fetching data from DATABASE")

    return jsonify({'data': {
        'courses': SubjectCourse.query.count(),
        'exams': VivaExam.query.count(),
        'students': CampusUser.query.filter_by(role='user').count(),
        'examinors': CampusUser.query.filter_by(role='examinor').count(),
        'slots': BookingSlot.query.count(),
        'bookings': StudentBooking.query.count()
    }})

@app.route('/update_viva_exam/<int:exam_id>', methods=['POST'])
def update_viva_exam(exam_id):
    data = request.json
    exam = VivaExam.query.filter_by(id=exam_id).first()
    exam.exam_name = data['exam_name']
    exam.exam_description = data['exam_description']
    exam.exam_type = data['exam_type']
    exam.duration = data['duration']
    exam.max_marks = data['max_marks']
    exam.examinor_slot_create_start_date = data['examinor_slot_create_start_date']
    exam.examinor_slot_create_end_date = data['examinor_slot_create_end_date']
    exam.booking_start_time = data['booking_start_time']
    exam.booking_end_time = data['booking_end_time']
    new_start = str(data['exam_start_date'])[:10]
    new_end = str(data['exam_end_date'])[:10]
    old_start = str(exam.exam_start_date)[:10]
    old_end = str(exam.exam_end_date)[:10]
    if are_viva_dates_locked(exam) and (new_start != old_start or new_end != old_end):
        db.session.rollback()
        return jsonify({'message': 'Exam date cannot be changed after booking is closed or a booking has happened'})
    exam.exam_start_date = data['exam_start_date']
    exam.exam_end_date = data['exam_end_date']
    exam.course_id = data['course_id']
    if str(data['examinor_id']) != str(exam.examinor_id):
        conflict = viva_staff_conflict(exam, data['examinor_id'])
        if conflict:
            db.session.rollback()
            return jsonify({'message': conflict})
    exam.examinor_id = data['examinor_id']
    exam.status = data['status']
    if data['status'] == 'Slot Creation':
        exam.slot_open = True
    elif data['status'] == 'Booking Open':
        exam.booking_open = True
    elif data['status'] in ('Draft', 'Closed', 'Completed'):
        exam.slot_open = False
        exam.booking_open = False
    db.session.commit()
    return jsonify({'message': 'VivaExam updated successfully'})

@app.route('/delete_viva_exam/<int:exam_id>', methods=['POST'])
def delete_viva_exam(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    slots = BookingSlot.query.filter_by(exam_id=exam_id).all()
    for slot in slots:
        bookings = StudentBooking.query.filter_by(slot_id=slot.id).all()
        for booking in bookings:
            ScoreRecord.query.filter_by(booking_id=booking.id).delete()
            VivaResult.query.filter_by(booking_id=booking.id).delete()
        StudentBooking.query.filter_by(slot_id=slot.id).delete()
    BookingSlot.query.filter_by(exam_id=exam_id).delete()
    VivaQuestion.query.filter_by(exam_id=exam_id).delete()
    db.session.delete(exam)
    db.session.commit()
    return jsonify({'message': 'VivaExam deleted successfully'})

@app.route('/open_viva_booking/<int:exam_id>', methods=['POST'])
def open_viva_booking(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    exam.booking_open = True
    exam.status = 'Booking Open'
    db.session.commit()
    return jsonify({'message': 'Student booking opened'})

@app.route('/close_viva_booking/<int:exam_id>', methods=['POST'])
def close_viva_booking(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    exam.booking_open = False
    if exam.status != 'Completed':
        exam.status = 'Closed'
    db.session.commit()
    return jsonify({'message': 'Student booking closed'})

@app.route('/publish_viva_results/<int:exam_id>', methods=['POST'])
def publish_viva_results(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    exam.results_published = True
    for slot in BookingSlot.query.filter_by(exam_id=exam_id).all():
        for booking in StudentBooking.query.filter_by(slot_id=slot.id).all():
            evaluation = VivaResult.query.filter_by(booking_id=booking.id).first()
            if evaluation:
                evaluation.status = 'Published'
    db.session.commit()
    return jsonify({'message': 'Results published'})

def viva_staff_conflict(exam, examinor_id):
    new_id = int(examinor_id)
    if int(exam.examinor_id) == new_id:
        return None
    exam_slots = [slot for slot in BookingSlot.query.filter_by(exam_id=exam.id).all() if slot.status != 'Cancelled']
    for slot in exam_slots:
        start, end = booking_slot_range(slot.slot_time, slot.end_time, exam.duration)
        for other in BookingSlot.query.all():
            if other.id == slot.id or other.exam_id == exam.id or other.status == 'Cancelled':
                continue
            if str(other.slot_date)[:10] != str(slot.slot_date)[:10]:
                continue
            owns_slot = int(other.examinor_id) == new_id
            if not owns_slot:
                for booking in StudentBooking.query.filter_by(slot_id=other.id).all():
                    if booking.status != 'Cancelled' and booking.assigned_examinor_id and int(booking.assigned_examinor_id) == new_id:
                        owns_slot = True
                        break
            if not owns_slot:
                continue
            other_exam = VivaExam.query.filter_by(id=other.exam_id).first()
            duration = other_exam.duration if other_exam else 30
            other_start, other_end = booking_slot_range(other.slot_time, other.end_time, duration)
            if time_ranges_overlap(start, end, other_start, other_end):
                person = CampusUser.query.filter_by(id=new_id).first()
                name = person.name if person else 'This examiner'
                return name + ' is not free on ' + str(slot.slot_date)[:10] + ' at ' + str(slot.slot_time)
    return None

@app.route('/change_viva_examiner/<int:exam_id>', methods=['POST'])
def change_viva_examiner(exam_id):
    data = request.json
    exam = VivaExam.query.filter_by(id=exam_id).first()
    conflict = viva_staff_conflict(exam, data['examinor_id'])
    if conflict:
        return jsonify({'message': conflict})
    old_id = exam.examinor_id
    exam.examinor_id = data['examinor_id']
    for slot in BookingSlot.query.filter_by(exam_id=exam_id).all():
        if slot.examinor_id == old_id:
            slot.examinor_id = data['examinor_id']
        for booking in StudentBooking.query.filter_by(slot_id=slot.id).all():
            booking.assigned_examinor_id = data['examinor_id']
    db.session.commit()
    return jsonify({'message': 'Examiner changed successfully'})

@app.route('/update_booking_slot/<int:slot_id>', methods=['POST'])
def update_booking_slot(slot_id):
    data = request.json
    slot = BookingSlot.query.filter_by(id=slot_id).first()
    exam = VivaExam.query.filter_by(id=slot.exam_id).first()
    today = date.today().isoformat()
    if exam.booking_open or exam.status in ('Booking Open', 'Closed', 'Completed') or today >= exam.booking_start_time:
        return jsonify({'message': 'Slots can only be updated before student booking begins'})
    slot.slot_date = data['slot_date']
    slot.slot_time = data['slot_time']
    slot.end_time = data['end_time']
    slot.capacity = 1
    slot.meeting_link = data['meeting_link']
    db.session.commit()
    return jsonify({'message': 'Slot updated successfully'})

@app.route('/delete_booking_slot/<int:slot_id>', methods=['POST'])
def delete_booking_slot(slot_id):
    slot = BookingSlot.query.filter_by(id=slot_id).first()
    exam = VivaExam.query.filter_by(id=slot.exam_id).first()
    today = date.today().isoformat()
    if exam.booking_open or exam.status in ('Booking Open', 'Closed', 'Completed') or today >= exam.booking_start_time:
        return jsonify({'message': 'Slots can only be removed before student booking begins'})
    if StudentBooking.query.filter(StudentBooking.slot_id == slot_id, StudentBooking.status != 'Cancelled').count():
        return jsonify({'message': 'Cannot remove a slot that has bookings'})
    for booking in StudentBooking.query.filter_by(slot_id=slot_id).all():
        ScoreRecord.query.filter_by(booking_id=booking.id).delete()
        VivaResult.query.filter_by(booking_id=booking.id).delete()
        db.session.delete(booking)
    db.session.delete(slot)
    db.session.commit()
    return jsonify({'message': 'Slot removed successfully'})

def parse_time_minutes(value):
    text = str(value or '')[:5]
    parts = text.split(':')
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return None
    return int(parts[0]) * 60 + int(parts[1])

def booking_slot_range(start_value, end_value, duration):
    start = parse_time_minutes(start_value)
    end = parse_time_minutes(end_value)
    if start is not None and end is None:
        end = start + int(duration or 30)
    return start, end

def time_ranges_overlap(start_a, end_a, start_b, end_b):
    if None in (start_a, end_a, start_b, end_b):
        return start_a is not None and start_a == start_b
    return start_a < end_b and start_b < end_a

@app.route('/move_booking_slot/<int:slot_id>', methods=['POST'])
def move_booking_slot(slot_id):
    data = request.json
    slot = BookingSlot.query.filter_by(id=slot_id).first()
    if not slot:
        return jsonify({'message': 'Slot not found'})
    for booking in StudentBooking.query.filter_by(slot_id=slot.id).all():
        if booking.status == 'Cancelled':
            continue
        if VivaResult.query.filter_by(booking_id=booking.id).first() or ScoreRecord.query.filter_by(booking_id=booking.id).first():
            return jsonify({'message': 'Marks have already been given, so this slot cannot be rescheduled'})
    exam = VivaExam.query.filter_by(id=slot.exam_id).first()
    slot_date = date.fromisoformat(str(data['slot_date'])[:10])
    exam_start = date.fromisoformat(str(exam.exam_start_date)[:10])
    exam_end = date.fromisoformat(str(exam.exam_end_date)[:10])
    if slot_date < exam_start or slot_date > exam_end:
        return jsonify({'message': 'Reschedule only on an exam date, from the exam start date to the exam end date'})
    new_start, new_end = booking_slot_range(data['slot_time'], data.get('end_time') or slot.end_time, exam.duration)
    if new_start is None or new_end is None or new_end <= new_start:
        return jsonify({'message': 'Choose a free time on the exam date'})
    for other in BookingSlot.query.filter_by(exam_id=slot.exam_id).all():
        if other.id == slot.id or other.status == 'Cancelled':
            continue
        if str(other.slot_date)[:10] != str(data['slot_date'])[:10]:
            continue
        other_start, other_end = booking_slot_range(other.slot_time, other.end_time, exam.duration)
        if time_ranges_overlap(new_start, new_end, other_start, other_end):
            return jsonify({'message': 'That time is not free. Choose a free time on the exam date'})
    slot.slot_date = str(data['slot_date'])[:10]
    slot.slot_time = data['slot_time']
    slot.end_time = data.get('end_time') or slot.end_time
    db.session.commit()
    return jsonify({'message': 'Slot rescheduled successfully'})

@app.route('/move_student_booking/<int:booking_id>', methods=['POST'])
def move_student_booking(booking_id):
    data = request.json
    booking = StudentBooking.query.filter_by(id=booking_id).first()
    booking.slot_id = data['slot_id']
    db.session.commit()
    return jsonify({'message': 'Booking moved successfully'})

@app.route('/reassign_booking_staff/<int:booking_id>', methods=['POST'])
def reassign_booking_staff(booking_id):
    data = request.json
    booking = StudentBooking.query.filter_by(id=booking_id).first()
    booking.assigned_examinor_id = data['examinor_id']
    db.session.commit()
    return jsonify({'message': 'Examiner reassigned successfully'})

@app.route('/fetch_student_list', methods=['GET', 'POST'])
def fetch_student_list():
    students = []
    for user in CampusUser.query.filter_by(role='user').all():
        students.append({'id': user.id, 'name': user.name, 'email': user.email, 'is_blocked': user.is_blocked})
    return jsonify({'data': students})

@app.route('/block_student_access/<int:id>', methods=['POST'])
def block_student_access(id):
    student = CampusUser.query.filter_by(id=id).first()
    student.is_blocked = True
    db.session.commit()
    return jsonify({'message': 'Student blocked successfully'})

@app.route('/unblock_student_access/<int:id>', methods=['POST'])
def unblock_student_access(id):
    student = CampusUser.query.filter_by(id=id).first()
    student.is_blocked = False
    db.session.commit()
    return jsonify({'message': 'Student unblocked successfully'})

@app.route('/fetch_all_bookings', methods=['GET', 'POST'])
def fetch_all_bookings():
    rows = []
    for booking in StudentBooking.query.all():
        slot = BookingSlot.query.filter_by(id=booking.slot_id).first()
        exam = VivaExam.query.filter_by(id=slot.exam_id).first() if slot else None
        student = CampusUser.query.filter_by(id=booking.user_id).first()
        examinor_id = booking.assigned_examinor_id if booking.assigned_examinor_id else (slot.examinor_id if slot else None)
        examinor = CampusUser.query.filter_by(id=examinor_id).first()
        evaluated = VivaResult.query.filter_by(booking_id=booking.id).first() is not None or ScoreRecord.query.filter_by(booking_id=booking.id).first() is not None
        if evaluated and booking.status == 'Booked':
            booking.status = 'Evaluated'
        rows.append({
            'id': booking.id,
            'student_name': student.name if student else '',
            'student_email': student.email if student else '',
            'exam_id': exam.id if exam else '',
            'exam_name': exam.exam_name if exam else '',
            'slot_id': slot.id if slot else '',
            'slot_date': slot.slot_date if slot else '',
            'slot_time': slot.slot_time if slot else '',
            'end_time': slot.end_time if slot else '',
            'exam_start_date': str(exam.exam_start_date)[:10] if exam else '',
            'exam_end_date': str(exam.exam_end_date)[:10] if exam else '',
            'status': booking.status,
            'booking_date': booking.booking_date,
            'examinor_id': examinor_id,
            'examinor_name': examinor.name if examinor else '',
            'evaluated': evaluated
        })
    db.session.commit()
    slots = []
    for slot in BookingSlot.query.all():
        slots.append({'id': slot.id, 'exam_id': slot.exam_id, 'slot_date': slot.slot_date, 'slot_time': slot.slot_time})
    examinors = []
    for user in CampusUser.query.filter_by(role='examinor').all():
        examinors.append({'id': user.id, 'name': user.name})
    return jsonify({'data': rows, 'slots': slots, 'examinors': examinors})

@app.route('/fetch_all_slots', methods=['GET', 'POST'])
def fetch_all_slots():
    rows = []
    for slot in BookingSlot.query.all():
        exam = VivaExam.query.filter_by(id=slot.exam_id).first()
        examinor = CampusUser.query.filter_by(id=slot.examinor_id).first()
        taken_bookings = StudentBooking.query.filter(StudentBooking.slot_id == slot.id, StudentBooking.status != 'Cancelled').all()
        booked_names = []
        for booking in taken_bookings:
            student = CampusUser.query.filter_by(id=booking.user_id).first()
            if student:
                booked_names.append(student.name)
        rows.append({
            'id': slot.id,
            'exam_id': slot.exam_id,
            'exam_name': exam.exam_name if exam else '',
            'examinor_id': slot.examinor_id,
            'examinor_name': examinor.name if examinor else '',
            'slot_date': slot.slot_date,
            'slot_time': slot.slot_time,
            'end_time': slot.end_time,
            'capacity': slot.capacity,
            'available': slot.capacity - len(taken_bookings),
            'meeting_link': slot.meeting_link,
            'status': slot.status,
            'booked_by': ', '.join(booked_names)
        })
    return jsonify({'data': rows})

@app.route('/portal_admin_search', methods=['POST'])
def portal_admin_search():
    data = request.json
    query = data['query'].lower()
    students = []
    for user in CampusUser.query.filter_by(role='user').all():
        if query in user.name.lower() or query in user.email.lower():
            students.append({'id': user.id, 'name': user.name, 'email': user.email, 'is_blocked': user.is_blocked})
    examinors = []
    for user in CampusUser.query.filter_by(role='examinor').all():
        profile = ExaminerDetail.query.filter_by(user_id=user.id).first()
        department = profile.department if profile else ''
        if query in user.name.lower() or query in user.email.lower() or query in department.lower():
            examinors.append({'id': user.id, 'name': user.name, 'email': user.email, 'department': department, 'is_blocked': user.is_blocked})
    exams = []
    for exam in VivaExam.query.all():
        if query in exam.exam_name.lower() or query in exam.exam_type.lower() or query in exam.status.lower():
            exams.append({'id': exam.id, 'name': exam.exam_name, 'exam_type': exam.exam_type, 'status': exam.status})
    bookings = []
    for booking in StudentBooking.query.all():
        slot = BookingSlot.query.filter_by(id=booking.slot_id).first()
        exam = VivaExam.query.filter_by(id=slot.exam_id).first() if slot else None
        student = CampusUser.query.filter_by(id=booking.user_id).first()
        text = ((student.name if student else '') + ' ' + (exam.exam_name if exam else '') + ' ' + booking.status).lower()
        if query in text:
            bookings.append({'id': booking.id, 'student_name': student.name if student else '', 'exam_name': exam.exam_name if exam else '', 'status': booking.status})
    return jsonify({'students': students, 'examinors': examinors, 'exams': exams, 'bookings': bookings})

@app.route('/portal_admin_reports', methods=['GET', 'POST'])
def portal_admin_reports():
    exam_rows = []
    for exam in VivaExam.query.all():
        booking_count = 0
        total = 0
        counted = 0
        for slot in BookingSlot.query.filter_by(exam_id=exam.id).all():
            for booking in StudentBooking.query.filter_by(slot_id=slot.id).all():
                if booking.status == 'Cancelled':
                    continue
                booking_count = booking_count + 1
                evaluation = VivaResult.query.filter_by(booking_id=booking.id).first()
                if evaluation:
                    total = total + evaluation.total_marks
                    counted = counted + 1
        average = ''
        if counted:
            average = round(total / counted, 2)
        exam_rows.append({
            'name': exam.exam_name,
            'exam_type': exam.exam_type,
            'status': exam.status,
            'bookings': booking_count,
            'average_marks': average,
            'results_published': bool(exam.results_published)
        })
    return jsonify({'data': {
        'courses': SubjectCourse.query.count(),
        'exams': VivaExam.query.count(),
        'students': CampusUser.query.filter_by(role='user').count(),
        'examinors': CampusUser.query.filter_by(role='examinor').count(),
        'slots': BookingSlot.query.count(),
        'bookings': StudentBooking.query.count(),
        'exam_rows': exam_rows
    }})

@app.route('/examiner_portal_stats', methods=['POST'])
@cache.cached(timeout=60)
def examiner_portal_stats():
    data = request.json
    examinor_id = str(data['examinor_id'])
    assigned = VivaExam.query.filter_by(examinor_id=data['examinor_id']).count()
    slots = BookingSlot.query.filter_by(examinor_id=data['examinor_id']).count()
    booked_students = 0
    pending = 0
    for booking in StudentBooking.query.all():
        if booking.status == 'Cancelled':
            continue
        slot = BookingSlot.query.filter_by(id=booking.slot_id).first()
        if not slot:
            continue
        effective_id = booking.assigned_examinor_id if booking.assigned_examinor_id else slot.examinor_id
        if str(effective_id) != examinor_id:
            continue
        booked_students = booked_students + 1
        evaluation = VivaResult.query.filter_by(booking_id=booking.id).first()
        if not evaluation:
            pending = pending + 1
    return jsonify({'data': {
        'assigned': assigned,
        'slots': slots,
        'booked_students': booked_students,
        'pending_evaluations': pending
    }})

@app.route('/complete_viva_exam/<int:exam_id>', methods=['POST'])
def complete_viva_exam(exam_id):
    exam = VivaExam.query.filter_by(id=exam_id).first()
    exam.status = 'Completed'
    exam.slot_open = False
    exam.booking_open = False
    for slot in BookingSlot.query.filter_by(exam_id=exam_id).all():
        if slot.status != 'Cancelled':
            slot.status = 'Completed'
        for booking in StudentBooking.query.filter_by(slot_id=slot.id).all():
            if booking.status == 'Booked':
                booking.status = 'Completed'
    db.session.commit()
    return jsonify({'message': 'VivaExam marked as completed'})

@app.route('/get_examiner_detail', methods=['POST'])
def get_examiner_detail():
    data = request.json
    profile = ExaminerDetail.query.filter_by(user_id=data['user_id']).first()
    if not profile:
        return jsonify({'data': None})
    return jsonify({'data': {
        'id': profile.id,
        'address': profile.address,
        'phone': profile.phone,
        'past_experience': profile.past_experience,
        'department': profile.department
    }})

@app.route('/update_examiner_detail', methods=['POST'])
def update_examiner_detail():
    data = request.json
    profile = ExaminerDetail.query.filter_by(user_id=data['user_id']).first()
    profile.address = data['address']
    profile.phone = data['phone']
    profile.past_experience = data['past_experience']
    profile.department = data['department']
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'})

@app.route('/update_examiner_user/<int:id>', methods=['POST'])
def update_examiner_user(id):
    data = request.json
    examinor = CampusUser.query.filter_by(id=id).first()
    examinor.name = data['name']
    profile = ExaminerDetail.query.filter_by(user_id=id).first()
    if not profile:
        profile = ExaminerDetail(address='', phone=data['phone'], past_experience='', department=data['department'], user_id=id)
        db.session.add(profile)
    else:
        profile.phone = data['phone']
        profile.department = data['department']
    db.session.commit()
    return jsonify({'message': 'Examiner updated successfully'})

@app.route('/student_portal_home', methods=['POST'])
def student_portal_home():
    data = request.json
    today = date.today().isoformat()
    available_exams = 0
    available_slots = 0
    seen = []
    for slot in BookingSlot.query.all():
        if slot.status == 'Cancelled':
            continue
        exam = VivaExam.query.filter_by(id=slot.exam_id).first()
        if not exam:
            continue
        open_now = False
        if exam.status != 'Closed' and exam.status != 'Completed':
            if exam.booking_open or exam.status == 'Booking Open':
                open_now = True
            elif exam.booking_start_time <= today <= exam.booking_end_time:
                open_now = True
        taken = StudentBooking.query.filter(StudentBooking.slot_id == slot.id, StudentBooking.status != 'Cancelled').count()
        if open_now and taken < slot.capacity:
            available_slots = available_slots + 1
            if exam.id not in seen:
                seen.append(exam.id)
                available_exams = available_exams + 1
    upcoming = 0
    booked = 0
    results = 0
    examinations = []
    for booking in StudentBooking.query.filter_by(user_id=data['user_id']).all():
        if booking.status == 'Cancelled':
            continue
        slot = BookingSlot.query.filter_by(id=booking.slot_id).first()
        exam = VivaExam.query.filter_by(id=slot.exam_id).first() if slot else None
        if booking.status == 'Booked':
            booked = booked + 1
            if slot and slot.slot_date >= today:
                upcoming = upcoming + 1
        if exam and exam.results_published:
            results = results + 1
        if slot and exam and booking.status == 'Booked':
            examinations.append({
                'id': booking.id,
                'name': exam.exam_name,
                'slot_date': slot.slot_date,
                'slot_time': slot.slot_time,
                'meeting_link': slot.meeting_link
            })
    return jsonify({'data': {
        'available_exams': available_exams,
        'available_slots': available_slots,
        'examinations': examinations,
        'upcoming': upcoming,
        'booked': booked,
        'results': results
    }})

@app.route('/fetch_my_results', methods=['POST'])
def fetch_my_results():
    data = request.json
    results = []
    for booking in StudentBooking.query.filter_by(user_id=data['user_id']).all():
        if booking.status == 'Cancelled':
            continue
        slot = BookingSlot.query.filter_by(id=booking.slot_id).first()
        exam = VivaExam.query.filter_by(id=slot.exam_id).first() if slot else None
        if not exam or not exam.results_published:
            continue
        evaluation = VivaResult.query.filter_by(booking_id=booking.id).first()
        rubrics = []
        for question in VivaQuestion.query.filter_by(exam_id=exam.id).all():
            given = ScoreRecord.query.filter_by(booking_id=booking.id, question_id=question.id).first()
            rubrics.append({
                'criterion': question.question,
                'max_marks': question.marks,
                'weightage': question.weightage,
                'marks': given.marks if given else ''
            })
        results.append({
            'exam_name': exam.exam_name,
            'exam_type': exam.exam_type,
            'max_marks': exam.max_marks,
            'total_marks': evaluation.total_marks if evaluation else '',
            'remarks': evaluation.remarks if evaluation else '',
            'evaluation_date': evaluation.evaluation_date if evaluation else '',
            'rubrics': rubrics
        })
    return jsonify({'data': results})
@app.route('/download_history_csv/<int:job_id>', methods=['GET'])
def download_history_csv(job_id):
    job = DataExport.query.filter_by(id=job_id, user_id=request.args.get('user_id')).first()
    if not job or job.status != 'completed' or not job.file_name:
        return jsonify({'message': 'Export file is not ready'})
    path = os.path.join(EXPORT_DIR, job.file_name)
    if not os.path.isfile(path):
        return jsonify({'message': 'Export file is missing'})
    return send_file(path, as_attachment=True, download_name=job.file_name)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin_email = 'portaladmin@studentportal.edu'
        admin_user = CampusUser.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = CampusUser(
                name='Portal Admin',
                email=admin_email,
                password='PortalAdmin@26',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)