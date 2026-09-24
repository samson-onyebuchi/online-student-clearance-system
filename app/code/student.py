from app.utils import *
from app.email_util import *
from flask import Flask, jsonify, Response, request
from flask_restful import Api, Resource, reqparse
from werkzeug.exceptions import BadRequest
import bcrypt   
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from datetime import datetime, timedelta
import random
import io, os
from werkzeug.security import generate_password_hash, check_password_hash


class RegisterStudent(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "surname",
            type=str,
            required=True,
            help="Surname is required"
        )

        self.parser.add_argument(
            "first_name",
            type=str,
            required=True,
            help="First name is required"
        )

        self.parser.add_argument(
            "other_names",
            type=str,
            required=False
        )

        self.parser.add_argument(
            "email",
            type=str,
            required=True,
            help="Email is required"
        )

        self.parser.add_argument(
            "reg_no",
            type=str,
            required=True,
            help="Registration number is required"
        )

        self.parser.add_argument(
            "department",
            type=str,
            required=True,
            help="Department is required"
        )

        self.parser.add_argument(
            "faculty",
            type=str,
            required=True,
            help="Faculty is required"
        )

        self.parser.add_argument(
            "phone_number",
            type=str,
            required=True,
            help="Phone number is required"
        )

        self.parser.add_argument(
            "gender",
            type=str,
            required=True,
            help="Gender is required"
        )

        self.parser.add_argument(
            "admission_year",
            type=int,
            required=True,
            help="Admission year is required"
        )

        self.parser.add_argument(
            "password",
            type=str,
            required=True,
            help="Password is required"
        )

    def post(self):

        # ---------- Parse request ----------
        args = self.parser.parse_args()

        # ---------- Clean input ----------
        surname = args["surname"].strip().title()

        first_name = args["first_name"].strip().title()

        other_names = (
            args["other_names"].strip().title()
            if args["other_names"]
            else ""
        )

        email = args["email"].strip().lower()

        reg_no = args["reg_no"].strip().upper()

        department = args["department"].strip().title()

        faculty = args["faculty"].strip().title()

        phone_number = args["phone_number"].strip()

        gender = args["gender"].strip().lower()

        admission_year = args["admission_year"]

        password = args["password"].strip()

        # ---------- Validate gender ----------
        if gender not in ["male", "female"]:
            return {
                "status": "error",
                "message": "Gender must be either 'male' or 'female'"
            }, 400

        # ---------- Validate admission year ----------
        current_year = datetime.now().year

        if admission_year > current_year:
            return {
                "status": "error",
                "message": "Admission year cannot be in the future"
            }, 400

        # ---------- Calculate study duration ----------
        study_duration = current_year - admission_year

        # ---------- Determine student status ----------
        if study_duration > 6:
            student_status = "external"
        else:
            student_status = "regular"

        # ---------- Validate password ----------
        if len(password) < 6:
            return {
                "status": "error",
                "message": "Password must be at least 6 characters long"
            }, 400

        # ---------- Check existing student ----------
        existing_student = students.find_one({
            "$or": [
                {"reg_no": reg_no},
                {"phone_number": phone_number},
                {"email": email}
            ]
        })

        if existing_student:
            return {
                "status": "error",
                "message": (
                    "Student with this registration number, "
                    "phone number, or email already exists"
                )
            }, 409

        # ---------- Hash password ----------
        hashed_password = generate_password_hash(password)

        # ---------- Create student record ----------
        new_student = {
            "surname": surname,
            "first_name": first_name,
            "other_names": other_names,

            "email": email,

            "reg_no": reg_no,

            "department": department,
            "faculty": faculty,

            "phone_number": phone_number,

            "gender": gender,

            # Academic information
            "admission_year": admission_year,
            "study_duration": study_duration,
            "student_status": student_status,

            # System-controlled role
            "role": "student",

            # Authentication
            "password": hashed_password,

            # Account information
            "account_status": "active",

            # Account creation date
            "created_at": datetime.utcnow()
        }

        # ---------- Insert into MongoDB ----------
        result = students.insert_one(new_student)

        # ---------- Send Registration Email ----------
        email_sent = EmailSender.send_student_registration_email(
            receiver_email=email,
            student_name=f"{surname} {first_name}",
            reg_no=reg_no,
            password=password
        )

        # ---------- Response ----------
        return {
            "status": "success",
            "message": "Student registered successfully",
            "data": {
                "id": str(result.inserted_id),

                "surname": surname,
                "first_name": first_name,
                "other_names": other_names,

                "email": email,

                "reg_no": reg_no,

                "department": department,
                "faculty": faculty,

                "phone_number": phone_number,

                "gender": gender,

                "admission_year": admission_year,
                "study_duration": study_duration,
                "student_status": student_status,

                "role": "student",
                "account_status": "active",

                "email_sent": email_sent
            }
        }, 201


