from app.utils import *
from app.email_util import *
from flask import Flask, jsonify, Response
from flask_restful import Api, Resource, reqparse
from werkzeug.exceptions import BadRequest
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import random
import bcrypt   
import io
import string
import secrets
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from flask import request
from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================================
# ONBOARD STAFF FOR THE 8 UNIVERSITY CLEARANCE STAGES
# Creates a staff account, assigns the correct clearance stage,
# generates a temporary password, and sends onboarding details.
# ==========================================================

class OnboardStaff(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "staff_id", type=str, required=True,
            help="Staff ID is required."
        )
        self.parser.add_argument(
            "surname", type=str, required=True,
            help="Surname is required."
        )
        self.parser.add_argument(
            "first_name", type=str, required=True,
            help="First name is required."
        )
        self.parser.add_argument(
            "email", type=str, required=True,
            help="Email address is required."
        )
        self.parser.add_argument(
            "department", type=str, required=True,
            help="Department is required."
        )
        self.parser.add_argument(
            "faculty", type=str, required=True,
            help="Faculty is required."
        )
        self.parser.add_argument(
            "role", type=str, required=True,
            help="Staff role is required."
        )

    def post(self):

        # ---------- Parse request ----------
        args = self.parser.parse_args()

        # ---------- Clean input ----------
        staff_id = (args.get("staff_id") or "").strip().upper()
        surname = (args.get("surname") or "").strip().title()
        first_name = (args.get("first_name") or "").strip().title()
        email = (args.get("email") or "").strip().lower()
        department = (args.get("department") or "").strip().title()
        faculty = (args.get("faculty") or "").strip().title()
        submitted_role = (args.get("role") or "").strip()

        # ---------- Validate required fields ----------
        if not all([
            staff_id, surname, first_name,
            email, department, faculty, submitted_role
        ]):
            return {
                "status": "error",
                "message": (
                    "All staff details, including the assigned role, "
                    "are required."
                )
            }, 400

        # ---------- Validate email ----------
        if (
            "@" not in email
            or "." not in email.split("@")[-1]
            or " " in email
        ):
            return {
                "status": "error",
                "message": "Please provide a valid staff email address."
            }, 400

        # ---------- Define the 8 recognized clearance roles ----------
        role_mapping = {
            "department clearance officer": {
                "role": "Department Clearance Officer",
                "assigned_stage": "department"
            },
            "finance clearance officer": {
                "role": "Finance Clearance Officer",
                "assigned_stage": "finance"
            },
            "library clearance officer": {
                "role": "Library Clearance Officer",
                "assigned_stage": "library"
            },
            "alumni clearance officer": {
                "role": "Alumni Clearance Officer",
                "assigned_stage": "alumni"
            },
            "student affairs clearance officer": {
                "role": "Student Affairs Clearance Officer",
                "assigned_stage": "student_affairs"
            },
            "health clearance officer": {
                "role": "Health Clearance Officer",
                "assigned_stage": "health"
            },
            "security clearance officer": {
                "role": "Security Clearance Officer",
                "assigned_stage": "security"
            },
            "audit clearance officer": {
                "role": "Audit Clearance Officer",
                "assigned_stage": "audit"
            }
        }

        # ---------- Normalize submitted role ----------
        role_key = " ".join(
            submitted_role.replace("_", " ")
            .replace("-", " ")
            .lower()
            .split()
        )

        # ---------- Validate role ----------
        if role_key not in role_mapping:
            return {
                "status": "error",
                "message": (
                    "Invalid staff role. Select one of the eight "
                    "recognized clearance roles."
                ),
                "allowed_roles": [
                    "Department Clearance Officer",
                    "Finance Clearance Officer",
                    "Library Clearance Officer",
                    "Alumni Clearance Officer",
                    "Student Affairs Clearance Officer",
                    "Health Clearance Officer",
                    "Security Clearance Officer",
                    "Audit Clearance Officer"
                ]
            }, 400

        role_details = role_mapping[role_key]
        role = role_details["role"]
        assigned_stage = role_details["assigned_stage"]

        # ---------- Check for existing staff ----------
        try:
            existing_staff = mongo.db.staff.find_one({
                "$or": [
                    {"staff_id": staff_id},
                    {"email": email}
                ]
            })

        except Exception as e:
            print(f"Staff duplicate-check database error: {e}")

            return {
                "status": "error",
                "message": (
                    "Unable to verify the staff ID or email. "
                    "Please try again."
                )
            }, 500

        if existing_staff:
            if existing_staff.get("staff_id") == staff_id:
                return {
                    "status": "error",
                    "message": f"Staff ID '{staff_id}' already exists."
                }, 409

            return {
                "status": "error",
                "message": f"Email '{email}' is already registered."
            }, 409

        # ---------- Generate temporary password ----------
        temporary_password = str(
            random.SystemRandom().randint(10000000, 99999999)
        )

        # ---------- Hash temporary password ----------
        try:
            hashed_password = generate_password_hash(
                temporary_password
            )

        except Exception as e:
            print(f"Staff password-hashing error: {e}")

            return {
                "status": "error",
                "message": (
                    "Unable to prepare the staff password. "
                    "The account was not created."
                )
            }, 500

        # ---------- Prepare staff record ----------
        new_staff = {
            "staff_id": staff_id,
            "surname": surname,
            "first_name": first_name,
            "email": email,
            "department": department,
            "faculty": faculty,
            "role": role,
            "assigned_stage": assigned_stage,
            "password": hashed_password,
            "must_change_password": True,
            "account_status": "active",
            "created_at": datetime.utcnow()
        }

        # ---------- Save staff account ----------
        try:
            result = mongo.db.staff.insert_one(new_staff)

        except Exception as e:
            print(f"Staff account creation database error: {e}")

            return {
                "status": "error",
                "message": (
                    "Unable to create the staff account. "
                    "Please check the database connection and try again."
                )
            }, 500

        # ---------- Send onboarding email ----------
        email_sent = False

        try:
            email_result = EmailSender.send_staff_onboarding_email(
                receiver_email=email,
                staff_name=f"{surname} {first_name}",
                staff_id=staff_id,
                role=role,
                temporary_password=temporary_password
            )

            email_sent = email_result is True

            if email_sent:
                print(
                    "Onboarding email accepted by SMTP server "
                    f"for staff ID: {staff_id}"
                )
            else:
                print(
                    f"Onboarding email failed for staff ID: {staff_id}"
                )

        except Exception as e:
            print(
                f"Onboarding email error for staff ID {staff_id}: "
                f"{type(e).__name__}: {e}"
            )
            email_sent = False

        # ---------- Prepare response ----------
        response_data = {
            "id": str(result.inserted_id),
            "staff_id": staff_id,
            "surname": surname,
            "first_name": first_name,
            "email": email,
            "department": department,
            "faculty": faculty,
            "role": role,
            "assigned_stage": assigned_stage,
            "account_status": "active",
            "must_change_password": True,
            "email_sent": email_sent
        }

        # ---------- Successful onboarding email ----------
        if email_sent:
            return {
                "status": "success",
                "message": (
                    "Staff account created successfully. "
                    "The onboarding email was accepted by the email server. "
                    "The recipient should check their inbox and spam folder."
                ),
                "data": response_data
            }, 201

        # ---------- Account created but email failed ----------
        return {
            "status": "partial_success",
            "message": (
                "Staff account created successfully, but the onboarding "
                "email failed. The account remains saved. Check the "
                "application logs and SMTP configuration."
            ),
            "data": response_data
        }, 201


