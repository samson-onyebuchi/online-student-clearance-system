from app.utils import *
from app.email_util import *
from flask import Flask, jsonify, Response, request, send_file
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
import mimetypes
import uuid


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


# ==========================================================
# CREATE STUDENT CLEARANCE
# Creates a clearance record for an existing student and
# initializes all eight official clearance stages in order.
# ==========================================================

class CreateClearance(Resource):

    def __init__(self):

        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "reg_no",
            type=str,
            required=True,
            help="Registration number is required"
        )

    def post(self):

        try:

            # ==================================================
            # 1. GET REGISTRATION NUMBER
            # ==================================================

            args = self.parser.parse_args()

            reg_no = args["reg_no"]

            if not reg_no or not str(reg_no).strip():

                return {
                    "status": "error",
                    "message": "Registration number is required."
                }, 400

            reg_no = str(reg_no).strip().upper()

            # ==================================================
            # 2. CHECK THAT STUDENT EXISTS
            # ==================================================

            student = students.find_one({
                "reg_no": reg_no
            })

            if student is None:

                return {
                    "status": "error",
                    "message": (
                        f"Student with registration number "
                        f"'{reg_no}' does not exist in the "
                        "student records."
                    )
                }, 404

            # ==================================================
            # 3. CHECK WHETHER CLEARANCE ALREADY EXISTS
            # ==================================================

            clearance = clearances.find_one({
                "reg_no": reg_no
            })

            if clearance is not None:

                return {
                    "status": "error",
                    "message": (
                        f"Clearance has already been started "
                        f"for student '{reg_no}'."
                    ),
                    "data": {
                        "clearance_id": str(clearance["_id"]),
                        "reg_no": clearance.get("reg_no"),
                        "current_stage": clearance.get(
                            "current_stage"
                        ),
                        "status": clearance.get("status"),
                        "stage_status": clearance.get(
                            "stage_status"
                        ),
                        "feedback": clearance.get(
                            "feedback",
                            ""
                        ),
                        "created_at": (
                            clearance.get("created_at").isoformat()
                            if clearance.get("created_at")
                            else None
                        ),
                        "updated_at": (
                            clearance.get("updated_at").isoformat()
                            if clearance.get("updated_at")
                            else None
                        )
                    }
                }, 409

            # ==================================================
            # 4. DEFINE OFFICIAL CLEARANCE STAGES
            # ==================================================

            stage_names = [
                "department",
                "finance",
                "library",
                "alumni",
                "student_affairs",
                "health",
                "security",
                "audit"
            ]

            # ==================================================
            # 5. INITIALIZE EACH STAGE
            # ==================================================

            stages = {}

            for stage_name in stage_names:

                stages[stage_name] = {
                    "status": "pending",
                    "feedback": "",
                    "documents": [],
                    "approved_by": None,
                    "approved_at": None,
                    "rejected_by": None,
                    "rejected_at": None
                }

            # ==================================================
            # 6. PREPARE NEW CLEARANCE RECORD
            # ==================================================

            current_time = datetime.utcnow()

            new_clearance = {
                "reg_no": reg_no,

                # Clearance starts at the Department stage.
                "current_stage": "department",

                # Overall clearance status.
                "status": "in_progress",

                # Status of the current stage.
                "stage_status": "pending",

                # Feedback for the current stage.
                "feedback": "",

                # All eight official stages.
                "stages": stages,

                # Timestamps.
                "created_at": current_time,
                "updated_at": current_time
            }

            # ==================================================
            # 7. SAVE CLEARANCE RECORD
            # ==================================================

            result = clearances.insert_one(
                new_clearance
            )

            if not result.inserted_id:

                return {
                    "status": "error",
                    "message": (
                        f"Student '{reg_no}' exists, but the "
                        "clearance record could not be created."
                    )
                }, 500

            # ==================================================
            # 8. RETURN SUCCESS RESPONSE
            # ==================================================

            return {
                "status": "success",
                "message": (
                    f"Clearance started successfully for student "
                    f"'{reg_no}'. The first stage is Department."
                ),
                "data": {
                    "clearance_id": str(result.inserted_id),
                    "reg_no": reg_no,
                    "current_stage": "department",
                    "status": "in_progress",
                    "stage_status": "pending",
                    "feedback": "",
                    "stages": {
                        stage_name: {
                            "status": "pending",
                            "documents": []
                        }
                        for stage_name in stage_names
                    },
                    "created_at": current_time.isoformat(),
                    "updated_at": current_time.isoformat()
                }
            }, 201

        # ==================================================
        # 9. HANDLE UNEXPECTED ERRORS
        # ==================================================

        except Exception as e:

            print(
                "CREATE CLEARANCE ERROR:",
                str(e)
            )

            return {
                "status": "error",
                "message": (
                    "An unexpected error occurred while "
                    "starting the student's clearance. "
                    "Check the server terminal for details."
                )
            }, 500


# ==========================================================
# ADD RESOURCE
# ==========================================================

api.add_resource(
    CreateClearance,
    "/api/v1/clearance/create"
)


# ==========================================================
# VIEW STUDENT CLEARANCE
# ==========================================================