# ---------- ADD RESOURCE ----------
api.add_resource(
    RegisterStudent,
    "/api/v1/clearance/register/student"
)


class LoginStudent(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "reg_no",
            type=str,
            required=True,
            help="Registration number is required"
        )

        self.parser.add_argument(
            "password",
            type=str,
            required=True,
            help="Password is required"
        )

    def post(self):

        # ---------- Parse request ----------
        args = self.parser.parse_args()

        # ---------- Clean input ----------
        reg_no = args["reg_no"].strip().upper()
        password = args["password"].strip()

        # ---------- Find student ----------
        student = students.find_one({
            "reg_no": reg_no
        })

        # ---------- Check if student exists ----------
        if not student:
            return {
                "status": "error",
                "message": "Invalid registration number or password"
            }, 401

        # ---------- Check account status ----------
        if student.get("account_status") != "active":
            return {
                "status": "error",
                "message": "Your account is not active. Please contact the administrator"
            }, 403

        # ---------- Check password ----------
        password_is_valid = check_password_hash(
            student["password"],
            password
        )

        if not password_is_valid:
            return {
                "status": "error",
                "message": "Invalid registration number or password"
            }, 401

        # ---------- Successful login ----------
        return {
            "status": "success",
            "message": "Login successful",
            "data": {
                "id": str(student["_id"]),

                "surname": student.get("surname"),
                "first_name": student.get("first_name"),
                "other_names": student.get("other_names", ""),

                "email": student.get("email"),

                "reg_no": student.get("reg_no"),

                "department": student.get("department"),
                "faculty": student.get("faculty"),

                "phone_number": student.get("phone_number"),

                "gender": student.get("gender"),

                "admission_year": student.get("admission_year"),
                "study_duration": student.get("study_duration"),
                "student_status": student.get("student_status"),

                "role": student.get("role"),
                "account_status": student.get("account_status")
            }
        }, 200


# ---------- ADD RESOURCE ----------
api.add_resource(
    LoginStudent,
    "/api/v1/clearance/login/student"
)



class ForgotPassword(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "reg_no",
            type=str,
            required=True,
            help="Registration number is required"
        )

    def post(self):

        args = self.parser.parse_args()

        reg_no = args["reg_no"].strip().upper()

        # Find student
        student = students.find_one({
            "reg_no": reg_no
        })

        if not student:
            return {
                "status": "error",
                "message": "Student with this registration number does not exist"
            }, 404

        # Check account status
        if student.get("account_status") != "active":
            return {
                "status": "error",
                "message": "Your account is not active. Please contact the administrator"
            }, 403

        # Check if student has an email
        if not student.get("email"):
            return {
                "status": "error",
                "message": "No email address is associated with this account"
            }, 400

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # OTP expires after 10 minutes
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)

        # Save OTP and expiry time
        students.update_one(
            {"_id": student["_id"]},
            {
                "$set": {
                    "password_reset_otp": otp,
                    "password_reset_otp_expiry": otp_expiry
                }
            }
        )

        # Send OTP to student's email
        email_sent = EmailSender.send_student_forgot_password_email(
            receiver_email=student["email"],
            student_name=f'{student["surname"]} {student["first_name"]}',
            otp=otp
        )

        if not email_sent:
            return {
                "status": "error",
                "message": "Failed to send password reset email. Please try again"
            }, 500

        return {
            "status": "success",
            "message": "Password reset OTP has been sent to your email",
            "data": {
                "email": student["email"]
            }
        }, 200


