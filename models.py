# models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(255))

class Housing(db.Model):
    __tablename__ = 'housing'
    housing_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255))
    monthly_rent = db.Column(db.Integer)

class Room(db.Model):
    __tablename__ = 'room'
    room_id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(50))
    housing_id = db.Column(db.Integer, db.ForeignKey('housing.housing_id'))
    available = db.Column(db.Boolean)

class Booking(db.Model):
    __tablename__ = 'booking'
    booking_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'))
    booking_date = db.Column(db.Date)
    payment_status = db.Column(db.String(20))

class RoommateMatch(db.Model):
    __tablename__ = 'roommate_match'
    match_id = db.Column(db.Integer, primary_key=True)
    student1_id = db.Column(db.Integer, db.ForeignKey('student.student_id'))
    student2_id = db.Column(db.Integer, db.ForeignKey('student.student_id'))
    compatibility_score = db.Column(db.Numeric(5,2))

class ConflictReport(db.Model):
    __tablename__ = 'conflict_report'
    conflict_id = db.Column(db.Integer, primary_key=True)
    reporter_student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'))
    reported_student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'))
    description = db.Column(db.Text)
    report_date = db.Column(db.Date)
    resolved = db.Column(db.Boolean)