class ViewClearance(Resource):

    def __init__(self):

        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "reg_no",
            type=str,
            required=True,
            help="Registration number is required"
        )


    def get(self):

        try:

            # ==================================================
            # 1. GET REGISTRATION NUMBER
            # ==================================================

            args = self.parser.parse_args()

            reg_no = args["reg_no"]

            if not reg_no:

                return {
                    "status": "error",
                    "message": "Registration number is required"
                }, 400

            reg_no = str(reg_no).strip().upper()


            # ==================================================
            # 2. CHECK STUDENT COLLECTION
            # ==================================================

            student = students.find_one(
                {
                    "reg_no": reg_no
                }
            )


            # ==================================================
            # 3. STUDENT DOES NOT EXIST
            # ==================================================

            if student is None:

                return {
                    "status": "error",
                    "message": (
                        f"Student with registration number "
                        f"'{reg_no}' does not exist in the "
                        f"student records."
                    )
                }, 404


            # ==================================================
            # 4. CHECK CLEARANCE COLLECTION
            # ==================================================

            clearance = clearances.find_one(
                {
                    "reg_no": reg_no
                }
            )


            # ==================================================
            # 5. CLEARANCE DOES NOT EXIST
            # ==================================================

            if clearance is None:

                return {
                    "status": "error",
                    "message": (
                        f"Student '{reg_no}' has not started "
                        f"the clearance process."
                    )
                }, 404


            # ==================================================
            # 6. RETURN CLEARANCE INFORMATION
            # ==================================================

            return {
                "status": "success",
                "message": "Clearance retrieved successfully.",
                "data": {

                    "clearance_id": str(
                        clearance["_id"]
                    ),

                    "reg_no": clearance.get(
                        "reg_no"
                    ),

                    "current_stage": clearance.get(
                        "current_stage"
                    ),

                    "status": clearance.get(
                        "status"
                    ),

                    "stage_status": clearance.get(
                        "stage_status"
                    ),

                    "feedback": clearance.get(
                        "feedback",
                        ""
                    ),

                    "created_at": (
                        clearance.get("created_at").isoformat()
                        if clearance.get("created_at")
                        else None
                    ),

                    "updated_at": (
                        clearance.get("updated_at").isoformat()
                        if clearance.get("updated_at")
                        else None
                    )
                }
            }, 200


        # ==================================================
        # 7. UNEXPECTED ERROR
        # ==================================================

        except Exception as e:

            print(
                "VIEW CLEARANCE ERROR:",
                str(e)
            )

            return {
                "status": "error",
                "message": (
                    "An unexpected error occurred while "
                    "retrieving the student's clearance."
                )
            }, 500


# ==========================================================
# ADD RESOURCE
# ==========================================================

api.add_resource(
    ViewClearance,
    "/api/v1/clearance/view"
)





# ==========================================================
# UPLOAD CLEARANCE DOCUMENT
# Allows students to upload PDF and Word documents under
# their current clearance stage and resubmit rejected documents.
# Generates a unique server filename for every uploaded file.
# Sets the stage to under_review after successful submission.
# Prevents duplicate document submissions and stage skipping.
# ==========================================================