api.add_resource(
    ForgotPassword,
    "/api/v1/clearance/forgot-password/student"
)



# ==========================================================
# OTP RESET STUDENT PASSWORD
# ==========================================================

class OTPResetStudentPassword(Resource):

    def __init__(self):

        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "reg_no",
            type=str,
            required=True,
            help="Registration number is required"
        )

        self.parser.add_argument(
            "otp",
            type=str,
            required=True,
            help="OTP is required"
        )

        self.parser.add_argument(
            "new_password",
            type=str,
            required=True,
            help="New password is required"
        )


    def post(self):

        # ==================================================
        # Parse request
        # ==================================================

        args = self.parser.parse_args()

        reg_no = args["reg_no"].strip().upper()
        otp = args["otp"].strip()
        new_password = args["new_password"].strip()


        # ==================================================
        # Validate new password
        # ==================================================

        if len(new_password) < 6:

            return {
                "status": "error",
                "message": "Password must be at least 6 characters long"
            }, 400


        # ==================================================
        # Find student
        # ==================================================

        student = students.find_one({
            "reg_no": reg_no
        })


        if not student:

            return {
                "status": "error",
                "message": "Student with this registration number does not exist"
            }, 404


        # ==================================================
        # Check account status
        # ==================================================

        if student.get("account_status") != "active":

            return {
                "status": "error",
                "message": (
                    "Your account is not active. "
                    "Please contact the administrator"
                )
            }, 403


        # ==================================================
        # Check student email
        # ==================================================

        if not student.get("email"):

            return {
                "status": "error",
                "message": (
                    "No email address is associated "
                    "with this account"
                )
            }, 400


        # ==================================================
        # Get previously sent OTP
        # ==================================================

        stored_otp = student.get(
            "password_reset_otp"
        )


        if not stored_otp:

            return {
                "status": "error",
                "message": (
                    "No password reset OTP was found. "
                    "Please request an OTP first"
                )
            }, 400


        # ==================================================
        # Verify OTP
        # ==================================================

        if otp != stored_otp:

            return {
                "status": "error",
                "message": "Invalid OTP"
            }, 400


        # ==================================================
        # Get OTP expiry
        # ==================================================

        otp_expiry = student.get(
            "password_reset_otp_expiry"
        )


        if not otp_expiry:

            return {
                "status": "error",
                "message": (
                    "OTP expiry information was not found. "
                    "Please request a new OTP"
                )
            }, 400


        # ==================================================
        # Check OTP expiry
        # ==================================================

        if datetime.utcnow() > otp_expiry:

            return {
                "status": "error",
                "message": (
                    "OTP has expired. "
                    "Please request a new OTP"
                )
            }, 400


        # ==================================================
        # Hash new password
        # ==================================================

        hashed_password = generate_password_hash(
            new_password
        )


        # ==================================================
        # Change password
        # ==================================================

        update_result = students.update_one(
            {
                "_id": student["_id"]
            },
            {
                "$set": {
                    "password": hashed_password,
                    "updated_at": datetime.utcnow()
                },

                "$unset": {
                    "password_reset_otp": "",
                    "password_reset_otp_expiry": ""
                }
            }
        )


        # ==================================================
        # Check if password was actually updated
        # ==================================================

        if update_result.modified_count == 0:

            return {
                "status": "error",
                "message": (
                    "Password could not be changed. "
                    "Please try again"
                )
            }, 500


        # ==================================================
        # Send password changed notification
        # ==================================================

        email_sent = EmailSender.send_student_password_changed_email(
            receiver_email=student["email"],
            student_name=(
                f'{student["surname"]} '
                f'{student["first_name"]}'
            )
        )


        # ==================================================
        # Successful response
        # ==================================================

        return {
            "status": "success",
            "message": (
                "Your password has been changed successfully. "
                "You can now login with your new password"
            ),
            "data": {
                "email": student["email"],
                "email_sent": email_sent
            }
        }, 200