# ---------- ADD RESOURCE ----------
# Replace the existing registration; do not register this route twice.
api.add_resource(
    OnboardStaff,
    "/api/v1/clearance/admin/onboard/staff"
)

# ==========================================================
# STAFF LOGIN
# Authenticates staff using their staff ID and password,
# verifies the stored password hash, and checks account status.
# ==========================================================

class StaffLogin(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "staff_id",
            type=str,
            required=True,
            help="Staff ID is required."
        )

        self.parser.add_argument(
            "password",
            type=str,
            required=True,
            help="Password is required."
        )

    def post(self):

        # ---------- Parse request ----------
        args = self.parser.parse_args()

        # ---------- Clean input ----------
        staff_id = (args.get("staff_id") or "").strip().upper()
        password = args.get("password") or ""

        # ---------- Validate required fields ----------
        if not staff_id or not password:
            return {
                "status": "error",
                "message": "Staff ID and password are required."
            }, 400

        # ---------- Find staff account ----------
        try:
            staff = mongo.db.staff.find_one({
                "staff_id": staff_id
            })
        except Exception as e:
            print(f"Staff login database error: {e}")

            return {
                "status": "error",
                "message": (
                    "Unable to verify your staff account at this time. "
                    "Please try again."
                )
            }, 500

        # ---------- Check whether staff exists ----------
        if not staff:
            return {
                "status": "error",
                "message": "Invalid Staff ID or password."
            }, 401

        # ---------- Check account status ----------
        if staff.get("account_status") != "active":
            return {
                "status": "error",
                "message": (
                    "Your staff account is not active. "
                    "Please contact the system administrator."
                )
            }, 403

        # ---------- Verify stored password ----------
        stored_password = staff.get("password")

        if not stored_password:
            return {
                "status": "error",
                "message": (
                    "Your account has no valid password record. "
                    "Please contact the system administrator."
                )
            }, 500

        try:
            password_valid = check_password_hash(
                stored_password,
                password
            )
        except (ValueError, TypeError) as e:
            print(f"Staff password verification error: {e}")

            return {
                "status": "error",
                "message": (
                    "Unable to verify your password. "
                    "Please contact the system administrator."
                )
            }, 500

        if not password_valid:
            return {
                "status": "error",
                "message": "Invalid Staff ID or password."
            }, 401

        # ---------- Check temporary password requirement ----------
        if staff.get("must_change_password", False):
            return {
                "status": "success",
                "message": (
                    "Login credentials verified. You must change your "
                    "temporary password before proceeding."
                ),
                "must_change_password": True,
                "data": {
                    "staff_id": staff.get("staff_id"),
                    "surname": staff.get("surname"),
                    "first_name": staff.get("first_name"),
                    "email": staff.get("email"),
                    "department": staff.get("department"),
                    "faculty": staff.get("faculty"),
                    "role": staff.get("role"),
                    "assigned_stage": staff.get("assigned_stage"),
                    "account_status": staff.get("account_status")
                }
            }, 200

        # ---------- Return successful login ----------
        return {
            "status": "success",
            "message": "Staff login successful.",
            "must_change_password": False,
            "data": {
                "staff_id": staff.get("staff_id"),
                "surname": staff.get("surname"),
                "first_name": staff.get("first_name"),
                "email": staff.get("email"),
                "department": staff.get("department"),
                "faculty": staff.get("faculty"),
                "role": staff.get("role"),
                "assigned_stage": staff.get("assigned_stage"),
                "account_status": staff.get("account_status")
            }
        }, 200


# ---------- ADD RESOURCE ----------
api.add_resource(
    StaffLogin,
    "/api/v1/clearance/login/staff"
)


# ==========================================================
# STAFF FORGOT PASSWORD
# Uses staff_id as the staff account identifier.
# Sends the password reset OTP to the staff member's
# registered email address.
# ==========================================================

class StaffForgotPassword(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "staff_id",
            type=str,
            required=True,
            help="Staff ID is required."
        )

    def post(self):
        data = self.parser.parse_args()

        staff_id = data["staff_id"].strip().upper()

        # --------------------------------------------------
        # 1. VALIDATE STAFF ID
        # --------------------------------------------------
        if not staff_id:
            return {
                "success": False,
                "message": "Staff ID cannot be empty."
            }, 400

        # --------------------------------------------------
        # 2. FIND STAFF USING STAFF ID
        # --------------------------------------------------
        staff = mongo.db.staff.find_one({
            "staff_id": staff_id
        })

        if not staff:
            return {
                "success": False,
                "message": (
                    "No staff account was found with the "
                    "provided Staff ID."
                )
            }, 404

        # --------------------------------------------------
        # 3. CHECK STAFF ACCOUNT STATUS
        # --------------------------------------------------
        if staff.get("account_status") != "active":
            return {
                "success": False,
                "message": (
                    "This staff account is not active. "
                    "Contact the system administrator."
                )
            }, 403

        # --------------------------------------------------
        # 4. GET REGISTERED EMAIL ADDRESS
        # --------------------------------------------------
        email = staff.get("email", "").strip()

        if not email:
            return {
                "success": False,
                "message": (
                    "No email address is registered for this "
                    "staff account. Contact the administrator."
                )
            }, 400

        # --------------------------------------------------
        # 5. GENERATE SIX-DIGIT OTP
        # --------------------------------------------------
        otp = f"{secrets.randbelow(1000000):06d}"

        otp_hash = generate_password_hash(otp)

        current_time = datetime.now(timezone.utc)
        expiry_time = current_time + timedelta(minutes=10)

        # --------------------------------------------------
        # 6. SAVE OTP AGAINST THE STAFF ACCOUNT
        # --------------------------------------------------
        update_result = mongo.db.staff.update_one(
            {"staff_id": staff_id},
            {
                "$set": {
                    "password_reset_otp_hash": otp_hash,
                    "password_reset_otp_created_at": current_time,
                    "password_reset_otp_expires_at": expiry_time
                }
            }
        )

        if update_result.matched_count != 1:
            return {
                "success": False,
                "message": (
                    "The staff account could not be updated. "
                    "Please try again."
                )
            }, 500

        # --------------------------------------------------
        # 7. SEND OTP TO REGISTERED EMAIL
        # --------------------------------------------------
        staff_name = " ".join(
            str(staff.get(field, "")).strip()
            for field in ("first_name", "surname")
            if str(staff.get(field, "")).strip()
        )

        if not staff_name:
            staff_name = "Staff Member"

        email_sent = EmailSender.send_staff_forgot_password_email(
            receiver_email=email,
            staff_name=staff_name,
            otp=otp
        )

        # --------------------------------------------------
        # 8. HANDLE EMAIL DELIVERY FAILURE
        # --------------------------------------------------
        if not email_sent:
            mongo.db.staff.update_one(
                {
                    "staff_id": staff_id,
                    "password_reset_otp_hash": otp_hash
                },
                {
                    "$unset": {
                        "password_reset_otp_hash": "",
                        "password_reset_otp_created_at": "",
                        "password_reset_otp_expires_at": ""
                    }
                }
            )

            return {
                "success": False,
                "message": (
                    "The OTP email could not be sent to the "
                    "registered email address. Please try again."
                )
            }, 500

        # --------------------------------------------------
        # 9. RETURN SUCCESS RESPONSE
        # --------------------------------------------------
        return {
            "success": True,
            "message": (
                "A password reset OTP has been sent to the "
                "email address registered to this staff account."
            ),
            "staff_id": staff_id,
            "expires_in_minutes": 10
        }, 200