class UploadDocument(Resource):

    def post(self):

        file_path = None

        try:
            # ==================================================
            # 1. CHECK REQUEST TYPE
            # ==================================================

            if not request.content_type:
                return {
                    "status": "error",
                    "message": "No request content type was received."
                }, 400

            if not request.content_type.startswith("multipart/form-data"):
                return {
                    "status": "error",
                    "message": (
                        "Invalid request format. This endpoint requires "
                        "multipart/form-data."
                    )
                }, 400

            # ==================================================
            # 2. GET REGISTRATION NUMBER
            # ==================================================

            reg_no = request.form.get("reg_no")

            if reg_no is None or not str(reg_no).strip():
                return {
                    "status": "error",
                    "message": "Student registration number is required."
                }, 400

            reg_no = str(reg_no).strip().upper()

            # Preserve reg_no in MongoDB; sanitize the folder name only.
            safe_reg_no = reg_no.replace("/", "_").replace("\\", "_")

            # ==================================================
            # 3. GET AND VALIDATE STAGE
            # ==================================================

            stage = request.form.get("stage")

            if stage is None or not str(stage).strip():
                return {
                    "status": "error",
                    "message": "Clearance stage is required."
                }, 400

            stage = str(stage).strip().lower()

            allowed_stages = [
                "department",
                "finance",
                "library",
                "alumni",
                "student_affairs",
                "health",
                "security",
                "audit"
            ]

            if stage not in allowed_stages:
                return {
                    "status": "error",
                    "message": (
                        f"Invalid clearance stage '{stage}'. "
                        "Allowed stages are: department, finance, library, "
                        "alumni, student_affairs, health, security, and audit."
                    )
                }, 400

            # ==================================================
            # 4. GET AND VALIDATE DOCUMENT NAME
            # ==================================================

            document_name = request.form.get("document_name")

            if document_name is None or not str(document_name).strip():
                return {
                    "status": "error",
                    "message": (
                        "Document name is required. "
                        "Example: School Fees Receipt."
                    )
                }, 400

            document_name = str(document_name).strip()

            invalid_characters = '<>:"/\\|?*'

            if (
                any(char in document_name for char in invalid_characters)
                or "\x00" in document_name
                or document_name in {".", ".."}
                or document_name.endswith(".")
            ):
                return {
                    "status": "error",
                    "message": (
                        "The document name contains invalid characters. "
                        "Use a human-readable name without file paths or "
                        "characters such as /, \\, :, *, or ?."
                    )
                }, 400

            # ==================================================
            # 5. CHECK UPLOADED FILE
            # ==================================================

            if "document" not in request.files:
                return {
                    "status": "error",
                    "message": (
                        "No document file was received. Attach a PDF or "
                        "Word document using the 'document' field."
                    )
                }, 400

            file = request.files.get("document")

            if file is None or not file.filename:
                return {
                    "status": "error",
                    "message": (
                        "No document was selected. Please select a "
                        "PDF, DOC, or DOCX file."
                    )
                }, 400

            original_filename = os.path.basename(file.filename.strip())

            if "." not in original_filename:
                return {
                    "status": "error",
                    "message": (
                        "The uploaded file has no valid extension. "
                        "Only PDF, DOC, and DOCX files are allowed."
                    )
                }, 400

            file_extension = original_filename.rsplit(".", 1)[1].lower()
            allowed_extensions = {"pdf", "doc", "docx"}

            if file_extension not in allowed_extensions:
                return {
                    "status": "error",
                    "message": (
                        f"The file type '.{file_extension}' is not allowed. "
                        "Only PDF (.pdf), Word (.doc), and "
                        "Word (.docx) files are allowed."
                    )
                }, 400

            # ==================================================
            # 6. CHECK STUDENT
            # ==================================================

            student = students.find_one({
                "reg_no": reg_no
            })

            if student is None:
                return {
                    "status": "error",
                    "message": (
                        f"Student '{reg_no}' does not exist in the "
                        "student records. Register the student first."
                    )
                }, 404

            # ==================================================
            # 7. CHECK CLEARANCE RECORD
            # ==================================================

            clearance = clearances.find_one({
                "reg_no": reg_no
            })

            if clearance is None:
                return {
                    "status": "error",
                    "message": (
                        f"Student '{reg_no}' has not started clearance. "
                        "Create a clearance record before uploading documents."
                    )
                }, 404

            # ==================================================
            # 8. CHECK OVERALL CLEARANCE STATUS
            # ==================================================

            clearance_status = str(
                clearance.get("status", "")
            ).strip().lower()

            if clearance_status != "in_progress":
                return {
                    "status": "error",
                    "message": (
                        "Documents cannot be uploaded because the student's "
                        f"clearance status is '{clearance_status}'. "
                        "Uploads are allowed only while clearance is "
                        "in progress."
                    )
                }, 400

            # ==================================================
            # 9. CHECK CURRENT CLEARANCE STAGE
            # ==================================================

            current_stage = str(
                clearance.get("current_stage", "")
            ).strip().lower()

            if not current_stage:
                return {
                    "status": "error",
                    "message": (
                        "The clearance record has no current stage. "
                        "Please check the clearance record."
                    )
                }, 400

            if current_stage not in allowed_stages:
                return {
                    "status": "error",
                    "message": (
                        f"The current stage '{current_stage}' is invalid. "
                        "Update the clearance record to use an official "
                        "clearance stage."
                    )
                }, 400

            # ==================================================
            # 10. PREVENT SKIPPING CLEARANCE STAGES
            # ==================================================

            if stage != current_stage:
                current_index = allowed_stages.index(current_stage)
                requested_index = allowed_stages.index(stage)

                if requested_index > current_index:
                    return {
                        "status": "error",
                        "message": (
                            f"You cannot upload documents for the '{stage}' "
                            f"stage yet. Your current stage is "
                            f"'{current_stage}'. Obtain staff approval "
                            "for the current stage before proceeding."
                        )
                    }, 403

                return {
                    "status": "error",
                    "message": (
                        f"The requested stage is '{stage}', but your current "
                        f"stage is '{current_stage}'. Upload documents only "
                        "under your current stage."
                    )
                }, 400

            # ==================================================
            # 11. GET CURRENT STAGE INFORMATION
            # ==================================================

            stages_data = clearance.get("stages", {})
            current_stage_data = stages_data.get(current_stage, {})

            stage_status = str(
                current_stage_data.get("status", "pending")
            ).strip().lower()

            if stage_status in {"approved", "completed"}:
                return {
                    "status": "error",
                    "message": (
                        f"The '{current_stage}' stage has already been "
                        "approved. Additional uploads to this stage "
                        "are not allowed."
                    )
                }, 409

            existing_documents = current_stage_data.get("documents", [])

            # ==================================================
            # 12. FIND DOCUMENT WITH THE SAME NAME
            # ==================================================

            matching_document = None

            for existing_document in existing_documents:
                existing_name = str(
                    existing_document.get("document_name", "")
                ).strip()

                if existing_name.lower() == document_name.lower():
                    matching_document = existing_document
                    break

            # ==================================================
            # 13. DETERMINE WHETHER THIS IS A RESUBMISSION
            # ==================================================

            document_status = ""

            if matching_document is not None:
                document_status = str(
                    matching_document.get(
                        "status",
                        matching_document.get("review_status", "")
                    )
                ).strip().lower()

            is_rejected_document = (
                matching_document is not None
                and (
                    document_status == "rejected"
                    or stage_status == "rejected"
                )
            )

            if (
                matching_document is not None
                and not is_rejected_document
            ):
                return {
                    "status": "error",
                    "message": (
                        f"The document '{document_name}' has already been "
                        f"uploaded under the '{current_stage}' stage and "
                        "has not been rejected. Duplicate uploads are "
                        "not allowed."
                    )
                }, 409

            # ==================================================
            # 14. CREATE UPLOAD DIRECTORY
            # ==================================================

            upload_folder = os.path.join(
                "uploads",
                "clearance_documents",
                safe_reg_no,
                current_stage
            )

            os.makedirs(upload_folder, exist_ok=True)

            # ==================================================
            # 15. GENERATE A UNIQUE SERVER FILENAME
            # Every upload receives a unique filename, even when
            # an earlier file with the same document name exists.
            # The human-readable document_name in MongoDB is
            # kept unchanged.
            # ==================================================

            unique_id = uuid.uuid4().hex

            if is_rejected_document:
                safe_filename = (
                    f"{document_name}_resubmitted_{unique_id}."
                    f"{file_extension}"
                )
            else:
                safe_filename = (
                    f"{document_name}_{unique_id}.{file_extension}"
                )

            file_path = os.path.join(
                upload_folder,
                safe_filename
            )

            # UUID makes collisions extremely unlikely. Check anyway.
            if os.path.exists(file_path):
                return {
                    "status": "error",
                    "message": (
                        "A rare server filename conflict occurred. "
                        "Please retry the upload."
                    )
                }, 409

            # ==================================================
            # 16. SAVE FILE TO SERVER
            # ==================================================

            try:
                file.save(file_path)

            except Exception as file_error:
                print(
                    "FILE SAVE ERROR:",
                    type(file_error).__name__,
                    str(file_error)
                )

                return {
                    "status": "error",
                    "message": (
                        "The document could not be saved to the server. "
                        "Check the server's file permissions and storage."
                    )
                }, 500

            # ==================================================
            # 17. CREATE DOCUMENT DATABASE RECORD
            # ==================================================

            current_time = datetime.utcnow()

            document_record = {
                "document_name": document_name,
                "original_filename": original_filename,
                "file_path": file_path,
                "file_type": file_extension,
                "uploaded_at": current_time,
                "status": "under_review"
            }

            # ==================================================
            # 18. SAVE DOCUMENT AND UPDATE STAGE STATUS
            # ==================================================

            try:
                if is_rejected_document:

                    updated_documents = []
                    replaced = False

                    for existing_document in existing_documents:
                        existing_name = str(
                            existing_document.get("document_name", "")
                        ).strip()

                        if (
                            existing_name.lower() == document_name.lower()
                            and not replaced
                        ):
                            updated_documents.append(document_record)
                            replaced = True
                        else:
                            updated_documents.append(existing_document)

                    if not replaced:
                        if os.path.exists(file_path):
                            os.remove(file_path)

                        file_path = None

                        return {
                            "status": "error",
                            "message": (
                                "The rejected document record could not be "
                                "located for replacement. Refresh the "
                                "clearance record and try again."
                            )
                        }, 409

                    update_result = clearances.update_one(
                        {
                            "_id": clearance["_id"],
                            "current_stage": current_stage,
                            f"stages.{current_stage}.status": "rejected"
                        },
                        {
                            "$set": {
                                f"stages.{current_stage}.documents":
                                    updated_documents,
                                f"stages.{current_stage}.status":
                                    "under_review",
                                f"stages.{current_stage}.resubmitted_at":
                                    current_time,
                                "updated_at": current_time
                            }
                        }
                    )

                else:
                    set_fields = {
                        "updated_at": current_time
                    }

                    if stage_status in {"pending", "rejected"}:
                        set_fields[
                            f"stages.{current_stage}.status"
                        ] = "under_review"

                    update_result = clearances.update_one(
                        {
                            "_id": clearance["_id"],
                            "current_stage": current_stage,
                            f"stages.{current_stage}.status": stage_status
                        },
                        {
                            "$push": {
                                f"stages.{current_stage}.documents":
                                    document_record
                            },
                            "$set": set_fields
                        }
                    )

            except Exception as database_error:
                print(
                    "DATABASE UPDATE ERROR:",
                    type(database_error).__name__,
                    str(database_error)
                )

                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as cleanup_error:
                        print(
                            "FILE CLEANUP ERROR:",
                            str(cleanup_error)
                        )

                file_path = None

                return {
                    "status": "error",
                    "message": (
                        "The document could not be recorded in the "
                        "clearance database. Check the server terminal "
                        "for technical details."
                    )
                }, 500

            # ==================================================
            # 19. VERIFY DATABASE UPDATE
            # ==================================================

            if update_result.modified_count != 1:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as cleanup_error:
                        print(
                            "FILE CLEANUP ERROR:",
                            str(cleanup_error)
                        )

                file_path = None

                return {
                    "status": "error",
                    "message": (
                        "The document was saved to the server, but the "
                        "clearance record was not updated. The stage may "
                        "have changed during upload. Refresh the record "
                        "and try again."
                    )
                }, 409

            # ==================================================
            # 20. RETURN SUCCESS RESPONSE
            # ==================================================

            if is_rejected_document or stage_status == "rejected":
                success_message = (
                    f"The document '{document_name}' has been uploaded "
                    f"again under the '{current_stage}' stage. The stage "
                    "status is now 'under_review' and staff can review "
                    "the resubmitted documents."
                )
            else:
                success_message = (
                    f"The document '{document_name}' was uploaded "
                    f"successfully under the '{current_stage}' stage. "
                    "The stage status is now 'under_review' for staff review."
                )

            return {
                "status": "success",
                "message": success_message,
                "data": {
                    "reg_no": reg_no,
                    "stage": current_stage,
                    "stage_status": "under_review",
                    "document_name": document_name,
                    "original_filename": original_filename,
                    "file_type": file_extension,
                    "file_path": file_path,
                    "resubmission": (
                        is_rejected_document
                        or stage_status == "rejected"
                    ),
                    "uploaded_at": current_time.isoformat()
                }
            }, 201

        # ======================================================
        # 21. HANDLE UNEXPECTED ERRORS
        # ======================================================

        except Exception as e:
            print(
                f"UPLOAD DOCUMENT ERROR: {type(e).__name__}: {e}"
            )

            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as cleanup_error:
                    print(
                        "FILE CLEANUP ERROR:",
                        str(cleanup_error)
                    )

            return {
                "status": "error",
                "message": (
                    "An unexpected error occurred while uploading the "
                    "document. Check the server terminal for technical details."
                )
            }, 500


