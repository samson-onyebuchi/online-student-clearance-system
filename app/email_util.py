
# ==========================================================
# EMAIL UTILITIES
# Handles student registration, password OTP, password changes,
# staff onboarding, staff forgot-password OTP, staff password
# changes, and student clearance approval/rejection emails.
# Students use IMAGE_URL; staff use LECTURER_IMAGE_URL.
# ==========================================================

import smtplib
import ssl
import html

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config


# ==========================================================
# EMAIL CONFIGURATION
# ==========================================================

SMTP_SERVER = Config.SMTP_SERVER
SMTP_PORT = int(Config.SMTP_PORT)

EMAIL_USERNAME = Config.EMAIL_USERNAME
EMAIL_PASSWORD = Config.EMAIL_PASSWORD

IMAGE_URL = getattr(Config, "IMAGE_URL", "")
LECTURER_IMAGE_URL = getattr(Config, "LECTURER_IMAGE_URL", "")


# ==========================================================
# EMAIL SENDER
# ==========================================================

class EmailSender:

    # ======================================================
    # COMMON EMAIL SENDING FUNCTION
    # Used by both students and staff.
    # ======================================================

    @staticmethod
    def _send_html_email(
        receiver_email,
        subject,
        heading,
        body_html,
        image_url=""
    ):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = EMAIL_USERNAME
            msg["To"] = receiver_email

            plain_text = (
                f"{subject}\n\n"
                f"{heading}\n\n"
                "Please view this message in an "
                "HTML-compatible email application."
            )

            msg.attach(MIMEText(plain_text, "plain", "utf-8"))

            safe_subject = html.escape(str(subject))
            safe_heading = html.escape(str(heading))

            logo_html = ""

            if image_url:
                safe_image_url = html.escape(
                    image_url,
                    quote=True
                )

                logo_html = f"""
                    <div style="text-align:center;margin-bottom:15px;">
                        <img src="{safe_image_url}"
                             alt="Clearance System Logo"
                             style="max-width:180px;max-height:100px;
                                    width:auto;height:auto;">
                    </div>
                """

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{safe_subject}</title>
            </head>
            <body style="margin:0;padding:20px;background:#f4f6f8;
                         font-family:Arial,Helvetica,sans-serif;">

                <div style="max-width:600px;margin:20px auto;
                            background:#ffffff;border-radius:10px;
                            overflow:hidden;border:1px solid #eeeeee;">

                    <div style="background:#1b5e20;color:#ffffff;
                                padding:25px;text-align:center;">
                        {logo_html}
                        <h2>Student Clearance System</h2>
                    </div>

                    <div style="padding:30px;color:#333333;
                                line-height:1.7;">
                        <h3>{safe_heading}</h3>
                        {body_html}

                        <hr style="border:none;
                                   border-top:1px solid #eeeeee;
                                   margin:25px 0;">

                        <p style="font-size:12px;color:#888888;
                                  text-align:center;">
                            This is an automated email.
                            Please do not reply directly.
                        </p>
                    </div>

                    <div style="background:#f8f8f8;padding:15px;
                                text-align:center;font-size:12px;
                                color:#888888;">
                        Student Clearance System
                    </div>

                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_body, "html", "utf-8"))

            if SMTP_PORT == 465:
                with smtplib.SMTP_SSL(
                    SMTP_SERVER,
                    SMTP_PORT,
                    context=ssl.create_default_context()
                ) as server:
                    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                    server.send_message(msg)

            else:
                with smtplib.SMTP(
                    SMTP_SERVER,
                    SMTP_PORT
                ) as server:
                    server.ehlo()

                    server.starttls(
                        context=ssl.create_default_context()
                    )

                    server.ehlo()
                    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                    server.send_message(msg)

            print(
                f"Email accepted by SMTP: "
                f"{receiver_email} | Subject: {subject}"
            )
            return True

        except Exception as e:
            print(
                f"Email sending failed: "
                f"{type(e).__name__}: {e}"
            )
            return False

    # ======================================================
    # STUDENT REGISTRATION EMAIL
    # ======================================================

    @staticmethod
    def send_student_registration_email(
        receiver_email: str,
        student_name: str,
        reg_no: str,
        password: str
    ):
        name = html.escape(str(student_name))
        safe_reg_no = html.escape(str(reg_no))
        safe_password = html.escape(str(password))

        body = f"""
            <p>Hello <strong>{name}</strong>,</p>
            <p>Your student clearance account has been created
               successfully.</p>
            <p><strong>Registration Number:</strong>
               {safe_reg_no}</p>
            <p><strong>Password:</strong> {safe_password}</p>
            <p>Please keep your login details secure.</p>
        """

        return EmailSender._send_html_email(
            receiver_email=receiver_email,
            subject="Student Clearance - Registration Successful",
            heading="Welcome to the Student Clearance System",
            body_html=body,
            image_url=IMAGE_URL
        )

    # ======================================================
    # STUDENT FORGOT PASSWORD OTP EMAIL
    # ======================================================

    @staticmethod
    def send_student_forgot_password_email(
        receiver_email: str,
        student_name: str,
        otp: str
    ):
        name = html.escape(str(student_name))
        safe_otp = html.escape(str(otp))

        body = f"""
            <p>Hello <strong>{name}</strong>,</p>
            <p>Use the verification code below to reset your
               student account password.</p>

            <div style="text-align:center;padding:20px;
                        background:#f1f8e9;border:1px dashed #1b5e20;
                        border-radius:8px;">
                <span style="font-size:28px;font-weight:bold;
                             letter-spacing:6px;color:#1b5e20;">
                    {safe_otp}
                </span>
            </div>

            <p>This code expires in <strong>10 minutes</strong>.</p>
            <p>Do not share this code with anyone.</p>
            <p>If you did not request a password reset,
               you can ignore this email.</p>
        """

        return EmailSender._send_html_email(
            receiver_email=receiver_email,
            subject="Student Clearance - Password Reset OTP",
            heading="Password Reset Request",
            body_html=body,
            image_url=IMAGE_URL
        )

    # ======================================================
    # STAFF FORGOT PASSWORD OTP EMAIL
    # ======================================================

    @staticmethod
    def send_staff_forgot_password_email(
        receiver_email: str,
        staff_name: str,
        otp: str
    ):
        name = html.escape(str(staff_name))
        safe_otp = html.escape(str(otp))

        body = f"""
            <p>Hello <strong>{name}</strong>,</p>
            <p>A password reset was requested for your staff
               account in the Student Clearance System.</p>
            <p>Use the verification code below to reset your
               staff account password.</p>

            <div style="text-align:center;padding:20px;
                        background:#f1f8e9;border:1px dashed #1b5e20;
                        border-radius:8px;">
                <span style="font-size:28px;font-weight:bold;
                             letter-spacing:6px;color:#1b5e20;">
                    {safe_otp}
                </span>
            </div>

            <p>This code expires in <strong>10 minutes</strong>.</p>
            <p>Do not share this code with anyone.</p>
            <p>If you did not request a password reset,
               you can ignore this email and keep your current
               password.</p>
            <p>If you suspect someone is trying to access your
               account, contact the system administrator.</p>
        """

        return EmailSender._send_html_email(
            receiver_email=receiver_email,
            subject="Student Clearance - Staff Password Reset OTP",
            heading="Staff Password Reset Request",
            body_html=body,
            image_url=LECTURER_IMAGE_URL
        )

    # ======================================================
    # STUDENT PASSWORD CHANGED NOTIFICATION EMAIL
    # ======================================================

    @staticmethod
    def send_student_password_changed_email(
        receiver_email: str,
        student_name: str
    ):
        name = html.escape(str(student_name))

        body = f"""
            <p>Hello <strong>{name}</strong>,</p>
            <p>Your student clearance account password has been
               changed successfully.</p>
            <p>You can now log in using your new password.</p>
            <p>If you did not make this change, contact your
               system administrator immediately.</p>
        """

        return EmailSender._send_html_email(
            receiver_email=receiver_email,
            subject="Student Clearance - Password Changed Successfully",
            heading="Password Changed Successfully",
            body_html=body,
            image_url=IMAGE_URL
        )

    # ======================================================
    # STAFF / LECTURER ACCOUNT ONBOARDING EMAIL
    # ======================================================

    @staticmethod
    def send_staff_onboarding_email(
        receiver_email: str,
        staff_name: str,
        staff_id: str,
        role: str,
        temporary_password: str
    ):
        name = html.escape(str(staff_name))
        safe_staff_id = html.escape(str(staff_id))
        safe_role = html.escape(str(role))
        safe_email = html.escape(str(receiver_email))
        safe_password = html.escape(str(temporary_password))

        body = f"""
            <p>Hello <strong>{name}</strong>,</p>
            <p>Your staff account has been created successfully
               in the Student Clearance System.</p>

            <div style="background:#f1f8e9;border:1px solid #c5e1a5;
                        border-radius:8px;padding:20px;margin:20px 0;">
                <p><strong>Staff ID:</strong> {safe_staff_id}</p>
                <p><strong>Assigned Role:</strong> {safe_role}</p>
                <p><strong>Login Email:</strong> {safe_email}</p>
                <p><strong>Temporary Password:</strong>
                   {safe_password}</p>
            </div>

            <p>Please log in using your assigned credentials and
               change your temporary password as soon as possible.</p>
            <p>Keep your login details confidential.</p>
            <p>If you did not expect this account, contact the
               system administrator.</p>
        """

        return EmailSender._send_html_email(
            receiver_email=receiver_email,
            subject="Student Clearance - Staff Account Created",
            heading="Your Staff Account Has Been Created",
            body_html=body,
            image_url=LECTURER_IMAGE_URL
        )

    # ======================================================
    # STAFF PASSWORD CHANGED NOTIFICATION EMAIL
    # ======================================================

    @staticmethod
    def send_staff_password_changed_email(
        receiver_email: str,
        staff_name: str
    ):
        name = html.escape(str(staff_name))

        body = f"""
            <p>Hello <strong>{name}</strong>,</p>
            <p>Your staff account password in the Student
               Clearance System has been changed successfully.</p>
            <p>You can now log in using your new password.</p>
            <p><strong>Security notice:</strong> If you did not
               make this change, contact your system
               administrator immediately.</p>
            <p>For your security, never share your password
               with anyone.</p>
        """

        return EmailSender._send_html_email(
            receiver_email=receiver_email,
            subject="Student Clearance - Staff Password Changed Successfully",
            heading="Staff Password Changed Successfully",
            body_html=body,
            image_url=LECTURER_IMAGE_URL
        )

    # ======================================================
    # STUDENT CLEARANCE STAGE APPROVED EMAIL
    # Includes an OTP when the student must proceed to another
    # stage. Final-stage approval is sent without an OTP.
    # ======================================================

    @staticmethod
    def send_student_clearance_stage_approved_email(
        receiver_email: str,
        student_name: str,
        reg_no: str,
        stage: str,
        next_stage: str = None,
        otp: str = None,
        otp_expiry_minutes: int = None
    ):
        try:
            if not receiver_email or not str(receiver_email).strip():
                print("Approval email failed: student email is missing.")
                return False

            if next_stage and not otp:
                print(
                    "Approval email failed: an OTP is required "
                    "for the next clearance stage."
                )
                return False

            name = html.escape(str(student_name))
            safe_reg_no = html.escape(str(reg_no))
            safe_stage = html.escape(
                str(stage).replace("_", " ").title()
            )

            if next_stage:
                safe_next_stage = html.escape(
                    str(next_stage).replace("_", " ").title()
                )
                safe_otp = html.escape(str(otp))

                body = f"""
                    <p>Hello <strong>{name}</strong>,</p>
                    <p>Your clearance stage has been
                       <strong>approved</strong>.</p>

                    <div style="background:#f1f8e9;
                                border:1px solid #c5e1a5;
                                border-radius:8px;padding:20px;
                                margin:20px 0;">
                        <p><strong>Registration Number:</strong>
                           {safe_reg_no}</p>
                        <p><strong>Approved Stage:</strong>
                           {safe_stage}</p>
                        <p><strong>Next Stage:</strong>
                           {safe_next_stage}</p>
                    </div>

                    <p>Your OTP for the next clearance stage is:</p>

                    <div style="text-align:center;padding:20px;
                                background:#f1f8e9;
                                border:1px dashed #1b5e20;
                                border-radius:8px;">
                        <span style="font-size:28px;font-weight:bold;
                                     letter-spacing:6px;color:#1b5e20;">
                            {safe_otp}
                        </span>
                    </div>

                    <p>This OTP does not expire with time. It remains
                       valid until it is used or invalidated by the
                       clearance system.</p>

                    <p>Provide this OTP to the authorized staff
                       responsible for your next clearance stage.</p>
                    <p>Do not share this OTP with anyone else.</p>
                """

                subject = (
                    "Student Clearance - "
                    f"{str(stage).replace('_', ' ').title()} Approved"
                )
                heading = "Clearance Stage Approved"

            else:
                body = f"""
                    <p>Hello <strong>{name}</strong>,</p>
                    <p>Your final clearance stage has been
                       <strong>approved</strong>.</p>

                    <div style="background:#f1f8e9;
                                border:1px solid #c5e1a5;
                                border-radius:8px;padding:20px;
                                margin:20px 0;">
                        <p><strong>Registration Number:</strong>
                           {safe_reg_no}</p>
                        <p><strong>Approved Stage:</strong>
                           {safe_stage}</p>
                    </div>

                    <p>Your clearance has been marked as completed.
                       Congratulations!</p>
                """

                subject = "Student Clearance - Final Clearance Approved"
                heading = "Final Clearance Approved"

            email_sent = EmailSender._send_html_email(
                receiver_email=str(receiver_email).strip(),
                subject=subject,
                heading=heading,
                body_html=body,
                image_url=IMAGE_URL
            )

            if email_sent is True:
                print(
                    f"Approval email accepted by SMTP for "
                    f"{receiver_email} | Student: {reg_no} "
                    f"| Stage: {stage}"
                )
                return True

            print(
                f"Approval email failed for {receiver_email} "
                f"| Student: {reg_no} | Stage: {stage}"
            )
            return False

        except Exception as e:
            print(
                f"Approval email error: {type(e).__name__}: {e}"
            )
            return False

    # ======================================================
    # STUDENT CLEARANCE STAGE REJECTED EMAIL
    # Sends the rejection reason. No OTP is included.
    # ======================================================

    @staticmethod
    def send_student_clearance_stage_rejected_email(
        receiver_email: str,
        student_name: str,
        reg_no: str,
        stage: str,
        rejection_comment: str
    ):
        try:
            if not receiver_email or not str(receiver_email).strip():
                print("Rejection email failed: student email is missing.")
                return False

            if not rejection_comment or not str(rejection_comment).strip():
                print(
                    "Rejection email failed: rejection reason is missing."
                )
                return False

            name = html.escape(str(student_name))
            safe_reg_no = html.escape(str(reg_no))
            safe_stage = html.escape(
                str(stage).replace("_", " ").title()
            )
            safe_comment = html.escape(str(rejection_comment))

            body = f"""
                <p>Hello <strong>{name}</strong>,</p>
                <p>Your clearance stage has been reviewed but
                   could not be approved.</p>

                <div style="background:#fff3e0;
                            border:1px solid #ffcc80;
                            border-radius:8px;padding:20px;
                            margin:20px 0;">
                    <p><strong>Registration Number:</strong>
                       {safe_reg_no}</p>
                    <p><strong>Stage:</strong> {safe_stage}</p>
                    <p><strong>Reason for Rejection:</strong></p>
                    <p style="white-space:pre-wrap;">
                        {safe_comment}
                    </p>
                </div>

                <p>Please address the issue described above
                   before requesting another review.</p>
                <p>If you need clarification, contact the office
                   responsible for this clearance stage.</p>
            """

            email_sent = EmailSender._send_html_email(
                receiver_email=str(receiver_email).strip(),
                subject=(
                    f"Student Clearance - {safe_stage} Stage Rejected"
                ),
                heading="Clearance Stage Rejected",
                body_html=body,
                image_url=IMAGE_URL
            )

            if email_sent is True:
                print(
                    f"Rejection email accepted by SMTP for "
                    f"{receiver_email} | Student: {reg_no} "
                    f"| Stage: {stage}"
                )
                return True

            print(
                f"Rejection email failed for {receiver_email} "
                f"| Student: {reg_no} | Stage: {stage}"
            )
            return False

        except Exception as e:
            print(
                f"Rejection email error: {type(e).__name__}: {e}"
            )
            return False

    # ======================================================
    # STUDENT CLEARANCE STAGE OTP VERIFIED EMAIL
    # Notifies the student after successful OTP verification
    # and clearance advancement.
    # ======================================================

    @staticmethod
    def send_student_clearance_stage_otp_verified_email(
        receiver_email: str,
        student_name: str,
        reg_no: str,
        previous_stage: str,
        current_stage: str
    ):
        try:
            if not receiver_email or not str(receiver_email).strip():
                print(
                    "OTP verification email failed: "
                    "student email is missing."
                )
                return False

            name = html.escape(str(student_name or "Student"))
            safe_reg_no = html.escape(str(reg_no))

            safe_previous_stage = html.escape(
                str(previous_stage).replace("_", " ").title()
            )

            safe_current_stage = html.escape(
                str(current_stage).replace("_", " ").title()
            )

            body = f"""
                <p>Hello <strong>{name}</strong>,</p>

                <p>
                    Your clearance OTP has been
                    <strong style="color:#218838;">
                        verified successfully
                    </strong>.
                </p>

                <div style="background:#f1f8e9;
                            border:1px solid #c5e1a5;
                            border-radius:8px;
                            padding:20px;
                            margin:20px 0;">

                    <p>
                        <strong>Registration Number:</strong>
                        {safe_reg_no}
                    </p>

                    <p>
                        <strong>Previous Stage:</strong>
                        {safe_previous_stage}
                    </p>

                    <p>
                        <strong>Current Clearance Stage:</strong>
                        <span style="color:#1b5e20;font-weight:bold;">
                            {safe_current_stage}
                        </span>
                    </p>

                    <p>
                        <strong>OTP Verification Status:</strong>
                        <span style="color:#218838;font-weight:bold;">
                            Successful
                        </span>
                    </p>
                </div>

                <p>
                    Your clearance has advanced to the
                    <strong>{safe_current_stage}</strong> stage.
                </p>

                <p>
                    You can now proceed with the clearance
                    requirements for this stage.
                </p>

                <p>
                    Please contact the appropriate clearance
                    officer if you need assistance.
                </p>

                <p>
                    Regards,<br>
                    Student Clearance System
                </p>
            """

            email_sent = EmailSender._send_html_email(
                receiver_email=str(receiver_email).strip(),
                subject=(
                    "Student Clearance - OTP Verified "
                    "and Stage Updated"
                ),
                heading="Clearance OTP Verified Successfully",
                body_html=body,
                image_url=IMAGE_URL
            )

            if email_sent is True:
                print(
                    "OTP verification email accepted by SMTP: "
                    f"{receiver_email} | Student: {reg_no} | "
                    f"New stage: {current_stage}"
                )
                return True

            print(
                "OTP verification email failed: "
                f"{receiver_email} | Student: {reg_no}"
            )
            return False

        except Exception as e:
            print(
                "OTP verification email error: "
                f"{type(e).__name__}: {e}"
            )
            return False