# ==========================================================
# STAFF FORGOT PASSWORD ROUTE
# ==========================================================

api.add_resource(
    StaffForgotPassword,
    "/api/v1/clearance/forgot-password/staff"
)


# ==========================================================
# STAFF RESET PASSWORD WITH OTP
# Uses staff_id to identify the staff account, verifies the
# OTP sent to the registered email, and securely saves the
# new password after validating the OTP and its expiry.
# ==========================================================

class StaffResetPasswordWithOTP(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "staff_id",
            type=str,
            required=True,
            help="Staff ID is required."
        )

        self.parser.add_argument(
            "otp",
            type=str,
            required=True,
            help="The OTP sent to your registered email is required."
        )

        self.parser.add_argument(
            "new_password",
            type=str,
            required=True,
            help="New password is required."
        )

        self.parser.add_argument(
            "confirm_password",
            type=str,
            required=True,
            help="Please confirm your new password."
        )

    def post(self):
        data = self.parser.parse_args()

        staff_id = data["staff_id"].strip().upper()
        otp = data["otp"].strip()
        new_password = data["new_password"]
        confirm_password = data["confirm_password"]

        # --------------------------------------------------
        # 1. VALIDATE REQUIRED VALUES
        # --------------------------------------------------
        if not staff_id:
            return {
                "success": False,
                "message": "Staff ID cannot be empty."
            }, 400

        if not otp:
            return {
                "success": False,
                "message": "OTP cannot be empty."
            }, 400

        if not new_password:
            return {
                "success": False,
                "message": "New password cannot be empty."
            }, 400

        if len(new_password) < 8:
            return {
                "success": False,
                "message": (
                    "Password must contain at least "
                    "8 characters."
                )
            }, 400

        if new_password != confirm_password:
            return {
                "success": False,
                "message": (
                    "New password and confirm password do not match."
                )
            }, 400

        # --------------------------------------------------
        # 2. FIND STAFF USING STAFF ID
        # --------------------------------------------------
        staff = mongo.db.staff.find_one({
            "staff_id": staff_id
        })

        if not staff:
            return {
                "success": False,
                "message": (
                    "No staff account was found with the "
                    "provided Staff ID."
                )
            }, 404

        # --------------------------------------------------
        # 3. CHECK STAFF ACCOUNT STATUS
        # --------------------------------------------------
        if staff.get("account_status") != "active":
            return {
                "success": False,
                "message": (
                    "This staff account is not active. "
                    "Contact the system administrator."
                )
            }, 403

        # --------------------------------------------------
        # 4. CHECK WHETHER AN OTP WAS GENERATED
        # --------------------------------------------------
        otp_hash = staff.get("password_reset_otp_hash")
        expiry_time = staff.get("password_reset_otp_expires_at")

        if not otp_hash or not expiry_time:
            return {
                "success": False,
                "message": (
                    "No active password reset OTP was found. "
                    "Request a new OTP first."
                )
            }, 400

        # --------------------------------------------------
        # 5. CHECK OTP EXPIRY
        # --------------------------------------------------
        current_time = datetime.now(timezone.utc)

        # MongoDB may return stored datetimes without timezone
        # information. Treat those values as UTC.
        if expiry_time.tzinfo is None:
            expiry_time = expiry_time.replace(
                tzinfo=timezone.utc
            )

        if current_time >= expiry_time:
            mongo.db.staff.update_one(
                {"staff_id": staff_id},
                {
                    "$unset": {
                        "password_reset_otp_hash": "",
                        "password_reset_otp_created_at": "",
                        "password_reset_otp_expires_at": ""
                    }
                }
            )

            return {
                "success": False,
                "message": (
                    "Your password reset OTP has expired. "
                    "Please request a new OTP."
                )
            }, 400

        # --------------------------------------------------
        # 6. VERIFY OTP
        # --------------------------------------------------
        if not check_password_hash(otp_hash, otp):
            return {
                "success": False,
                "message": (
                    "The OTP you entered is incorrect. "
                    "Please check your email and try again."
                )
            }, 400

        # --------------------------------------------------
        # 7. HASH THE NEW PASSWORD
        # --------------------------------------------------
        hashed_password = generate_password_hash(new_password)

        # --------------------------------------------------
        # 8. UPDATE PASSWORD AND CLEAR OTP
        # --------------------------------------------------
        update_result = mongo.db.staff.update_one(
            {
                "staff_id": staff_id,
                "password_reset_otp_hash": otp_hash
            },
            {
                "$set": {
                    "password": hashed_password,
                    "password_changed_at": current_time
                },
                "$unset": {
                    "password_reset_otp_hash": "",
                    "password_reset_otp_created_at": "",
                    "password_reset_otp_expires_at": ""
                }
            }
        )

        if update_result.modified_count != 1:
            return {
                "success": False,
                "message": (
                    "The password could not be updated. "
                    "The OTP may have changed or already been used. "
                    "Please request a new OTP and try again."
                )
            }, 409

        # --------------------------------------------------
        # 9. RETURN SUCCESS RESPONSE
        # --------------------------------------------------
        return {
            "success": True,
            "message": (
                "Your staff account password has been reset "
                "successfully. You can now log in using your "
                "new password."
            ),
            "staff_id": staff_id
        }, 200


# ==========================================================
# STAFF RESET PASSWORD WITH OTP ROUTE
# ==========================================================

api.add_resource(
    StaffResetPasswordWithOTP,
    "/api/v1/clearance/reset-password/staff"
)


# ==========================================================
# RESET STAFF PASSWORD USING OTP
# Uses staff_id as the primary identifier, verifies the OTP
# and expiry, updates the password, and clears OTP fields.
# ==========================================================

