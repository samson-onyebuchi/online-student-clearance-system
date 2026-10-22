from app.utils import *
from app.email_util import *
from flask import Flask, jsonify, Response, request, send_file, make_response
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
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
import json
from werkzeug.security import generate_password_hash, check_password_hash
import mimetypes
import uuid
from bson import ObjectId

# NOTE: Make sure your app and api are initialized like this in your main runner file:
# app = Flask(__name__)
# CORS(app)
# api = Api(app)


# ==========================================================
# GLOBAL JSON SERIALIZER FOR DATETIME & OBJECTID
# ==========================================================
def output_json_custom(data, code, headers=None):
    def default_serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, ObjectId):
            return str(o)
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

    rendered = json.dumps(data, default=default_serializer)
    response = make_response(rendered, code)
    if headers:
        response.headers.extend(headers)
    response.headers['Content-Type'] = 'application/json'
    return response


# ==========================================================
# 1. REGISTER STUDENT
# ==========================================================
class RegisterStudent(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("surname", type=str, required=True, help="Surname is required")
        self.parser.add_argument("first_name", type=str, required=True, help="First name is required")
        self.parser.add_argument("other_names", type=str, required=False)
        self.parser.add_argument("email", type=str, required=True, help="Email is required")
        self.parser.add_argument("reg_no", type=str, required=True, help="Registration number is required")
        self.parser.add_argument("department", type=str, required=True, help="Department is required")
        self.parser.add_argument("faculty", type=str, required=True, help="Faculty is required")
        self.parser.add_argument("phone_number", type=str, required=True, help="Phone number is required")
        self.parser.add_argument("gender", type=str, required=True, help="Gender is required")
        self.parser.add_argument("admission_year", type=int, required=True, help="Admission year is required")
        self.parser.add_argument("password", type=str, required=True, help="Password is required")

    def post(self):
        args = self.parser.parse_args()
        surname = args["surname"].strip().title()
        first_name = args["first_name"].strip().title()
        other_names = args["other_names"].strip().title() if args["other_names"] else ""
        email = args["email"].strip().lower()
        reg_no = args["reg_no"].strip().upper()
        department = args["department"].strip().title()
        faculty = args["faculty"].strip().title()
        phone_number = args["phone_number"].strip()
        gender = args["gender"].strip().lower()
        admission_year = args["admission_year"]
        password = args["password"].strip()

        if gender not in ["male", "female"]:
            return {"status": "error", "message": "Gender must be either 'male' or 'female'"}, 400

        current_year = datetime.now().year
        if admission_year > current_year:
            return {"status": "error", "message": "Admission year cannot be in the future"}, 400

        study_duration = current_year - admission_year
        student_status = "external" if study_duration > 6 else "regular"

        if len(password) < 6:
            return {"status": "error", "message": "Password must be at least 6 characters long"}, 400

        existing_student = students.find_one({
            "$or": [{"reg_no": reg_no}, {"phone_number": phone_number}, {"email": email}]
        })

        if existing_student:
            return {"status": "error", "message": "Student with this registration number, phone number, or email already exists"}, 409

        hashed_password = generate_password_hash(password)

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
            "admission_year": admission_year,
            "study_duration": study_duration,
            "student_status": student_status,
            "role": "student",
            "password": hashed_password,
            "account_status": "active",
            "created_at": datetime.utcnow()
        }

        result = students.insert_one(new_student)

        email_sent = EmailSender.send_student_registration_email(
            receiver_email=email,
            student_name=f"{surname} {first_name}",
            reg_no=reg_no,
            password=password
        )

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