# ==========================================================
# REGISTER UPLOAD DOCUMENT ENDPOINT
# Register this resource only once.
# ==========================================================

api.add_resource(
    UploadDocument,
    "/api/v1/clearance/upload-document"
)



# This endpoint retrieves all clearance documents uploaded by a student using the registration number from the GET query parameters.

# ==========================================================
# VIEW UPLOADED CLEARANCE DOCUMENTS
# ==========================================================

class ViewUploadedDocuments(Resource):

    def get(self):

        try:

            # ==================================================
            # 1. GET REGISTRATION NUMBER FROM QUERY PARAMETER
            # ==================================================

            reg_no = request.args.get("reg_no")


            # ==================================================
            # 2. CHECK IF REGISTRATION NUMBER WAS PROVIDED
            # ==================================================

            if not reg_no:

                return {
                    "status": "error",
                    "message": (
                        "Registration number is required. "
                        "Please provide 'reg_no' as a query parameter."
                    )
                }, 400


            # ==================================================
            # 3. CLEAN REGISTRATION NUMBER
            # ==================================================

            reg_no = str(
                reg_no
            ).strip().upper()


            # ==================================================
            # 4. CHECK IF REGISTRATION NUMBER IS STILL VALID
            # ==================================================

            if not reg_no:

                return {
                    "status": "error",
                    "message": (
                        "Registration number cannot be empty."
                    )
                }, 400


            # ==================================================
            # 5. CHECK STUDENT COLLECTION
            # ==================================================

            student = students.find_one(
                {
                    "reg_no": reg_no
                }
            )


            # ==================================================
            # 6. STUDENT DOES NOT EXIST
            # ==================================================

            if student is None:

                return {
                    "status": "error",
                    "message": (
                        f"Student with registration number "
                        f"'{reg_no}' does not exist in the "
                        f"student records."
                    )
                }, 404


            # ==================================================
            # 7. CHECK CLEARANCE COLLECTION
            # ==================================================

            clearance = clearances.find_one(
                {
                    "reg_no": reg_no
                }
            )


            # ==================================================
            # 8. CLEARANCE DOES NOT EXIST
            # ==================================================

            if clearance is None:

                return {
                    "status": "error",
                    "message": (
                        f"Student '{reg_no}' has an account, "
                        f"but has not started the clearance process."
                    )
                }, 404


            # ==================================================
            # 9. GET CLEARANCE STAGES
            # ==================================================

            stages = [
                "finance",
                "department",
                "faculty",
                "library",
                "health",
                "student_affairs",
                "final"
            ]


            # ==================================================
            # 10. PREPARE DOCUMENT RESPONSE
            # ==================================================

            documents_by_stage = {}

            total_documents = 0


            # ==================================================
            # 11. GET DOCUMENTS FROM EACH STAGE
            # ==================================================

            for stage in stages:

                stage_data = clearance.get(
                    "stages",
                    {}
                ).get(
                    stage,
                    {}
                )


                documents = stage_data.get(
                    "documents",
                    []
                )


                # ==================================================
                # 12. PROCESS DOCUMENTS IF THEY EXIST
                # ==================================================

                if documents:

                    stage_documents = []


                    for document in documents:

                        uploaded_at = document.get(
                            "uploaded_at"
                        )


                        # ==================================================
                        # 13. CONVERT DATETIME TO JSON-SAFE FORMAT
                        # ==================================================

                        if isinstance(
                            uploaded_at,
                            datetime
                        ):

                            uploaded_at = (
                                uploaded_at.isoformat()
                            )


                        # ==================================================
                        # 14. PREPARE DOCUMENT INFORMATION
                        # ==================================================

                        stage_documents.append(
                            {
                                "document_name":
                                    document.get(
                                        "document_name",
                                        ""
                                    ),

                                "original_filename":
                                    document.get(
                                        "original_filename",
                                        ""
                                    ),

                                "file_type":
                                    document.get(
                                        "file_type",
                                        ""
                                    ),

                                "file_path":
                                    document.get(
                                        "file_path",
                                        ""
                                    ),

                                "uploaded_at":
                                    uploaded_at
                            }
                        )


                    # ==================================================
                    # 15. ADD STAGE DOCUMENTS TO RESPONSE
                    # ==================================================

                    documents_by_stage[
                        stage
                    ] = stage_documents


                    total_documents += len(
                        stage_documents
                    )


            # ==================================================
            # 16. NO DOCUMENTS FOUND
            # ==================================================

            if total_documents == 0:

                return {
                    "status": "success",
                    "message": (
                        f"Student '{reg_no}' has started "
                        f"the clearance process, but no documents "
                        f"have been uploaded yet."
                    ),
                    "data": {

                        "reg_no":
                            reg_no,

                        "total_documents":
                            0,

                        "documents":
                            {}
                    }
                }, 200


            # ==================================================
            # 17. DOCUMENTS FOUND
            # ==================================================

            return {
                "status": "success",
                "message": (
                    f"Uploaded documents retrieved "
                    f"successfully for student '{reg_no}'."
                ),
                "data": {

                    "reg_no":
                        reg_no,

                    "total_documents":
                        total_documents,

                    "documents":
                        documents_by_stage
                }
            }, 200


        # ======================================================
        # 18. UNEXPECTED ERROR
        # ======================================================

        except Exception as e:

            print(
                "VIEW UPLOADED DOCUMENTS ERROR:",
                str(e)
            )

            return {
                "status": "error",
                "message": (
                    "An unexpected error occurred while "
                    "retrieving the student's uploaded "
                    "documents."
                ),
                "error": str(e)
            }, 500