class OTPResetStaffPassword(Resource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "staff_id",
            type=str,
            required=True,
            help="Staff ID is required."
        )
        parser.add_argument(
            "otp",
            type=str,
            required=True,
            help="OTP is required."
        )
        parser.add_argument(
            "new_password",
            type=str,
            required=True,
            help="New password is required."
        )

        args = parser.parse_args()

        staff_id = args["staff_id"].strip().upper()
        otp = args["otp"].strip()
        new_password = args["new_password"]

        staff_collection = mongo.db.staff

        # Find the staff account using its primary identifier
        staff = staff_collection.find_one({"staff_id": staff_id})

        if not staff:
            return {
                "status": "error",
                "message": f"No staff account was found with Staff ID '{staff_id}'."
            }, 404

        # Confirm that an OTP was generated
        otp_hash = staff.get("password_reset_otp_hash")
        otp_expiry = staff.get("password_reset_otp_expires_at")

        if not otp_hash or not otp_expiry:
            return {
                "status": "error",
                "message": "No active password-reset OTP was found. Request a new OTP."
            }, 400

        # Verify the supplied OTP
        if not check_password_hash(otp_hash, otp):
            return {
                "status": "error",
                "message": "The OTP is incorrect. Please enter the correct OTP."
            }, 400

        # Check whether the OTP has expired
        if datetime.utcnow() >= otp_expiry:
            staff_collection.update_one(
                {"staff_id": staff_id},
                {
                    "$unset": {
                        "password_reset_otp_hash": "",
                        "password_reset_otp_expires_at": "",
                        "password_reset_otp_created_at": ""
                    }
                }
            )

            return {
                "status": "error",
                "message": "The OTP has expired. Request a new password-reset OTP."
            }, 400

        # Validate the new password
        if len(new_password) < 8:
            return {
                "status": "error",
                "message": "The new password must contain at least 8 characters."
            }, 400

        # Update the password and invalidate the OTP
        staff_collection.update_one(
            {"staff_id": staff_id},
            {
                "$set": {
                    "password": generate_password_hash(new_password)
                },
                "$unset": {
                    "password_reset_otp_hash": "",
                    "password_reset_otp_expires_at": "",
                    "password_reset_otp_created_at": ""
                }
            }
        )

        # Send notification to the email registered to this staff account
        try:
            EmailSender.send_staff_password_changed_email(
                receiver_email=staff["email"],
                staff_name=staff.get(
                    "name",
                    staff.get("staff_id", "Staff")
                )
            )
        except Exception:
            return {
                "status": "success",
                "message": "Password reset successfully, but the notification email could not be sent."
            }, 200

        return {
            "status": "success",
            "message": f"Password reset successfully for Staff ID '{staff_id}'. You can now log in with your new password."
        }, 200


# ==========================================================
# REGISTER STAFF RESET PASSWORD WITH OTP ENDPOINT
# ==========================================================

api.add_resource(
    OTPResetStaffPassword,
    "/api/v1/clearance/otp-reset-password/staff"
)




# ==========================================================
# CHANGE STAFF PASSWORD AND SEND EMAIL NOTIFICATION
# Finds the staff account using staff_id, verifies the
# current password, securely updates it, and sends a password
# change notification using the staff member's actual name.
# ==========================================================

class ChangeStaffPassword(Resource):

    def post(self):

        # ---------- Define request fields ----------
        parser = reqparse.RequestParser()

        parser.add_argument(
            "staff_id",
            type=str,
            required=True,
            help="Staff ID is required."
        )

        parser.add_argument(
            "current_password",
            type=str,
            required=True,
            help="Current password is required."
        )

        parser.add_argument(
            "new_password",
            type=str,
            required=True,
            help="New password is required."
        )

        args = parser.parse_args()

        # ---------- Clean input ----------
        staff_id = (args.get("staff_id") or "").strip().upper()
        current_password = args.get("current_password") or ""
        new_password = args.get("new_password") or ""

        # ---------- Validate required fields ----------
        if not staff_id:
            return {
                "status": "error",
                "message": "Staff ID is required."
            }, 400

        if not current_password:
            return {
                "status": "error",
                "message": "Current password is required."
            }, 400

        if not new_password:
            return {
                "status": "error",
                "message": "New password is required."
            }, 400

        staff_collection = mongo.db.staff

        # ---------- Find staff account ----------
        try:
            staff = staff_collection.find_one({
                "staff_id": staff_id
            })

        except Exception as e:
            print(f"Staff lookup database error: {e}")

            return {
                "status": "error",
                "message": (
                    "Unable to retrieve the staff account. "
                    "Please try again."
                )
            }, 500

        # ---------- Confirm staff account exists ----------
        if not staff:
            return {
                "status": "error",
                "message": (
                    f"No staff account was found with "
                    f"Staff ID '{staff_id}'."
                )
            }, 404

        # ---------- Check staff account status ----------
        if staff.get("account_status") != "active":
            return {
                "status": "error",
                "message": (
                    "This staff account is not active. "
                    "Contact the system administrator."
                )
            }, 403

        # ---------- Confirm that a password exists ----------
        stored_password = staff.get("password")

        if not stored_password:
            return {
                "status": "error",
                "message": (
                    "No password is configured for this staff "
                    "account. Contact the system administrator."
                )
            }, 400

        # ---------- Verify current password ----------
        try:
            password_valid = check_password_hash(
                stored_password,
                current_password
            )

        except (ValueError, TypeError) as e:
            print(f"Current password verification error: {e}")

            return {
                "status": "error",
                "message": (
                    "Unable to verify the current password. "
                    "Please contact the system administrator."
                )
            }, 500

        if not password_valid:
            return {
                "status": "error",
                "message": "The current password is incorrect."
            }, 401

        # ---------- Validate new password ----------
        if len(new_password) < 8:
            return {
                "status": "error",
                "message": (
                    "The new password must contain at least "
                    "8 characters."
                )
            }, 400

        # ---------- Prevent reuse of current password ----------
        try:
            if check_password_hash(
                stored_password,
                new_password
            ):
                return {
                    "status": "error",
                    "message": (
                        "The new password must be different "
                        "from the current password."
                    )
                }, 400

        except (ValueError, TypeError) as e:
            print(f"New password validation error: {e}")

            return {
                "status": "error",
                "message": (
                    "Unable to validate the new password. "
                    "Please try again."
                )
            }, 500

        # ---------- Confirm registered email ----------
        receiver_email = (
            staff.get("email") or ""
        ).strip()

        if not receiver_email:
            return {
                "status": "error",
                "message": (
                    "Password was not changed because no "
                    "registered email address was found "
                    "for this staff account."
                )
            }, 400

        # ---------- Prepare password update ----------
        try:
            hashed_password = generate_password_hash(
                new_password
            )

            current_time = datetime.now(timezone.utc)

        except Exception as e:
            print(f"New password hashing error: {e}")

            return {
                "status": "error",
                "message": (
                    "Unable to prepare the new password. "
                    "The password has not been changed."
                )
            }, 500

        # ---------- Update password securely ----------
        try:
            result = staff_collection.update_one(
                {
                    "_id": staff["_id"],
                    "password": stored_password,
                    "account_status": "active"
                },
                {
                    "$set": {
                        "password": hashed_password,
                        "password_changed_at": current_time,
                        "must_change_password": False
                    }
                }
            )

        except Exception as e:
            print(f"Password update database error: {e}")

            return {
                "status": "error",
                "message": (
                    "A database error prevented the password "
                    "change. Please try again."
                )
            }, 500

        # ---------- Confirm database update ----------
        if result.matched_count != 1:
            return {
                "status": "error",
                "message": (
                    "The password was not changed because the "
                    "staff account or password record changed "
                    "during the request. Please try again."
                )
            }, 409

        if result.modified_count != 1:
            return {
                "status": "error",
                "message": (
                    "The database did not confirm the password "
                    "change. Please verify your login before "
                    "retrying."
                )
            }, 500

        # ---------- Get the staff member's actual name ----------
        first_name = (
            staff.get("first_name") or ""
        ).strip()

        surname = (
            staff.get("surname") or ""
        ).strip()

        staff_name = " ".join(
            part for part in [first_name, surname] if part
        )

        # Do not use staff_id as the person's name.
        if not staff_name:
            staff_name = "Staff Member"

        # ---------- Send password-change notification ----------
        try:
            email_sent = (
                EmailSender.send_staff_password_changed_email(
                    receiver_email=receiver_email,
                    staff_name=staff_name
                )
            )

        except Exception as e:
            print(
                f"Staff password-change email error "
                f"for {staff_id}: {e}"
            )

            email_sent = False

        # ---------- Return success response ----------
        if not email_sent:
            return {
                "status": "success",
                "message": (
                    "Password changed successfully, but the "
                    "notification email could not be sent. "
                    "Please check the email configuration."
                ),
                "data": {
                    "staff_id": staff_id,
                    "password_changed": True,
                    "notification_sent": False
                }
            }, 200

        return {
            "status": "success",
            "message": (
                "Password changed successfully. A confirmation "
                "email has been sent to your registered email "
                "address."
            ),
            "data": {
                "staff_id": staff_id,
                "password_changed": True,
                "notification_sent": True
            }
        }, 200