# ==========================================================
# 2. LOGIN STUDENT
# ==========================================================
class LoginStudent(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("reg_no", type=str, required=True, help="Registration number is required")
        self.parser.add_argument("password", type=str, required=True, help="Password is required")

    def post(self):
        args = self.parser.parse_args()
        reg_no = args["reg_no"].strip().upper()
        password = args["password"].strip()

        student = students.find_one({"reg_no": reg_no})
        if not student:
            return {"status": "error", "message": "Invalid registration number or password"}, 401

        if student.get("account_status") != "active":
            return {"status": "error", "message": "Your account is not active. Please contact the administrator"}, 403

        if not check_password_hash(student["password"], password):
            return {"status": "error", "message": "Invalid registration number or password"}, 401

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


# ==========================================================
# 3. FORGOT PASSWORD
# ==========================================================
class ForgotPassword(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("reg_no", type=str, required=True, help="Registration number is required")

    def post(self):
        args = self.parser.parse_args()
        reg_no = args["reg_no"].strip().upper()

        student = students.find_one({"reg_no": reg_no})
        if not student:
            return {"status": "error", "message": "Student with this registration number does not exist"}, 404

        if student.get("account_status") != "active":
            return {"status": "error", "message": "Your account is not active. Please contact the administrator"}, 403

        if not student.get("email"):
            return {"status": "error", "message": "No email address is associated with this account"}, 400

        otp = str(random.randint(100000, 999999))
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)

        students.update_one(
            {"_id": student["_id"]},
            {"$set": {"password_reset_otp": otp, "password_reset_otp_expiry": otp_expiry}}
        )

        email_sent = EmailSender.send_student_forgot_password_email(
            receiver_email=student["email"],
            student_name=f'{student["surname"]} {student["first_name"]}',
            otp=otp
        )

        if not email_sent:
            return {"status": "error", "message": "Failed to send password reset email. Please try again"}, 500

        return {
            "status": "success",
            "message": "Password reset OTP has been sent to your email",
            "data": {"email": student["email"]}
        }, 200


# ==========================================================
# 4. OTP RESET STUDENT PASSWORD
# ==========================================================
class OTPResetStudentPassword(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("reg_no", type=str, required=True, help="Registration number is required")
        self.parser.add_argument("otp", type=str, required=True, help="OTP is required")
        self.parser.add_argument("new_password", type=str, required=True, help="New password is required")

    def post(self):
        args = self.parser.parse_args()
        reg_no = args["reg_no"].strip().upper()
        otp = args["otp"].strip()
        new_password = args["new_password"].strip()

        if len(new_password) < 6:
            return {"status": "error", "message": "Password must be at least 6 characters long"}, 400

        student = students.find_one({"reg_no": reg_no})
        if not student:
            return {"status": "error", "message": "Student with this registration number does not exist"}, 404

        if student.get("account_status") != "active":
            return {"status": "error", "message": "Your account is not active. Please contact the administrator"}, 403

        if not student.get("email"):
            return {"status": "error", "message": "No email address is associated with this account"}, 400

        stored_otp = student.get("password_reset_otp")
        if not stored_otp or otp != stored_otp:
            return {"status": "error", "message": "Invalid OTP"}, 400

        otp_expiry = student.get("password_reset_otp_expiry")
        if not otp_expiry or datetime.utcnow() > otp_expiry:
            return {"status": "error", "message": "OTP has expired. Please request a new OTP"}, 400

        hashed_password = generate_password_hash(new_password)

        update_result = students.update_one(
            {"_id": student["_id"]},
            {
                "$set": {"password": hashed_password, "updated_at": datetime.utcnow()},
                "$unset": {"password_reset_otp": "", "password_reset_otp_expiry": ""}
            }
        )

        if update_result.modified_count == 0:
            return {"status": "error", "message": "Password could not be changed. Please try again"}, 500

        email_sent = EmailSender.send_student_password_changed_email(
            receiver_email=student["email"],
            student_name=f'{student["surname"]} {student["first_name"]}'
        )

        return {
            "status": "success",
            "message": "Your password has been changed successfully. You can now login with your new password",
            "data": {"email": student["email"], "email_sent": email_sent}
        }, 200


# ==========================================================
# 5. RESET STUDENT PASSWORD (LOGGED IN)
# ==========================================================
class ResetStudentPassword(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("reg_no", type=str, required=True, help="Registration number is required")
        self.parser.add_argument("current_password", type=str, required=True, help="Current password is required")
        self.parser.add_argument("new_password", type=str, required=True, help="New password is required")

    def post(self):
        args = self.parser.parse_args()
        reg_no = args["reg_no"].strip().upper()
        current_password = args["current_password"].strip()
        new_password = args["new_password"].strip()

        if len(new_password) < 6:
            return {"status": "error", "message": "Password must be at least 6 characters long"}, 400

        if current_password == new_password:
            return {"status": "error", "message": "New password must be different from your current password"}, 400

        student = students.find_one({"reg_no": reg_no})
        if not student:
            return {"status": "error", "message": "Student with this registration number does not exist"}, 404

        if student.get("account_status") != "active":
            return {"status": "error", "message": "Your account is not active. Please contact the administrator"}, 403

        if not student.get("email"):
            return {"status": "error", "message": "No email address is associated with this account"}, 400

        if not check_password_hash(student["password"], current_password):
            return {"status": "error", "message": "Current password is incorrect"}, 401

        hashed_password = generate_password_hash(new_password)

        update_result = students.update_one(
            {"_id": student["_id"]},
            {"$set": {"password": hashed_password, "updated_at": datetime.utcnow()}}
        )

        if update_result.modified_count == 0:
            return {"status": "error", "message": "Password could not be changed. Please try again"}, 500

        email_sent = EmailSender.send_student_password_changed_email(
            receiver_email=student["email"],
            student_name=f'{student["surname"]} {student["first_name"]}'
        )

        return {
            "status": "success",
            "message": "Your password has been changed successfully. You can now login with your new password",
            "data": {"email": student["email"], "email_sent": email_sent}
        }, 200


# ==========================================================
# 6. CREATE STUDENT CLEARANCE
# ==========================================================
class CreateClearance(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("reg_no", type=str, required=True, help="Registration number is required")

    def post(self):
        try:
            args = self.parser.parse_args()
            reg_no = args["reg_no"]

            if not reg_no or not str(reg_no).strip():
                return {"status": "error", "message": "Registration number is required."}, 400

            reg_no = str(reg_no).strip().upper()

            student = students.find_one({"reg_no": reg_no})
            if student is None:
                return {"status": "error", "message": f"Student with registration number '{reg_no}' does not exist."}, 404

            clearance = clearances.find_one({"reg_no": reg_no})
            if clearance is not None:
                return {
                    "status": "error",
                    "message": f"Clearance has already been started for student '{reg_no}'.",
                    "data": {
                        "clearance_id": clearance["_id"],
                        "reg_no": clearance.get("reg_no"),
                        "current_stage": clearance.get("current_stage"),
                        "status": clearance.get("status"),
                        "stage_status": clearance.get("stage_status"),
                        "stages": clearance.get("stages", {})
                    }
                }, 409

            stage_names = ["department", "finance", "library", "alumni", "student_affairs", "health", "security", "audit"]
            stages = {
                stage_name: {
                    "status": "pending",
                    "feedback": "",
                    "documents": [],
                    "approved_by": None,
                    "approved_at": None,
                    "rejected_by": None,
                    "rejected_at": None
                }
                for stage_name in stage_names
            }

            current_time = datetime.utcnow()
            new_clearance = {
                "reg_no": reg_no,
                "current_stage": "department",
                "status": "in_progress",
                "stage_status": "pending",
                "feedback": "",
                "stages": stages,
                "created_at": current_time,
                "updated_at": current_time
            }

            result = clearances.insert_one(new_clearance)
            if not result.inserted_id:
                return {"status": "error", "message": f"Student '{reg_no}' exists, but clearance could not be created."}, 500

            return {
                "status": "success",
                "message": f"Clearance started successfully for student '{reg_no}'. The first stage is Department.",
                "data": {
                    "clearance_id": result.inserted_id,
                    "reg_no": reg_no,
                    "current_stage": "department",
                    "status": "in_progress",
                    "stage_status": "pending",
                    "stages": stages,
                    "created_at": current_time,
                    "updated_at": current_time
                }
            }, 201

        except Exception as e:
            return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}, 500


# ==========================================================
# 7. VIEW STUDENT CLEARANCE
# ==========================================================
class ViewClearance(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("reg_no", type=str, required=True, location="args", help="Registration number is required")

    def get(self):
        try:
            args = self.parser.parse_args()
            reg_no = args["reg_no"]

            if not reg_no:
                return {"status": "error", "message": "Registration number is required"}, 400

            reg_no = str(reg_no).strip().upper()

            student = students.find_one({"reg_no": reg_no})
            if student is None:
                return {"status": "error", "message": f"Student with registration number '{reg_no}' does not exist."}, 404

            clearance = clearances.find_one({"reg_no": reg_no})
            if clearance is None:
                return {"status": "error", "message": f"Student '{reg_no}' has not started the clearance process."}, 404

            return {
                "status": "success",
                "message": "Clearance retrieved successfully.",
                "data": {
                    "clearance_id": clearance["_id"],
                    "reg_no": clearance.get("reg_no"),
                    "current_stage": clearance.get("current_stage"),
                    "status": clearance.get("status"),
                    "stage_status": clearance.get("stage_status"),
                    "feedback": clearance.get("feedback", ""),
                    "stages": clearance.get("stages", {}),
                    "created_at": clearance.get("created_at"),
                    "updated_at": clearance.get("updated_at")
                }
            }, 200

        except Exception as e:
            return {"status": "error", "message": str(e)}, 500


# ==========================================================
# 8. UPLOAD DOCUMENT
# ==========================================================
class UploadDocument(Resource):
    def post(self):
        file_path = None
        try:
            if not request.content_type or not request.content_type.startswith("multipart/form-data"):
                return {"status": "error", "message": "This endpoint requires multipart/form-data."}, 400

            reg_no = request.form.get("reg_no")
            if not reg_no or not str(reg_no).strip():
                return {"status": "error", "message": "Student registration number is required."}, 400

            reg_no = str(reg_no).strip().upper()
            safe_reg_no = reg_no.replace("/", "_").replace("\\", "_")

            stage = request.form.get("stage")
            if not stage or not str(stage).strip():
                return {"status": "error", "message": "Clearance stage is required."}, 400

            stage = str(stage).strip().lower()
            allowed_stages = ["department", "finance", "library", "alumni", "student_affairs", "health", "security", "audit"]

            if stage not in allowed_stages:
                return {"status": "error", "message": f"Invalid clearance stage '{stage}'."}, 400

            document_name = request.form.get("document_name")
            if not document_name or not str(document_name).strip():
                return {"status": "error", "message": "Document name is required."}, 400

            document_name = str(document_name).strip()

            if "document" not in request.files:
                return {"status": "error", "message": "No document file was received."}, 400

            file = request.files.get("document")
            if file is None or not file.filename:
                return {"status": "error", "message": "No document was selected."}, 400

            original_filename = os.path.basename(file.filename.strip())
            if "." not in original_filename:
                return {"status": "error", "message": "The uploaded file has no valid extension."}, 400

            file_extension = original_filename.rsplit(".", 1)[1].lower()
            if file_extension not in {"pdf", "doc", "docx"}:
                return {"status": "error", "message": f"File type '.{file_extension}' is not allowed."}, 400

            clearance = clearances.find_one({"reg_no": reg_no})
            if clearance is None:
                return {"status": "error", "message": f"Student '{reg_no}' has not started clearance."}, 404

            current_stage = str(clearance.get("current_stage", "")).strip().lower()
            if stage != current_stage:
                return {"status": "error", "message": f"Current stage is '{current_stage}', but requested stage is '{stage}'."}, 400

            stages_data = clearance.get("stages", {})
            current_stage_data = stages_data.get(current_stage, {})
            stage_status = str(current_stage_data.get("status", "pending")).strip().lower()

            if stage_status in {"approved", "completed"}:
                return {"status": "error", "message": f"The '{current_stage}' stage has already been approved."}, 409

            upload_folder = os.path.join("uploads", "clearance_documents", safe_reg_no, current_stage)
            os.makedirs(upload_folder, exist_ok=True)

            unique_id = uuid.uuid4().hex
            safe_filename = f"{document_name}_{unique_id}.{file_extension}"
            file_path = os.path.join(upload_folder, safe_filename)

            file.save(file_path)

            current_time = datetime.utcnow()
            document_record = {
                "document_name": document_name,
                "original_filename": original_filename,
                "file_path": file_path,
                "file_type": file_extension,
                "uploaded_at": current_time,
                "status": "under_review"
            }

            update_result = clearances.update_one(
                {"_id": clearance["_id"], "current_stage": current_stage},
                {
                    "$push": {f"stages.{current_stage}.documents": document_record},
                    "$set": {
                        f"stages.{current_stage}.status": "under_review",
                        "updated_at": current_time
                    }
                }
            )

            if update_result.modified_count != 1:
                if os.path.exists(file_path):
                    os.remove(file_path)
                return {"status": "error", "message": "Clearance record could not be updated."}, 409

            return {
                "status": "success",
                "message": f"The document '{document_name}' was uploaded successfully.",
                "data": {
                    "reg_no": reg_no,
                    "stage": current_stage,
                    "stage_status": "under_review",
                    "document_name": document_name,
                    "original_filename": original_filename,
                    "file_type": file_extension,
                    "file_path": file_path,
                    "uploaded_at": current_time
                }
            }, 201

        except Exception as e:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            return {"status": "error", "message": str(e)}, 500


# ==========================================================
# 9. VIEW UPLOADED CLEARANCE DOCUMENTS
# ==========================================================
class ViewUploadedDocuments(Resource):
    def get(self):
        try:
            reg_no = request.args.get("reg_no")
            if not reg_no:
                return {"status": "error", "message": "Registration number is required."}, 400

            reg_no = str(reg_no).strip().upper()
            clearance = clearances.find_one({"reg_no": reg_no})
            if clearance is None:
                return {"status": "error", "message": f"Student '{reg_no}' has not started clearance."}, 404

            stages_data = clearance.get("stages", {})
            total_documents = sum(len(stage_info.get("documents", [])) for stage_info in stages_data.values())

            return {
                "status": "success",
                "message": f"Uploaded documents retrieved successfully for student '{reg_no}'.",
                "data": {
                    "reg_no": reg_no,
                    "total_documents": total_documents,
                    "documents": stages_data
                }
            }, 200

        except Exception as e:
            return {"status": "error", "message": str(e)}, 500


# ==========================================================
# 10. VIEW ACTUAL CLEARANCE DOCUMENT
# ==========================================================
class ViewClearanceDocument(Resource):
    def get(self):
        try:
            reg_no = request.args.get("reg_no")
            stage = request.args.get("stage")
            document_name = request.args.get("document_name")

            if not reg_no or not stage or not document_name:
                return {"status": "error", "message": "reg_no, stage, and document_name query parameters are required."}, 400

            reg_no = str(reg_no).strip().upper()
            stage = str(stage).strip().lower()
            document_name = str(document_name).strip()

            clearance = clearances.find_one({"reg_no": reg_no})
            if clearance is None:
                return {"status": "error", "message": f"Student '{reg_no}' clearance not found."}, 404

            stage_data = clearance.get("stages", {}).get(stage)
            if stage_data is None:
                return {"status": "error", "message": f"Stage '{stage}' not initialized."}, 404

            selected_doc = None
            for doc in stage_data.get("documents", []):
                if str(doc.get("document_name", "")).strip().casefold() == document_name.casefold():
                    selected_doc = doc
                    break

            if selected_doc is None:
                return {"status": "error", "message": f"Document '{document_name}' not found."}, 404

            file_path = selected_doc.get("file_path")
            if not file_path or not os.path.isfile(file_path):
                return {"status": "error", "message": "Actual file not found on server."}, 404

            original_filename = selected_doc.get("original_filename", os.path.basename(file_path))
            mime_type, _ = mimetypes.guess_type(original_filename)
            if mime_type is None:
                mime_type = "application/octet-stream"

            return send_file(file_path, mimetype=mime_type, as_attachment=False, download_name=original_filename)

        except Exception as e:
            return {"status": "error", "message": str(e)}, 500


# ==========================================================
# 11. DOWNLOAD SPECIFIC CLEARANCE DOCUMENT
# ==========================================================
class DownloadClearanceDocument(Resource):
    def get(self):
        try:
            reg_no = request.args.get("reg_no")
            stage = request.args.get("stage")
            document_name = request.args.get("document_name")

            if not reg_no or not stage or not document_name:
                return {"status": "error", "message": "reg_no, stage, and document_name query parameters are required."}, 400

            reg_no = str(reg_no).strip().upper()
            stage = str(stage).strip().lower()
            document_name = str(document_name).strip()

            clearance = clearances.find_one({"reg_no": reg_no})
            if clearance is None:
                return {"status": "error", "message": f"Student '{reg_no}' clearance not found."}, 404

            stage_data = clearance.get("stages", {}).get(stage)
            if stage_data is None:
                return {"status": "error", "message": f"Stage '{stage}' not initialized."}, 404

            selected_doc = None
            for doc in stage_data.get("documents", []):
                if str(doc.get("document_name", "")).strip().casefold() == document_name.casefold():
                    selected_doc = doc
                    break

            if selected_doc is None:
                return {"status": "error", "message": f"Document '{document_name}' not found."}, 404

            file_path = selected_doc.get("file_path")
            if not file_path or not os.path.isfile(file_path):
                return {"status": "error", "message": "Actual file not found on server."}, 404

            original_filename = selected_doc.get("original_filename", os.path.basename(file_path))
            file_extension = os.path.splitext(original_filename)[1].lower()

            if file_extension not in {".doc", ".docx"}:
                return {"status": "error", "message": "Only uploaded DOC and DOCX files can be downloaded via this endpoint."}, 415

            word_mime_types = {
                ".doc": "application/msword",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
            mime_type = word_mime_types.get(file_extension, "application/octet-stream")

            return send_file(file_path, mimetype=mime_type, as_attachment=True, download_name=original_filename, conditional=True)

        except Exception as e:
            return {"status": "error", "message": str(e)}, 500


# ==========================================================
# REGISTER ALL RESOURCES & CUSTOM JSON HANDLER TO API
# ==========================================================
# Ensure `api` is initialized with your Flask app before this section:
# api = Api(app)
api.representation('application/json')(output_json_custom)

api.add_resource(RegisterStudent, "/api/v1/clearance/register/student")
api.add_resource(LoginStudent, "/api/v1/clearance/login/student")
api.add_resource(ForgotPassword, "/api/v1/clearance/forgot-password/student")
api.add_resource(OTPResetStudentPassword, "/api/v1/clearance/otp-reset-password/student")
api.add_resource(ResetStudentPassword, "/api/v1/clearance/reset-password/student")
api.add_resource(CreateClearance, "/api/v1/clearance/create")
api.add_resource(ViewClearance, "/api/v1/clearance/view")
api.add_resource(UploadDocument, "/api/v1/clearance/upload-document")
api.add_resource(ViewUploadedDocuments, "/api/v1/clearance/documents")
api.add_resource(ViewClearanceDocument, "/api/v1/clearance/document/view")
api.add_resource(DownloadClearanceDocument, "/api/v1/clearance/document/download")