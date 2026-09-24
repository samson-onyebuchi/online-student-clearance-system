from config import Config
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ✅ Email configuration (explicitly set from Config)

# ==========================================================
# EMAIL CONFIGURATION
# ==========================================================

SMTP_SERVER = Config.SMTP_SERVER
SMTP_PORT = int(Config.SMTP_PORT)

EMAIL_USERNAME = Config.EMAIL_USERNAME
EMAIL_PASSWORD = Config.EMAIL_PASSWORD

IMAGE_URL = Config.IMAGE_URL
LECTURER_IMAGE_URL = Config.LECTURER_IMAGE_URL


# ==========================================================
# EMAIL SENDER
# ==========================================================

class EmailSender:


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

        try:

            # ----------------------------------------------
            # Create email
            # ----------------------------------------------

            msg = MIMEMultipart("alternative")

            msg["Subject"] = (
                "Student Clearance - Registration Successful"
            )

            msg["From"] = EMAIL_USERNAME
            msg["To"] = receiver_email


            # ----------------------------------------------
            # Registration Email HTML
            # ----------------------------------------------

            html_body = f"""
            <!DOCTYPE html>

            <html>

            <head>

                <meta charset="UTF-8">

                <meta name="viewport"
                      content="width=device-width, initial-scale=1.0">

                <title>
                    Student Registration
                </title>

            </head>


            <body style="
                margin: 0;
                padding: 0;
                background-color: #f4f6f8;
                font-family: Arial, Helvetica, sans-serif;
            ">


                <div style="
                    max-width: 600px;
                    margin: 30px auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                ">


                    <!-- =================================
                         HEADER
                    ================================== -->

                    <div style="
                        background-color: #1b5e20;
                        padding: 30px;
                        text-align: center;
                    ">

                        <img
                            src="{IMAGE_URL}"
                            alt="Logo"
                            style="
                                max-width: 100px;
                                height: auto;
                                margin-bottom: 10px;
                            "
                        >

                        <h2 style="
                            color: #ffffff;
                            margin: 5px 0;
                        ">
                            Student Clearance System
                        </h2>

                    </div>


                    <!-- =================================
                         BODY
                    ================================== -->

                    <div style="
                        padding: 30px;
                        color: #333333;
                    ">

                        <h3>
                            Welcome {student_name}
                        </h3>


                        <p style="
                            font-size: 15px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            Your student clearance account has been
                            successfully created.

                        </p>


                        <p style="
                            font-size: 15px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            Below are your login details:

                        </p>


                        <!-- =================================
                             LOGIN DETAILS
                        ================================== -->

                        <div style="
                            background-color: #f1f8e9;
                            border: 1px solid #c5e1a5;
                            border-radius: 8px;
                            padding: 20px;
                            margin: 20px 0;
                        ">

                            <p style="
                                margin: 8px 0;
                                font-size: 15px;
                            ">

                                <strong>
                                    Registration Number:
                                </strong>

                                {reg_no}

                            </p>


                            <p style="
                                margin: 8px 0;
                                font-size: 15px;
                            ">

                                <strong>
                                    Password:
                                </strong>

                                {password}

                            </p>

                        </div>


                        <p style="
                            font-size: 14px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            Please keep your login details secure.
                            Do not share your password with anyone.

                        </p>


                        <p style="
                            font-size: 14px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            You can now log in to your student
                            clearance account.

                        </p>


                        <hr style="
                            border: none;
                            border-top: 1px solid #eeeeee;
                            margin: 25px 0;
                        ">


                        <p style="
                            color: #888888;
                            font-size: 12px;
                            line-height: 1.5;
                            text-align: center;
                        ">

                            This is an automated email.
                            Please do not reply to this message.

                        </p>

                    </div>


                    <!-- =================================
                         FOOTER
                    ================================== -->

                    <div style="
                        background-color: #f8f8f8;
                        padding: 15px;
                        text-align: center;
                    ">

                        <p style="
                            margin: 0;
                            color: #888888;
                            font-size: 12px;
                        ">

                            Student Clearance System

                        </p>

                    </div>


                </div>

            </body>

            </html>
            """


            # ----------------------------------------------
            # Attach HTML
            # ----------------------------------------------

            msg.attach(
                MIMEText(
                    html_body,
                    "html"
                )
            )


            # ----------------------------------------------
            # Connect to SMTP Server
            # ----------------------------------------------

            with smtplib.SMTP(
                SMTP_SERVER,
                SMTP_PORT
            ) as server:

                server.starttls()

                server.login(
                    EMAIL_USERNAME,
                    EMAIL_PASSWORD
                )

                server.sendmail(
                    EMAIL_USERNAME,
                    receiver_email,
                    msg.as_string()
                )


            print(
                f"Student registration email sent to {receiver_email}"
            )

            return True


        except smtplib.SMTPAuthenticationError:

            print(
                "SMTP authentication failed"
            )

            return False


        except smtplib.SMTPConnectError:

            print(
                "Failed to connect to SMTP server"
            )

            return False


        except Exception as e:

            print(
                f"Failed to send student registration email: {e}"
            )

            return False



    # ======================================================
    # STUDENT FORGOT PASSWORD OTP EMAIL
    # ======================================================

    @staticmethod
    def send_student_forgot_password_email(
        receiver_email: str,
        student_name: str,
        otp: str
    ):

        try:

            # ----------------------------------------------
            # Create email
            # ----------------------------------------------

            msg = MIMEMultipart("alternative")

            msg["Subject"] = (
                "Student Clearance - Password Reset OTP"
            )

            msg["From"] = EMAIL_USERNAME
            msg["To"] = receiver_email


            # ----------------------------------------------
            # Forgot Password Email HTML
            # ----------------------------------------------

            html_body = f"""
            <!DOCTYPE html>

            <html>

            <head>

                <meta charset="UTF-8">

                <meta name="viewport"
                      content="width=device-width, initial-scale=1.0">

                <title>
                    Password Reset
                </title>

            </head>


            <body style="
                margin: 0;
                padding: 0;
                background-color: #f4f6f8;
                font-family: Arial, Helvetica, sans-serif;
            ">


                <div style="
                    max-width: 600px;
                    margin: 30px auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                ">


                    <!-- =================================
                         HEADER
                    ================================== -->

                    <div style="
                        background-color: #1b5e20;
                        padding: 30px;
                        text-align: center;
                    ">

                        <img
                            src="{IMAGE_URL}"
                            alt="Logo"
                            style="
                                max-width: 100px;
                                height: auto;
                                margin-bottom: 10px;
                            "
                        >

                        <h2 style="
                            color: #ffffff;
                            margin: 5px 0;
                        ">
                            Student Clearance System
                        </h2>

                    </div>


                    <!-- =================================
                         BODY
                    ================================== -->

                    <div style="
                        padding: 30px;
                        color: #333333;
                    ">

                        <h3>
                            Password Reset Request
                        </h3>


                        <p style="
                            font-size: 15px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            Hello <strong>{student_name}</strong>,

                        </p>


                        <p style="
                            font-size: 15px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            We received a request to reset the password
                            associated with your student clearance account.

                        </p>


                        <p style="
                            font-size: 15px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            Use the verification code below to continue
                            with your password reset:

                        </p>


                        <!-- =================================
                             OTP
                        ================================== -->

                        <div style="
                            text-align: center;
                            margin: 30px 0;
                        ">

                            <div style="
                                display: inline-block;
                                padding: 18px 30px;
                                background-color: #f1f8e9;
                                border: 2px dashed #1b5e20;
                                border-radius: 8px;
                            ">

                                <span style="
                                    font-size: 30px;
                                    font-weight: bold;
                                    letter-spacing: 8px;
                                    color: #1b5e20;
                                ">

                                    {otp}

                                </span>

                            </div>

                        </div>


                        <p style="
                            font-size: 14px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            This verification code will expire in
                            <strong>10 minutes</strong>.

                        </p>


                        <p style="
                            font-size: 14px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            Do not share this verification code with
                            anyone.

                        </p>


                        <p style="
                            font-size: 14px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            If you did not request a password reset,
                            you can safely ignore this email.

                        </p>


                        <hr style="
                            border: none;
                            border-top: 1px solid #eeeeee;
                            margin: 25px 0;
                        ">


                        <p style="
                            color: #888888;
                            font-size: 12px;
                            line-height: 1.5;
                            text-align: center;
                        ">

                            This is an automated email.
                            Please do not reply to this message.

                        </p>

                    </div>


                    <!-- =================================
                         FOOTER
                    ================================== -->

                    <div style="
                        background-color: #f8f8f8;
                        padding: 15px;
                        text-align: center;
                    ">

                        <p style="
                            margin: 0;
                            color: #888888;
                            font-size: 12px;
                        ">

                            Student Clearance System

                        </p>

                    </div>


                </div>

            </body>

            </html>
            """


            # ----------------------------------------------
            # Attach HTML
            # ----------------------------------------------

            msg.attach(
                MIMEText(
                    html_body,
                    "html"
                )
            )


            # ----------------------------------------------
            # Connect to SMTP Server
            # ----------------------------------------------

            with smtplib.SMTP(
                SMTP_SERVER,
                SMTP_PORT
            ) as server:

                server.starttls()

                server.login(
                    EMAIL_USERNAME,
                    EMAIL_PASSWORD
                )

                server.sendmail(
                    EMAIL_USERNAME,
                    receiver_email,
                    msg.as_string()
                )


            print(
                f"Student password reset OTP sent to {receiver_email}"
            )

            return True


        except smtplib.SMTPAuthenticationError:

            print(
                "SMTP authentication failed"
            )

            return False


        except smtplib.SMTPConnectError:

            print(
                "Failed to connect to SMTP server"
            )

            return False


        except Exception as e:

            print(
                f"Failed to send password reset email: {e}"
            )

            return False



    # ======================================================
    # STUDENT PASSWORD CHANGED NOTIFICATION EMAIL
    # ======================================================
    #
    # This method is used for BOTH:
    #
    # 1. OTP password reset
    # 2. Normal password reset using previous password
    #
    # ======================================================

    @staticmethod
    def send_student_password_changed_email(
        receiver_email: str,
        student_name: str
    ):

        try:

            # ----------------------------------------------
            # Create email
            # ----------------------------------------------

            msg = MIMEMultipart("alternative")

            msg["Subject"] = (
                "Student Clearance - Password Changed Successfully"
            )

            msg["From"] = EMAIL_USERNAME
            msg["To"] = receiver_email


            # ----------------------------------------------
            # Password Changed Email HTML
            # ----------------------------------------------

            html_body = f"""
            <!DOCTYPE html>

            <html>

            <head>

                <meta charset="UTF-8">

                <meta name="viewport"
                      content="width=device-width, initial-scale=1.0">

                <title>
                    Password Changed
                </title>

            </head>


            <body style="
                margin: 0;
                padding: 0;
                background-color: #f4f6f8;
                font-family: Arial, Helvetica, sans-serif;
            ">


                <div style="
                    max-width: 600px;
                    margin: 30px auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                ">


                    <!-- =================================
                         HEADER
                    ================================== -->

                    <div style="
                        background-color: #1b5e20;
                        padding: 30px;
                        text-align: center;
                    ">

                        <img
                            src="{IMAGE_URL}"
                            alt="Logo"
                            style="
                                max-width: 100px;
                                height: auto;
                                margin-bottom: 10px;
                            "
                        >

                        <h2 style="
                            color: #ffffff;
                            margin: 5px 0;
                        ">
                            Student Clearance System
                        </h2>

                    </div>


                    <!-- =================================
                         BODY
                    ================================== -->

                    <div style="
                        padding: 30px;
                        color: #333333;
                    ">

                        <h3 style="
                            color: #1b5e20;
                        ">

                            Password Changed Successfully

                        </h3>


                        <p style="
                            font-size: 15px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            Hello <strong>{student_name}</strong>,

                        </p>


                        <p style="
                            font-size: 15px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            Your Student Clearance account password
                            has been changed successfully.

                        </p>


                        <!-- =================================
                             SUCCESS MESSAGE
                        ================================== -->

                        <div style="
                            background-color: #f1f8e9;
                            border: 1px solid #c5e1a5;
                            border-radius: 8px;
                            padding: 20px;
                            margin: 20px 0;
                        ">

                            <p style="
                                margin: 0;
                                font-size: 15px;
                                line-height: 1.6;
                                color: #33691e;
                            ">

                                <strong>
                                    Your password has been updated.
                                </strong>

                                You can now log in using your new password.

                            </p>

                        </div>


                        <p style="
                            font-size: 14px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            If you made this change, no further action
                            is required.

                        </p>


                        <p style="
                            font-size: 14px;
                            line-height: 1.6;
                            color: #555555;
                        ">

                            If you did not make this change, please contact
                            the administrator immediately.

                        </p>


                        <hr style="
                            border: none;
                            border-top: 1px solid #eeeeee;
                            margin: 25px 0;
                        ">


                        <p style="
                            color: #888888;
                            font-size: 12px;
                            line-height: 1.5;
                            text-align: center;
                        ">

                            This is an automated email.
                            Please do not reply to this message.

                        </p>

                    </div>


                    <!-- =================================
                         FOOTER
                    ================================== -->

                    <div style="
                        background-color: #f8f8f8;
                        padding: 15px;
                        text-align: center;
                    ">

                        <p style="
                            margin: 0;
                            color: #888888;
                            font-size: 12px;
                        ">

                            Student Clearance System

                        </p>

                    </div>


                </div>

            </body>

            </html>
            """


            # ----------------------------------------------
            # Attach HTML
            # ----------------------------------------------

            msg.attach(
                MIMEText(
                    html_body,
                    "html"
                )
            )


            # ----------------------------------------------
            # Connect to SMTP Server
            # ----------------------------------------------

            with smtplib.SMTP(
                SMTP_SERVER,
                SMTP_PORT
            ) as server:

                server.starttls()

                server.login(
                    EMAIL_USERNAME,
                    EMAIL_PASSWORD
                )

                server.sendmail(
                    EMAIL_USERNAME,
                    receiver_email,
                    msg.as_string()
                )


            print(
                f"Password changed notification sent to {receiver_email}"
            )

            return True


        except smtplib.SMTPAuthenticationError:

            print(
                "SMTP authentication failed"
            )

            return False


        except smtplib.SMTPConnectError:

            print(
                "Failed to connect to SMTP server"
            )

            return False


        except Exception as e:

            print(
                f"Failed to send password changed email: {e}"
            )

            return False