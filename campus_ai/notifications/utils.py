from django.core.mail import send_mail
from django.conf import settings


def send_absent_email(student, subject, session):
    """
    Send email to parent when student is absent
    """

    student_profile = student.studentprofile
    parent_email = student_profile.parent_contact  # using as email

    if not parent_email:
        return

    message = f"""
Dear Parent,

This is to inform you that your ward:

Name: {student_profile.name}
Roll No: {student_profile.roll_no}
Subject: {subject.subject_name}
Date: {session.date}
Time: {session.start_time} - {session.end_time}

Status: ABSENT

Please ensure necessary action.

Regards,
Campus Attendance System
"""

    try:
        send_mail(
            subject='Attendance Alert: Absence Notification',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_email],
            fail_silently=False
        )
    except Exception as e:
        print(f"Email failed for {parent_email}: {e}")