# ==========================================================
# ADD RESOURCE
# ==========================================================

api.add_resource(
    ViewUploadedDocuments,
    "/api/v1/clearance/documents"
)


# ==========================================================
# VIEW / OPEN ACTUAL CLEARANCE DOCUMENT
# Finds a student's document using registration number,
# clearance stage, and document name, then opens the actual
# uploaded file in the browser.
# ==========================================================

class ViewClearanceDocument(Resource):

    def get(self):

        try:

            # ==================================================
            # 1. GET REQUIRED QUERY PARAMETERS
            # ==================================================

            reg_no = request.args.get("reg_no")
            stage = request.args.get("stage")
            document_name = request.args.get("document_name")

            # ==================================================
            # 2. VALIDATE REGISTRATION NUMBER
            # ==================================================

            if reg_no is None:
                return {
                    "status": "error",
                    "message": (
                        "Registration number is required. "
                        "Provide 'reg_no' as a query parameter."
                    )
                }, 400

            reg_no = str(reg_no).strip().upper()

            if not reg_no:
                return {
                    "status": "error",
                    "message": "Registration number cannot be empty."
                }, 400

            # ==================================================
            # 3. VALIDATE CLEARANCE STAGE
            # ==================================================

            if stage is None:
                return {
                    "status": "error",
                    "message": (
                        "Clearance stage is required. "
                        "Provide 'stage' as a query parameter."
                    )
                }, 400

            stage = str(stage).strip().lower()

            if not stage:
                return {
                    "status": "error",
                    "message": "Clearance stage cannot be empty."
                }, 400

            # ==================================================
            # 4. VALIDATE DOCUMENT NAME
            # ==================================================

            if document_name is None:
                return {
                    "status": "error",
                    "message": (
                        "Document name is required. "
                        "Provide 'document_name' as a query parameter."
                    )
                }, 400

            document_name = str(document_name).strip()

            if not document_name:
                return {
                    "status": "error",
                    "message": "Document name cannot be empty."
                }, 400

            # ==================================================
            # 5. VALIDATE OFFICIAL CLEARANCE STAGES
            # ==================================================

            valid_stages = [
                "department",
                "finance",
                "library",
                "alumni",
                "student_affairs",
                "health",
                "security",
                "audit"
            ]

            if stage not in valid_stages:
                return {
                    "status": "error",
                    "message": (
                        f"Invalid clearance stage '{stage}'. "
                        "Valid stages, in order, are: "
                        f"{', '.join(valid_stages)}."
                    )
                }, 400

            # ==================================================
            # 6. CHECK STUDENT
            # ==================================================

            student = students.find_one({
                "reg_no": reg_no
            })

            if student is None:
                return {
                    "status": "error",
                    "message": (
                        f"Student '{reg_no}' does not exist "
                        "in the student records."
                    )
                }, 404

            # ==================================================
            # 7. CHECK CLEARANCE RECORD
            # ==================================================

            clearance = clearances.find_one({
                "reg_no": reg_no
            })

            if clearance is None:
                return {
                    "status": "error",
                    "message": (
                        f"Student '{reg_no}' has an account, "
                        "but has not started the clearance process."
                    )
                }, 404

            # ==================================================
            # 8. GET REQUESTED STAGE
            # ==================================================

            all_stages = clearance.get("stages", {})

            if not isinstance(all_stages, dict):
                return {
                    "status": "error",
                    "message": (
                        "The student's clearance stage data "
                        "has an invalid format."
                    )
                }, 500

            stage_data = all_stages.get(stage)

            # ==================================================
            # 9. CHECK WHETHER STAGE EXISTS
            # ==================================================

            if stage_data is None:
                return {
                    "status": "error",
                    "message": (
                        f"The '{stage}' stage has not been "
                        f"initialized for student '{reg_no}'. "
                        "The clearance record may use an older "
                        "stage structure."
                    )
                }, 404

            # ==================================================
            # 10. GET DOCUMENTS FOR THE STAGE
            # ==================================================

            documents = stage_data.get("documents", [])

            if not isinstance(documents, list):
                return {
                    "status": "error",
                    "message": (
                        f"The document records for stage '{stage}' "
                        "have an invalid format."
                    )
                }, 500

            if not documents:
                return {
                    "status": "error",
                    "message": (
                        f"No documents have been uploaded under "
                        f"the '{stage}' stage for student '{reg_no}'."
                    )
                }, 404

            # ==================================================
            # 11. FIND REQUESTED DOCUMENT
            # ==================================================

            selected_document = None

            for document in documents:

                if not isinstance(document, dict):
                    continue

                stored_name = str(
                    document.get("document_name", "")
                ).strip()

                if stored_name.casefold() == document_name.casefold():
                    selected_document = document
                    break

            # ==================================================
            # 12. CHECK WHETHER DOCUMENT EXISTS
            # ==================================================

            if selected_document is None:
                return {
                    "status": "error",
                    "message": (
                        f"Document '{document_name}' was not found "
                        f"under the '{stage}' stage for student "
                        f"'{reg_no}'."
                    )
                }, 404

            # ==================================================
            # 13. GET STORED FILE PATH
            # ==================================================

            stored_file_path = selected_document.get("file_path")

            if not stored_file_path:
                return {
                    "status": "error",
                    "message": (
                        f"Document '{document_name}' exists in "
                        "the database, but its file path is missing."
                    )
                }, 404

            # ==================================================
            # 14. RESOLVE FILE PATH
            # ==================================================

            # Support paths saved with either Windows or Unix
            # separators. Relative paths are resolved from the
            # application's working directory.

            stored_file_path = str(stored_file_path).strip()

            normalized_path = os.path.normpath(
                stored_file_path.replace("\\", os.sep)
            )

            if os.path.isabs(normalized_path):
                file_path = normalized_path
            else:
                file_path = os.path.join(
                    os.getcwd(),
                    normalized_path
                )

            file_path = os.path.realpath(file_path)

            # ==================================================
            # 15. RESTRICT FILE ACCESS TO UPLOAD DIRECTORY
            # ==================================================

            upload_root = os.path.realpath(
                os.path.join(
                    os.getcwd(),
                    "uploads",
                    "clearance_documents"
                )
            )

            try:
                path_is_allowed = (
                    os.path.commonpath([
                        upload_root,
                        file_path
                    ]) == upload_root
                )
            except ValueError:
                path_is_allowed = False

            if not path_is_allowed:
                return {
                    "status": "error",
                    "message": (
                        "The stored document path is outside the "
                        "permitted clearance document directory."
                    )
                }, 403

            # ==================================================
            # 16. CHECK ACTUAL FILE
            # ==================================================

            if not os.path.isfile(file_path):
                return {
                    "status": "error",
                    "message": (
                        f"Document '{document_name}' is recorded "
                        "in the database, but its actual file "
                        "could not be found on the server. "
                        f"Resolved path: '{file_path}'."
                    )
                }, 404

            # ==================================================
            # 17. GET ORIGINAL FILE NAME
            # ==================================================

            original_filename = selected_document.get(
                "original_filename"
            )

            if not original_filename:
                original_filename = os.path.basename(file_path)

            # Use only the filename, not any stored directory path.
            original_filename = os.path.basename(
                str(original_filename).replace("\\", "/")
            )

            # ==================================================
            # 18. DETERMINE FILE MIME TYPE
            # ==================================================

            mime_type, _ = mimetypes.guess_type(
                original_filename
            )

            if mime_type is None:
                mime_type = "application/octet-stream"

            # ==================================================
            # 19. OPEN ACTUAL DOCUMENT IN BROWSER
            # ==================================================

            return send_file(
                file_path,
                mimetype=mime_type,
                as_attachment=False,
                download_name=original_filename
            )

        # ======================================================
        # 20. HANDLE UNEXPECTED ERRORS
        # ======================================================

        except Exception as e:

            print(
                "VIEW CLEARANCE DOCUMENT ERROR:",
                str(e)
            )

            return {
                "status": "error",
                "message": (
                    "An unexpected error occurred while opening "
                    "the student's document. Check the server "
                    "terminal for technical details."
                )
            }, 500