# ==========================================================
# REGISTER STAFF CHANGE PASSWORD ENDPOINT
# ==========================================================

api.add_resource(
    ChangeStaffPassword,
    "/api/v1/clearance/change-password/staff"
)





# ==========================================================
# STAFF APPROVE OR REJECT CLEARANCE STAGE
# Approves or rejects a student's submitted clearance stage.
# Only stages with status "under_review" can be reviewed.
# Rejection requires a comment and notifies the student.
# Resubmitted rejected stages can be reviewed again.
# Approval generates an OTP for the next stage when required.
# OTP has no expiry and remains valid until used or invalidated.
# Final-stage approval marks the clearance as completed.
# Register this endpoint only once.
# ==========================================================

class StaffApproveRejectClearanceStage(Resource):

    # ======================================================
    # INITIALIZE REQUEST PARSER
    # ======================================================

    def __init__(self):
        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "staff_id",
            type=str,
            required=True,
            help="Staff ID is required."
        )

        self.parser.add_argument(
            "reg_no",
            type=str,
            required=True,
            help="Student registration number is required."
        )

        self.parser.add_argument(
            "action",
            type=str,
            required=True,
            choices=("approve", "reject"),
            help="Action must be either approve or reject."
        )

        self.parser.add_argument(
            "comment",
            type=str,
            required=False,
            default=""
        )

    # ======================================================
    # APPROVE OR REJECT CLEARANCE STAGE
    # ======================================================

    def post(self):
        args = self.parser.parse_args()

        staff_id = args["staff_id"].strip()
        reg_no = args["reg_no"].strip().upper()
        action = args["action"].strip().lower()
        comment = (args.get("comment") or "").strip()

        # IMPORTANT:
        # This sequence must match the stage sequence used by
        # the clearance creation, upload, and OTP endpoints.
        stages = [
            "department",
            "finance",
            "library",
            "alumni",
            "student_affairs",
            "health",
            "security",
            "audit"
        ]

        # --------------------------------------------------
        # 1. VALIDATE REJECTION COMMENT
        # --------------------------------------------------

        if action == "reject" and not comment:
            return {
                "success": False,
                "message": (
                    "A rejection comment is required. "
                    "Explain why the clearance stage is being rejected."
                )
            }, 400

        if len(comment) > 1000:
            return {
                "success": False,
                "message": "The comment cannot exceed 1000 characters."
            }, 400

        # --------------------------------------------------
        # 2. VALIDATE STAFF ACCOUNT
        # --------------------------------------------------

        staff = mongo.db.staff.find_one({
            "staff_id": staff_id
        })

        if not staff:
            return {
                "success": False,
                "message": "Staff account was not found."
            }, 404

        if staff.get("account_status") != "active":
            return {
                "success": False,
                "message": "Staff account is not active."
            }, 403

        # --------------------------------------------------
        # 3. VALIDATE STUDENT ACCOUNT
        # --------------------------------------------------

        student = mongo.db.students.find_one({
            "reg_no": reg_no
        })

        if not student:
            return {
                "success": False,
                "message": (
                    f"No student account was found for {reg_no}."
                )
            }, 404

        student_email = student.get("email")

        student_name = " ".join(
            str(student.get(field, "")).strip()
            for field in ("first_name", "other_names", "surname")
            if student.get(field)
        ).strip()

        if not student_name:
            student_name = reg_no

        if not student_email:
            return {
                "success": False,
                "message": (
                    "The student account has no email address. "
                    "The clearance stage cannot be processed "
                    "because the notification recipient is missing."
                )
            }, 400

        # --------------------------------------------------
        # 4. FIND CLEARANCE RECORD
        # --------------------------------------------------

        clearance = mongo.db.clearances.find_one({
            "reg_no": reg_no
        })

        if not clearance:
            return {
                "success": False,
                "message": (
                    "The student account exists, but clearance "
                    "has not been started."
                )
            }, 404

        stage = str(
            clearance.get("current_stage", "")
        ).strip().lower()

        if stage not in stages:
            return {
                "success": False,
                "message": (
                    f"The current clearance stage '{stage}' "
                    "is invalid or is not included in the configured "
                    "clearance stage sequence."
                ),
                "configured_stages": stages
            }, 400

        # --------------------------------------------------
        # 5. VERIFY STAFF ASSIGNMENT
        # --------------------------------------------------

        assigned_stage = str(
            staff.get("assigned_stage", "")
        ).strip().lower()

        if assigned_stage != stage:
            return {
                "success": False,
                "message": (
                    f"This staff member is assigned to "
                    f"'{assigned_stage or 'no stage'}', but the "
                    f"student is currently at '{stage}'. "
                    "Only staff assigned to the current stage "
                    "can review it."
                ),
                "assigned_stage": assigned_stage or None,
                "student_current_stage": stage
            }, 403

        # --------------------------------------------------
        # 6. CHECK CURRENT STAGE STATUS
        # --------------------------------------------------

        stage_data = (
            clearance.get("stages", {}).get(stage, {})
        )

        stage_status = str(
            stage_data.get("status", "pending")
        ).strip().lower()

        if stage_status == "approved":
            return {
                "success": False,
                "message": (
                    f"The '{stage}' stage has already been approved. "
                    "It cannot be reviewed again."
                ),
                "stage": stage,
                "stage_status": "approved"
            }, 409

        if stage_status == "rejected":
            return {
                "success": False,
                "message": (
                    f"The '{stage}' stage is currently rejected. "
                    "The student must correct the issue and "
                    "resubmit the required document(s). The upload "
                    "endpoint must reset the stage status to "
                    "'under_review' after successful resubmission."
                ),
                "stage": stage,
                "stage_status": "rejected",
                "previous_rejection_comment": stage_data.get(
                    "comment", ""
                ),
                "resubmission_required": True
            }, 409

        if stage_status != "under_review":
            return {
                "success": False,
                "message": (
                    f"The '{stage}' stage cannot be reviewed because "
                    f"its current status is '{stage_status}'. "
                    "The student must successfully upload or "
                    "resubmit the required document(s) first."
                ),
                "stage": stage,
                "stage_status": stage_status,
                "required_status": "under_review"
            }, 409

        # --------------------------------------------------
        # 7. PREPARE REVIEW TIMESTAMP
        # --------------------------------------------------

        current_time = datetime.utcnow()

        # Only under_review stages can be processed.
        eligible_statuses = ["under_review"]

        # --------------------------------------------------
        # 8. PROCESS REJECTION
        # --------------------------------------------------

        if action == "reject":

            update_result = mongo.db.clearances.update_one(
                {
                    "_id": clearance["_id"],
                    "current_stage": stage,
                    f"stages.{stage}.status": {
                        "$in": eligible_statuses
                    }
                },
                {
                    "$set": {
                        f"stages.{stage}.status": "rejected",
                        f"stages.{stage}.comment": comment,
                        f"stages.{stage}.reviewed_by": staff_id,
                        f"stages.{stage}.reviewed_at": current_time,
                        "updated_at": current_time
                    }
                }
            )

            if update_result.modified_count != 1:
                return {
                    "success": False,
                    "message": (
                        "The rejection was not saved. The stage may "
                        "have changed or been reviewed by another "
                        "process. Reload the clearance record and "
                        "check its current status before retrying."
                    )
                }, 409

            # Invalidate unused OTPs associated with this stage.
            mongo.db.stage_otps.update_many(
                {
                    "reg_no": reg_no,
                    "stage": stage,
                    "status": "unused"
                },
                {
                    "$set": {
                        "status": "invalidated",
                        "invalidated_at": current_time
                    }
                }
            )

            # Send rejection notification.
            email_sent = False

            try:
                email_result = (
                    EmailSender
                    .send_student_clearance_stage_rejected_email(
                        receiver_email=student_email,
                        student_name=student_name,
                        reg_no=reg_no,
                        stage=stage,
                        rejection_comment=comment
                    )
                )

                email_sent = email_result is True

            except Exception as e:
                print(
                    f"Rejection email error: "
                    f"{type(e).__name__}: {e}"
                )

            return {
                "success": True,
                "message": (
                    f"The '{stage}' clearance stage has been rejected. "
                    "The rejection reason has been saved. Please "
                    "correct the issue and resubmit the required "
                    "document(s) for another review."
                ),
                "reg_no": reg_no,
                "stage": stage,
                "stage_status": "rejected",
                "rejection_comment": comment,
                "reviewed_by": staff_id,
                "reviewed_at": current_time.isoformat(),
                "resubmission_required": True,
                "email_sent": email_sent,
                "email_status": (
                    "Rejection notification accepted by SMTP."
                    if email_sent
                    else (
                        "The rejection was saved, but the email "
                        "could not be confirmed as sent. Check "
                        "your email configuration and logs."
                    )
                )
            }, 200

        # --------------------------------------------------
        # 9. DETERMINE NEXT STAGE AND GENERATE OTP
        # OTP does not expire; it remains valid until used
        # or invalidated.
        # --------------------------------------------------

        current_index = stages.index(stage)

        next_stage = (
            stages[current_index + 1]
            if current_index < len(stages) - 1
            else None
        )

        otp = None
        otp_expiry = None

        if next_stage is not None:
            otp = f"{secrets.randbelow(1000000):06d}"

        # --------------------------------------------------
        # 10. SAVE APPROVAL
        # --------------------------------------------------

        approval_fields = {
            f"stages.{stage}.status": "approved",
            f"stages.{stage}.reviewed_by": staff_id,
            f"stages.{stage}.reviewed_at": current_time,
            "updated_at": current_time
        }

        if next_stage is None:
            approval_fields["status"] = "completed"
            approval_fields["completed_at"] = current_time

        update_result = mongo.db.clearances.update_one(
            {
                "_id": clearance["_id"],
                "current_stage": stage,
                f"stages.{stage}.status": {
                    "$in": eligible_statuses
                }
            },
            {
                "$set": approval_fields
            }
        )

        if update_result.modified_count != 1:
            return {
                "success": False,
                "message": (
                    "The approval was not saved. The stage may have "
                    "changed during review. Reload the clearance "
                    "record and check its current status."
                )
            }, 409

        # --------------------------------------------------
        # 11. STORE OTP FOR THE NEXT STAGE
        # OTP has no expiry time.
        # --------------------------------------------------

        if next_stage is not None:
            try:
                mongo.db.stage_otps.insert_one({
                    "reg_no": reg_no,
                    "stage": stage,
                    "next_stage": next_stage,
                    "otp": otp,
                    "status": "unused",
                    "created_at": current_time,
                    "expires_at": None
                })

            except Exception as e:
                print(
                    f"Next-stage OTP storage error: "
                    f"{type(e).__name__}: {e}"
                )

                return {
                    "success": True,
                    "message": (
                        f"The '{stage}' stage was approved, but the "
                        "OTP for the next stage could not be stored. "
                        "The approval was saved, but administrative "
                        "attention is required before the student "
                        "can continue."
                    ),
                    "reg_no": reg_no,
                    "stage": stage,
                    "stage_status": "approved",
                    "clearance_completed": False,
                    "next_stage": next_stage,
                    "otp_generated": False,
                    "email_sent": False
                }, 500

        # --------------------------------------------------
        # 12. SEND APPROVAL / COMPLETION EMAIL
        # The email helper must support next_stage=None and
        # otp=None for final-stage completion.
        # --------------------------------------------------

        email_sent = False

        try:
            email_result = (
                EmailSender
                .send_student_clearance_stage_approved_email(
                    receiver_email=student_email,
                    student_name=student_name,
                    reg_no=reg_no,
                    stage=stage,
                    next_stage=next_stage,
                    otp=otp,
                    otp_expiry_minutes=None
                )
            )

            email_sent = email_result is True

        except Exception as e:
            print(
                f"Approval email error: "
                f"{type(e).__name__}: {e}"
            )

        # --------------------------------------------------
        # 13. RETURN FINAL CLEARANCE COMPLETION MESSAGE
        # --------------------------------------------------

        if next_stage is None:
            return {
                "success": True,
                "message": (
                    "Congratulations! Your clearance has been "
                    "completed successfully. This was the final "
                    "clearance stage, and there are no further "
                    "stages to complete."
                ),
                "reg_no": reg_no,
                "stage": stage,
                "stage_status": "approved",
                "clearance_status": "completed",
                "clearance_completed": True,
                "next_stage": None,
                "otp_generated": False,
                "email_sent": email_sent,
                "email_status": (
                    "Clearance completion notification accepted by SMTP."
                    if email_sent
                    else (
                        "Clearance was completed successfully, but "
                        "the email could not be confirmed as sent. "
                        "Check your email configuration and logs."
                    )
                )
            }, 200

        # --------------------------------------------------
        # 14. RETURN APPROVAL AND OTP MESSAGE
        # --------------------------------------------------

        return {
            "success": True,
            "message": (
                f"The '{stage}' clearance stage has been approved. "
                f"An OTP has been generated for the next stage: "
                f"'{next_stage}'. The OTP does not expire and "
                "remains valid until it is used or invalidated. "
                "Check your email to continue your clearance."
            ),
            "reg_no": reg_no,
            "stage": stage,
            "stage_status": "approved",
            "clearance_completed": False,
            "next_stage": next_stage,
            "otp_generated": otp is not None,
            "otp_expiry_minutes": None,
            "otp_expiry": "No expiry; valid until used or invalidated",
            "email_sent": email_sent,
            "email_status": (
                "Approval notification accepted by SMTP."
                if email_sent
                else (
                    "The stage was approved, but the email could "
                    "not be confirmed as sent. Check your email "
                    "configuration and logs."
                )
            )
        }, 200


