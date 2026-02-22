import random
import string
from datetime import time

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import User
from academics.models import Section, Subject
from .models import RemedialAttendance, RemedialSession


def _session_user_by_role(request, required_role):
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    if not user_id or role != required_role:
        return None, redirect("login")

    user = User.objects.filter(
        user_id=user_id,
        role=required_role,
        is_active=True,
    ).first()
    if not user:
        return None, redirect("login")
    return user, None


def _generate_unique_code(length=6):
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(alphabet, k=length))
        if not RemedialSession.objects.filter(code=code).exists():
            return code


def schedule_remedial(request):
    faculty_user, response = _session_user_by_role(request, "FACULTY")
    if response:
        return response

    subjects = Subject.objects.filter(faculty=faculty_user).select_related("course").order_by("subject_name")
    selected_subject_id = request.POST.get("subject", "")
    selected_section_id = request.POST.get("section", "")
    selected_date = request.POST.get("scheduled_date", "")
    selected_start_time = request.POST.get("start_time", "")
    selected_end_time = request.POST.get("end_time", "")
    sections = Section.objects.filter(course__in=subjects.values("course").distinct()).select_related("course").order_by("year", "name")

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        section_id = request.POST.get("section")
        scheduled_date = request.POST.get("scheduled_date")
        start_time_raw = request.POST.get("start_time")
        end_time_raw = request.POST.get("end_time")

        subject = subjects.filter(id=subject_id).first()
        if not subject:
            messages.error(request, "Invalid subject selection.")
            return redirect("schedule_remedial")

        section = Section.objects.filter(id=section_id, course=subject.course).first()
        if not section:
            messages.error(request, "Please select a valid section for the selected subject.")
            return redirect(f"/planner/schedule-remedial/?subject={subject.id}")

        if not scheduled_date:
            messages.error(request, "Please select a date.")
            return redirect(f"/planner/schedule-remedial/?subject={subject.id}")

        if not start_time_raw or not end_time_raw:
            messages.error(request, "Please select start and end time.")
            return redirect("schedule_remedial")

        try:
            start_time_value = time.fromisoformat(start_time_raw)
            end_time_value = time.fromisoformat(end_time_raw)
        except ValueError:
            messages.error(request, "Invalid time format.")
            return redirect("schedule_remedial")

        if end_time_value <= start_time_value:
            messages.error(request, "End time must be after start time.")
            return redirect("schedule_remedial")

        code = _generate_unique_code()
        RemedialSession.objects.create(
            subject=subject,
            section=section,
            scheduled_date=scheduled_date,
            start_time=start_time_value,
            end_time=end_time_value,
            code=code,
            created_by=faculty_user,
        )

        messages.success(request, f"Remedial session scheduled successfully. Code: {code}")
        return redirect("faculty_dashboard")

    return render(
        request,
        "planner/schedule_remedial.html",
        {
            "subjects": subjects,
            "sections": sections,
            "selected_subject_id": str(selected_subject_id),
            "selected_section_id": str(selected_section_id),
            "selected_date": selected_date,
            "selected_start_time": selected_start_time,
            "selected_end_time": selected_end_time,
        },
    )


def join_remedial(request):
    student_user, response = _session_user_by_role(request, "STUDENT")
    if response:
        return response

    if request.method == "POST":
        entered_code = request.POST.get("code", "").strip().upper()
        if not entered_code:
            messages.error(request, "Please enter a remedial code.")
            return redirect("join_remedial")

        session = RemedialSession.objects.filter(code=entered_code).select_related("subject", "section").first()
        if not session:
            messages.error(request, "Invalid remedial code.")
            return redirect("join_remedial")

        if session.scheduled_date != timezone.localdate():
            messages.error(request, "This remedial code is not active today.")
            return redirect("join_remedial")

        attendance, created = RemedialAttendance.objects.get_or_create(
            session=session,
            student=student_user,
        )
        if not created:
            messages.error(request, "Attendance already marked for this remedial session.")
            return redirect("join_remedial")

        messages.success(
            request,
            f"Attendance marked successfully for {session.subject.subject_name} ({session.code}).",
        )
        return redirect("student_dashboard")

    return render(request, "planner/join_remedial.html")