# ==========================================================
# ADD RESOURCE
# ==========================================================

api.add_resource(
    ViewClearanceDocument,
    "/api/v1/clearance/document/view"
)


# ==========================================================
# DOWNLOAD SPECIFIC CLEARANCE DOCUMENT AS A WORD FILE
# Finds a student's document using registration number,
# clearance stage, and document name, then forces the actual
# DOC or DOCX file to download instead of opening in a browser.
# ==========================================================

class DownloadClearanceDocument(Resource):

    def get(self):

        try:

            # ==================================================
            # 1. GET REQUIRED QUERY PARAMETERS
            # ==================================================

            reg_no = request.args.get("reg_no")
            stage = request.args.get("stage")
            document_name = request.args.get("document_name")

            # ==================================================
            # 2. VALIDATE REGISTRATION NUMBER
            # ==================================================

            if reg_no is None:
                return {
                    "status": "error",
                    "message": (
                        "Registration number is required. "
                        "Provide 'reg_no' as a query parameter."
                    )
                }, 400

            reg_no = str(reg_no).strip().upper()

            if not reg_no:
                return {
                    "status": "error",
                    "message": "Registration number cannot be empty."
                }, 400

            # ==================================================
            # 3. VALIDATE CLEARANCE STAGE
            # ==================================================

            if stage is None:
                return {
                    "status": "error",
                    "message": (
                        "Clearance stage is required. "
                        "Provide 'stage' as a query parameter."
                    )
                }, 400

            stage = str(stage).strip().lower()

            if not stage:
                return {
                    "status": "error",
                    "message": "Clearance stage cannot be empty."
                }, 400

            # ==================================================
            # 4. VALIDATE DOCUMENT NAME
            # ==================================================

            if document_name is None:
                return {
                    "status": "error",
                    "message": (
                        "Document name is required. "
                        "Provide 'document_name' as a query parameter."
                    )
                }, 400

            document_name = str(document_name).strip()

            if not document_name:
                return {
                    "status": "error",
                    "message": "Document name cannot be empty."
                }, 400

            # ==================================================
            # 5. VALIDATE OFFICIAL CLEARANCE STAGES
            # ==================================================

            valid_stages = [
                "department",
                "finance",
                "library",
                "alumni",
                "student_affairs",
                "health",
                "security",
                "audit"
            ]

            if stage not in valid_stages:
                return {
                    "status": "error",
                    "message": (
                        f"Invalid clearance stage '{stage}'. "
                        "Valid stages, in order, are: "
                        f"{', '.join(valid_stages)}."
                    )
                }, 400

            # ==================================================
            # 6. CHECK STUDENT
            # ==================================================

            student = students.find_one({
                "reg_no": reg_no
            })

            if student is None:
                return {
                    "status": "error",
                    "message": (
                        f"Student '{reg_no}' does not exist "
                        "in the student records."
                    )
                }, 404

            # ==================================================
            # 7. CHECK CLEARANCE RECORD
            # ==================================================

            clearance = clearances.find_one({
                "reg_no": reg_no
            })

            if clearance is None:
                return {
                    "status": "error",
                    "message": (
                        f"Student '{reg_no}' has an account, "
                        "but has not started the clearance process."
                    )
                }, 404

            # ==================================================
            # 8. GET REQUESTED STAGE
            # ==================================================

            all_stages = clearance.get("stages", {})

            if not isinstance(all_stages, dict):
                return {
                    "status": "error",
                    "message": (
                        "The student's clearance stage data "
                        "has an invalid format."
                    )
                }, 500

            stage_data = all_stages.get(stage)

            # ==================================================
            # 9. CHECK WHETHER STAGE EXISTS
            # ==================================================

            if stage_data is None:
                return {
                    "status": "error",
                    "message": (
                        f"The '{stage}' stage has not been "
                        f"initialized for student '{reg_no}'. "
                        "The clearance record may use an older "
                        "stage structure."
                    )
                }, 404

            # ==================================================
            # 10. GET DOCUMENTS
            # ==================================================

            documents = stage_data.get("documents", [])

            if not isinstance(documents, list):
                return {
                    "status": "error",
                    "message": (
                        f"The document records for stage '{stage}' "
                        "have an invalid format."
                    )
                }, 500

            if not documents:
                return {
                    "status": "error",
                    "message": (
                        f"No documents have been uploaded under "
                        f"the '{stage}' stage for student '{reg_no}'."
                    )
                }, 404

            # ==================================================
            # 11. FIND DOCUMENT BY NAME
            # ==================================================

            selected_document = None

            for document in documents:

                if not isinstance(document, dict):
                    continue

                stored_document_name = str(
                    document.get("document_name", "")
                ).strip()

                if (
                    stored_document_name.casefold()
                    == document_name.casefold()
                ):
                    selected_document = document
                    break

            # ==================================================
            # 12. CHECK WHETHER DOCUMENT EXISTS
            # ==================================================

            if selected_document is None:
                return {
                    "status": "error",
                    "message": (
                        f"Document '{document_name}' was not found "
                        f"under the '{stage}' stage for student "
                        f"'{reg_no}'."
                    )
                }, 404

            # ==================================================
            # 13. GET STORED FILE PATH
            # ==================================================

            stored_file_path = selected_document.get("file_path")

            if not stored_file_path:
                return {
                    "status": "error",
                    "message": (
                        f"Document '{document_name}' exists in "
                        "the database, but its file path is missing."
                    )
                }, 404

            # ==================================================
            # 14. RESOLVE STORED FILE PATH
            # ==================================================

            # Support Windows-style and Unix-style path separators.

            stored_file_path = str(stored_file_path).strip()

            normalized_path = os.path.normpath(
                stored_file_path.replace("\\", os.sep)
            )

            if os.path.isabs(normalized_path):
                file_path = normalized_path
            else:
                file_path = os.path.join(
                    os.getcwd(),
                    normalized_path
                )

            file_path = os.path.realpath(file_path)

            # ==================================================
            # 15. RESTRICT ACCESS TO CLEARANCE UPLOAD DIRECTORY
            # ==================================================

            upload_root = os.path.realpath(
                os.path.join(
                    os.getcwd(),
                    "uploads",
                    "clearance_documents"
                )
            )

            try:
                path_is_allowed = (
                    os.path.commonpath([
                        upload_root,
                        file_path
                    ]) == upload_root
                )
            except ValueError:
                path_is_allowed = False

            if not path_is_allowed:
                return {
                    "status": "error",
                    "message": (
                        "The stored document path is outside the "
                        "permitted clearance document directory."
                    )
                }, 403

            # ==================================================
            # 16. CHECK ACTUAL FILE
            # ==================================================

            if not os.path.isfile(file_path):
                return {
                    "status": "error",
                    "message": (
                        f"Document '{document_name}' is recorded "
                        "in the database, but its actual file "
                        "could not be found on the server. "
                        f"Resolved path: '{file_path}'."
                    )
                }, 404

            # ==================================================
            # 17. DETERMINE WHETHER FILE IS A WORD DOCUMENT
            # ==================================================

            original_filename = selected_document.get(
                "original_filename"
            )

            if not original_filename:
                original_filename = os.path.basename(file_path)

            original_filename = os.path.basename(
                str(original_filename).replace("\\", "/")
            )

            file_extension = os.path.splitext(
                original_filename
            )[1].lower()

            # Fall back to the actual stored file extension
            # if the original filename does not have one.
            if not file_extension:
                file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension not in {".doc", ".docx"}:
                return {
                    "status": "error",
                    "message": (
                        f"The selected document is a "
                        f"'{file_extension or 'file without an extension'}' "
                        "file, not a Word document. "
                        "Only uploaded DOC and DOCX files can be "
                        "downloaded by this endpoint. A PDF must "
                        "be converted to Word format before it can "
                        "be downloaded as a Word document."
                    )
                }, 415

            # ==================================================
            # 18. SET CORRECT WORD MIME TYPE
            # ==================================================

            word_mime_types = {
                ".doc": (
                    "application/msword"
                ),
                ".docx": (
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                )
            }

            mime_type = word_mime_types[file_extension]

            # ==================================================
            # 19. FORCE WORD DOCUMENT DOWNLOAD
            # ==================================================

            # as_attachment=True instructs the client to download
            # the file instead of opening it as a browser preview.

            return send_file(
                file_path,
                mimetype=mime_type,
                as_attachment=True,
                download_name=original_filename,
                conditional=True
            )

        # ======================================================
        # 20. HANDLE UNEXPECTED ERRORS
        # ======================================================

        except Exception as e:

            print(
                "DOWNLOAD CLEARANCE DOCUMENT ERROR:",
                str(e)
            )

            return {
                "status": "error",
                "message": (
                    "An unexpected error occurred while downloading "
                    "the student's document. Check the server "
                    "terminal for technical details."
                )
            }, 500


# ==========================================================
# ADD RESOURCE
# ==========================================================

api.add_resource(
    DownloadClearanceDocument,
    "/api/v1/clearance/document/download"
)