# ==========================================================
# REGISTER STAFF APPROVE / REJECT CLEARANCE ENDPOINT
# Register this resource only once in your application.
# ==========================================================

api.add_resource(
    StaffApproveRejectClearanceStage,
    "/api/v1/clearance/staff/review-stage"
)



# ==========================================================
# STAFF VERIFY CLEARANCE STAGE OTP
#
# Verifies a student's clearance OTP.
# Confirms that the staff member is registered, active,
# and authorized to verify the target stage.
# Advances the clearance after successful verification.
# Notifies the student by email of the new stage.
#
# OTP does not expire.
# OTP can only be used once.
# ==========================================================


class StaffVerifyStageOTP(Resource):

    # ======================================================
    # INITIALIZE REQUEST PARSER
    # ======================================================

    def __init__(self):
        self.parser = reqparse.RequestParser()

        self.parser.add_argument(
            "staff_id",
            type=str,
            required=True,
            help="Staff ID is required."
        )

        self.parser.add_argument(
            "reg_no",
            type=str,
            required=True,
            help="Student registration number is required."
        )

        self.parser.add_argument(
            "otp",
            type=str,
            required=True,
            help="The clearance OTP is required."
        )

    # ======================================================
    # VERIFY OTP AND ADVANCE CLEARANCE
    # ======================================================

    def post(self):
        args = self.parser.parse_args()

        staff_id = args["staff_id"].strip()
        reg_no = args["reg_no"].strip().upper()
        otp = args["otp"].strip()

        # --------------------------------------------------
        # 1. DEFINE CLEARANCE STAGE SEQUENCE
        # --------------------------------------------------

        stages = [
            "department",
            "finance",
            "library",
            "alumni",
            "student_affairs",
            "health",
            "security",
            "audit"
        ]

        # --------------------------------------------------
        # 2. VALIDATE OTP FORMAT
        # --------------------------------------------------

        if len(otp) != 6 or not otp.isdigit():
            return {
                "success": False,
                "error_code": "INVALID_OTP_FORMAT",
                "message": "The OTP must contain exactly 6 digits."
            }, 400

        # --------------------------------------------------
        # 3. VERIFY STAFF REGISTRATION
        # --------------------------------------------------

        staff = mongo.db.staff.find_one({
            "staff_id": staff_id
        })

        if not staff:
            return {
                "success": False,
                "error_code": "STAFF_NOT_FOUND",
                "message": (
                    f"No registered staff account was found "
                    f"for staff ID '{staff_id}'."
                )
            }, 404

        # --------------------------------------------------
        # 4. VERIFY STAFF ACCOUNT STATUS
        # --------------------------------------------------

        if staff.get("account_status") != "active":
            return {
                "success": False,
                "error_code": "STAFF_ACCOUNT_INACTIVE",
                "message": (
                    "Your staff account is not active. "
                    "Contact the system administrator."
                )
            }, 403

        # --------------------------------------------------
        # 5. VERIFY STAFF STAGE ASSIGNMENT
        # --------------------------------------------------

        assigned_stage = str(
            staff.get("assigned_stage", "")
        ).strip().lower()

        if not assigned_stage:
            return {
                "success": False,
                "error_code": "STAFF_STAGE_NOT_ASSIGNED",
                "message": (
                    "Your staff account has no assigned "
                    "clearance stage."
                )
            }, 403

        if assigned_stage not in stages:
            return {
                "success": False,
                "error_code": "INVALID_STAFF_STAGE",
                "message": (
                    f"Your assigned stage '{assigned_stage}' "
                    "is not recognized by the clearance workflow."
                )
            }, 403

        # --------------------------------------------------
        # 6. VERIFY STUDENT REGISTRATION
        # --------------------------------------------------

        student = mongo.db.students.find_one({
            "reg_no": reg_no
        })

        if not student:
            return {
                "success": False,
                "error_code": "STUDENT_NOT_FOUND",
                "message": (
                    f"No student account was found for {reg_no}."
                )
            }, 404

        # --------------------------------------------------
        # 7. FIND CLEARANCE RECORD
        # --------------------------------------------------

        clearance = mongo.db.clearances.find_one({
            "reg_no": reg_no
        })

        if not clearance:
            return {
                "success": False,
                "error_code": "CLEARANCE_NOT_FOUND",
                "message": (
                    "The student has not started clearance."
                )
            }, 404

        current_stage = str(
            clearance.get("current_stage", "")
        ).strip().lower()

        if current_stage not in stages:
            return {
                "success": False,
                "error_code": "INVALID_CURRENT_STAGE",
                "message": (
                    f"The student's current stage "
                    f"'{current_stage}' is not recognized."
                )
            }, 409

        # --------------------------------------------------
        # 8. FIND OTP WITHOUT FILTERING BY STAFF STAGE
        # --------------------------------------------------

        otp_record = mongo.db.stage_otps.find_one({
            "reg_no": reg_no,
            "otp": otp
        })

        if not otp_record:
            return {
                "success": False,
                "error_code": "OTP_NOT_FOUND",
                "message": (
                    "The OTP does not exist for this student's "
                    "clearance. Check the registration number "
                    "and OTP entered."
                )
            }, 400

        # --------------------------------------------------
        # 9. CHECK OTP STATUS
        # --------------------------------------------------

        otp_status = otp_record.get("status")

        if otp_status == "used":
            return {
                "success": False,
                "error_code": "OTP_ALREADY_USED",
                "message": (
                    "This OTP has already been used and "
                    "cannot be verified again."
                )
            }, 409

        if otp_status != "unused":
            return {
                "success": False,
                "error_code": "OTP_NOT_AVAILABLE",
                "message": (
                    f"This OTP cannot be verified because "
                    f"its status is '{otp_status}'."
                )
            }, 409

        # --------------------------------------------------
        # 10. READ OTP STAGE INFORMATION
        # --------------------------------------------------

        previous_stage = str(
            otp_record.get("stage", "")
        ).strip().lower()

        next_stage = str(
            otp_record.get("next_stage", "")
        ).strip().lower()

        if not previous_stage or not next_stage:
            return {
                "success": False,
                "error_code": "OTP_STAGE_MISSING",
                "message": (
                    "The OTP record is missing its stage "
                    "information. Contact the administrator."
                )
            }, 400

        if (
            previous_stage not in stages
            or next_stage not in stages
        ):
            return {
                "success": False,
                "error_code": "INVALID_OTP_STAGE",
                "message": (
                    f"The OTP references an invalid stage. "
                    f"Previous: '{previous_stage}', "
                    f"next: '{next_stage}'."
                )
            }, 400

        # --------------------------------------------------
        # 11. AUTHORIZE STAFF FOR THE TARGET STAGE
        # --------------------------------------------------

        if assigned_stage != next_stage:
            return {
                "success": False,
                "error_code": "UNAUTHORIZED_STAGE",
                "message": (
                    f"Unauthorized staff: this OTP is for "
                    f"the '{next_stage}' stage, but your "
                    f"assigned stage is '{assigned_stage}'. "
                    f"Only staff assigned to '{next_stage}' "
                    "can verify this OTP."
                ),
                "staff_id": staff_id,
                "staff_assigned_stage": assigned_stage,
                "otp_next_stage": next_stage
            }, 403

        # --------------------------------------------------
        # 12. VALIDATE STAGE TRANSITION
        # --------------------------------------------------

        previous_index = stages.index(previous_stage)

        expected_next_stage = (
            stages[previous_index + 1]
            if previous_index < len(stages) - 1
            else None
        )

        if next_stage != expected_next_stage:
            return {
                "success": False,
                "error_code": "INVALID_STAGE_TRANSITION",
                "message": (
                    f"The transition from '{previous_stage}' "
                    f"to '{next_stage}' does not match the "
                    "configured clearance stage sequence."
                )
            }, 400

        # --------------------------------------------------
        # 13. CHECK STUDENT CURRENT STAGE
        # --------------------------------------------------

        if current_stage != previous_stage:
            return {
                "success": False,
                "error_code": "CLEARANCE_STAGE_MISMATCH",
                "message": (
                    f"The student's current stage is "
                    f"'{current_stage}', but this OTP expects "
                    f"'{previous_stage}' as the previous stage."
                ),
                "student_current_stage": current_stage,
                "otp_previous_stage": previous_stage
            }, 409

        # --------------------------------------------------
        # 14. CONFIRM PREVIOUS STAGE WAS APPROVED
        # --------------------------------------------------

        previous_stage_data = (
            clearance.get("stages", {}).get(previous_stage, {})
        )

        if previous_stage_data.get("status") != "approved":
            return {
                "success": False,
                "error_code": "PREVIOUS_STAGE_NOT_APPROVED",
                "message": (
                    f"The '{previous_stage}' stage has not "
                    "been approved. The OTP cannot be used."
                )
            }, 409

        # --------------------------------------------------
        # 15. CLAIM OTP TO PREVENT DOUBLE VERIFICATION
        # --------------------------------------------------

        current_time = datetime.utcnow()

        claimed_otp = mongo.db.stage_otps.update_one(
            {
                "_id": otp_record["_id"],
                "status": "unused"
            },
            {
                "$set": {
                    "status": "verifying",
                    "verification_started_at": current_time,
                    "verified_by": staff_id
                }
            }
        )

        if claimed_otp.modified_count != 1:
            return {
                "success": False,
                "error_code": "OTP_ALREADY_PROCESSING",
                "message": (
                    "This OTP is already being processed "
                    "or has already been used."
                )
            }, 409

        # --------------------------------------------------
        # 16. ADVANCE CLEARANCE
        # --------------------------------------------------

        try:
            update_result = mongo.db.clearances.update_one(
                {
                    "_id": clearance["_id"],
                    "current_stage": previous_stage,
                    f"stages.{previous_stage}.status": "approved"
                },
                {
                    "$set": {
                        "current_stage": next_stage,
                        "updated_at": current_time
                    }
                }
            )

            if update_result.modified_count != 1:

                mongo.db.stage_otps.update_one(
                    {
                        "_id": otp_record["_id"],
                        "status": "verifying"
                    },
                    {
                        "$set": {
                            "status": "unused"
                        },
                        "$unset": {
                            "verification_started_at": "",
                            "verified_by": ""
                        }
                    }
                )

                return {
                    "success": False,
                    "error_code": "CLEARANCE_ADVANCEMENT_FAILED",
                    "message": (
                        "The clearance could not be advanced. "
                        "Reload the clearance record and retry."
                    )
                }, 409

            # ------------------------------------------------
            # 17. MARK OTP AS USED
            # ------------------------------------------------

            used_result = mongo.db.stage_otps.update_one(
                {
                    "_id": otp_record["_id"],
                    "status": "verifying"
                },
                {
                    "$set": {
                        "status": "used",
                        "used_at": datetime.utcnow(),
                        "verified_by": staff_id
                    },
                    "$unset": {
                        "verification_started_at": ""
                    }
                }
            )

            if used_result.modified_count != 1:
                print(
                    "WARNING: Clearance advanced, but OTP "
                    f"could not be marked used for {reg_no}."
                )

                return {
                    "success": True,
                    "message": (
                        "OTP verified and clearance advanced, "
                        "but OTP status finalization failed."
                    ),
                    "reg_no": reg_no,
                    "previous_stage": previous_stage,
                    "current_stage": next_stage,
                    "otp_status_warning": True
                }, 200

        except Exception as e:

            print(
                f"Stage OTP verification error: "
                f"{type(e).__name__}: {e}"
            )

            latest_clearance = mongo.db.clearances.find_one({
                "_id": clearance["_id"]
            })

            if (
                latest_clearance
                and latest_clearance.get("current_stage")
                == previous_stage
            ):
                mongo.db.stage_otps.update_one(
                    {
                        "_id": otp_record["_id"],
                        "status": "verifying"
                    },
                    {
                        "$set": {
                            "status": "unused"
                        },
                        "$unset": {
                            "verification_started_at": "",
                            "verified_by": ""
                        }
                    }
                )

            return {
                "success": False,
                "error_code": "OTP_VERIFICATION_ERROR",
                "message": (
                    "An unexpected error occurred during OTP "
                    "verification. Check the clearance and OTP "
                    "records before retrying."
                )
            }, 500

        # --------------------------------------------------
        # 18. NOTIFY STUDENT BY EMAIL
        # --------------------------------------------------

        email_sent = False

        try:
            student_email = (
                student.get("email") or ""
            ).strip()

            student_name = " ".join(
                str(part).strip()
                for part in [
                    student.get("first_name", ""),
                    student.get("surname", "")
                ]
                if part and str(part).strip()
            )

            if student_email:
                email_sent = bool(
                    EmailSender
                    .send_student_clearance_stage_otp_verified_email(
                        receiver_email=student_email,
                        student_name=student_name or "Student",
                        reg_no=reg_no,
                        previous_stage=previous_stage,
                        current_stage=next_stage
                    )
                )

            else:
                print(
                    f"Student email is missing for {reg_no}. "
                    "Clearance advanced without email notification."
                )

        except Exception as e:
            print(
                "Student notification error: "
                f"{type(e).__name__}: {e}"
            )

        # --------------------------------------------------
        # 19. RETURN SUCCESS RESPONSE
        # --------------------------------------------------

        return {
            "success": True,
            "message": (
                f"OTP verified successfully. The student's "
                f"clearance has advanced from '{previous_stage}' "
                f"to '{next_stage}'."
            ),
            "reg_no": reg_no,
            "previous_stage": previous_stage,
            "current_stage": next_stage,
            "otp_verified": True,
            "otp_status": "used",
            "verified_by": staff_id,
            "notification": {
                "type": "email",
                "email_sent": email_sent,
                "message": (
                    "Notification email sent successfully."
                    if email_sent
                    else (
                        "Clearance advanced successfully, but "
                        "the notification email could not be sent."
                    )
                )
            }
        }, 200


# ==========================================================
# REGISTER ENDPOINT ONLY ONCE
# ==========================================================

api.add_resource(
    StaffVerifyStageOTP,
    "/api/v1/clearance/staff/verify-stage-otp"
)