# ==========================================================
# ROUTE
# ==========================================================

api.add_resource(
    OTPResetStudentPassword,
    "/api/v1/clearance/otp-reset-password/student"
)



# ==========================================================
# CHANGE STUDENT PASSWORD
# ==========================================================

class ResetStudentPassword(Resource):

    def __init__(self):

        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "reg_no",
            type=str,
            required=True,
            help="Registration number is required"
        )

        self.parser.add_argument(
            "current_password",
            type=str,
            required=True,
            help="Current password is required"
        )

        self.parser.add_argument(
            "new_password",
            type=str,
            required=True,
            help="New password is required"
        )


    def post(self):

        # ==================================================
        # Parse request
        # ==================================================

        args = self.parser.parse_args()

        reg_no = args["reg_no"].strip().upper()
        current_password = args["current_password"].strip()
        new_password = args["new_password"].strip()


        # ==================================================
        # Validate new password
        # ==================================================

        if len(new_password) < 6:

            return {
                "status": "error",
                "message": "Password must be at least 6 characters long"
            }, 400


        # ==================================================
        # Make sure new password is different
        # ==================================================

        if current_password == new_password:

            return {
                "status": "error",
                "message": (
                    "New password must be different "
                    "from your current password"
                )
            }, 400


        # ==================================================
        # Find student
        # ==================================================

        student = students.find_one({
            "reg_no": reg_no
        })


        if not student:

            return {
                "status": "error",
                "message": (
                    "Student with this registration number "
                    "does not exist"
                )
            }, 404


        # ==================================================
        # Check account status
        # ==================================================

        if student.get("account_status") != "active":

            return {
                "status": "error",
                "message": (
                    "Your account is not active. "
                    "Please contact the administrator"
                )
            }, 403


        # ==================================================
        # Check email
        # ==================================================

        if not student.get("email"):

            return {
                "status": "error",
                "message": (
                    "No email address is associated "
                    "with this account"
                )
            }, 400


        # ==================================================
        # Verify current password
        # ==================================================

        password_is_valid = check_password_hash(
            student["password"],
            current_password
        )


        if not password_is_valid:

            return {
                "status": "error",
                "message": "Current password is incorrect"
            }, 401


        # ==================================================
        # Hash new password
        # ==================================================

        hashed_password = generate_password_hash(
            new_password
        )


        # ==================================================
        # Update password
        # ==================================================

        update_result = students.update_one(
            {
                "_id": student["_id"]
            },
            {
                "$set": {
                    "password": hashed_password,
                    "updated_at": datetime.utcnow()
                }
            }
        )


        # ==================================================
        # Check update
        # ==================================================

        if update_result.modified_count == 0:

            return {
                "status": "error",
                "message": (
                    "Password could not be changed. "
                    "Please try again"
                )
            }, 500


        # ==================================================
        # Send password changed notification
        # ==================================================

        email_sent = EmailSender.send_student_password_changed_email(
            receiver_email=student["email"],
            student_name=(
                f'{student["surname"]} '
                f'{student["first_name"]}'
            )
        )


        # ==================================================
        # Successful response
        # ==================================================

        return {
            "status": "success",
            "message": (
                "Your password has been changed successfully. "
                "You can now login with your new password"
            ),
            "data": {
                "email": student["email"],
                "email_sent": email_sent
            }
        }, 200


# ==========================================================
# ROUTE
# ==========================================================

api.add_resource(
    ResetStudentPassword,
    "/api/v1/clearance/reset-password/student"
)