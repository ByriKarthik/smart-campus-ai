from django.contrib import messages
from django.db.models import Count, ExpressionWrapper, F, FloatField, Q
from django.shortcuts import redirect, render
from django.utils import timezone
from math import ceil

from accounts.models import FacultyProfile, StudentProfile, User
from academics.models import ClassSchedule, Enrollment, Section, Subject
from attendance.models import AttendanceRecord, AttendanceSession
from canteen.models import Order
from planner.models import RemedialSession


ROLE_TO_DASHBOARD = {
    "ADMIN": "/admin-dashboard/",
    "FACULTY": "/faculty-dashboard/",
    "STUDENT": "/student-dashboard/",
}

WEEKDAY_CODE_MAP = {
    0: "MON",
    1: "TUE",
    2: "WED",
    3: "THU",
    4: "FRI",
    5: "SAT",
    6: "SUN",
}


def login_view(request):
    if request.session.get("user_id") and request.session.get("role") in ROLE_TO_DASHBOARD:
        return redirect(ROLE_TO_DASHBOARD[request.session["role"]])

    if request.method == "POST":
        user_id = request.POST.get("user_id", "").strip()
        password = request.POST.get("password", "")

        user = User.objects.filter(
            user_id=user_id,
            password=password,
            is_active=True,
        ).first()

        if user:
            request.session["user_id"] = user.user_id
            request.session["role"] = user.role
            return redirect(ROLE_TO_DASHBOARD.get(user.role, "/login/"))

        messages.error(request, "Invalid user ID or password.")

    return render(request, "core/login.html")


def home_view(request):
    if request.session.get("user_id") and request.session.get("role") in ROLE_TO_DASHBOARD:
        return redirect(ROLE_TO_DASHBOARD[request.session["role"]])
    return render(request, "home.html")


def logout_view(request):
    request.session.flush()
    return redirect("login")


def _session_check(request, required_role):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or not role:
        return None, redirect("login")

    if role != required_role:
        return None, redirect(ROLE_TO_DASHBOARD.get(role, "/login/"))

    return {"user_id": user_id, "role": role}, None


def admin_dashboard(request):
    context, response = _session_check(request, "ADMIN")
    if response:
        return response

    low_attendance_count = (
        AttendanceRecord.objects.values("student")
        .annotate(
            total_sessions=Count("id"),
            present_sessions=Count("id", filter=Q(status="PRESENT")),
        )
        .filter(total_sessions__gt=0)
        .annotate(
            attendance_percentage=ExpressionWrapper(
                (F("present_sessions") * 100.0) / F("total_sessions"),
                output_field=FloatField(),
            )
        )
        .filter(attendance_percentage__lt=75)
        .count()
    )

    overloaded_sections_count = (
        Section.objects.annotate(
            enrolled_students=Count("studentprofile"),
            section_capacity=F("capacity"),
        )
        .filter(section_capacity__gt=0)
        .annotate(
            utilization_percentage=ExpressionWrapper(
                (F("enrolled_students") * 100.0) / F("section_capacity"),
                output_field=FloatField(),
            )
        )
        .filter(utilization_percentage__gt=90)
        .count()
    )

    today = timezone.localdate()
    today_code = WEEKDAY_CODE_MAP[today.weekday()]

    scheduled_faculty_ids = ClassSchedule.objects.filter(
        day_of_week=today_code
    ).values_list("faculty_id", flat=True).distinct()

    faculty_marked_today_ids = AttendanceSession.objects.filter(
        date=today,
        marked_by__isnull=False,
    ).values_list("marked_by_id", flat=True).distinct()

    inactive_faculty_count = User.objects.filter(
        role="FACULTY",
        is_active=True,
        user_id__in=scheduled_faculty_ids,
    ).exclude(user_id__in=faculty_marked_today_ids).count()

    busiest_stall = (
        Order.objects.filter(status__in=["PENDING", "PREPARING"])
        .values("stall__name")
        .annotate(active_load=Count("id"))
        .order_by("-active_load")
        .first()
    )

    context.update(
        {
            "total_students": User.objects.filter(role="STUDENT").count(),
            "total_faculty": User.objects.filter(role="FACULTY").count(),
            "total_subjects": Subject.objects.count(),
            "total_attendance_sessions": AttendanceSession.objects.count(),
            "total_food_orders": Order.objects.count(),
            "low_attendance_count": low_attendance_count,
            "inactive_faculty_count": inactive_faculty_count,
            "overloaded_sections_count": overloaded_sections_count,
            "busiest_stall_name": busiest_stall["stall__name"] if busiest_stall else "No active orders",
            "busiest_stall_load": busiest_stall["active_load"] if busiest_stall else 0,
            "today_date": today,
            # Backward-compatible aliases for current template bindings.
            "low_attendance_students": low_attendance_count,
            "inactive_faculty_today": inactive_faculty_count,
            "overloaded_sections": overloaded_sections_count,
        }
    )
    return render(request, "core/admin_dashboard.html", context)


def admin_resources(request):
    context, response = _session_check(request, "ADMIN")
    if response:
        return response

    sections = (
        Section.objects.select_related("course")
        .annotate(enrolled_students=Count("studentprofile"))
        .order_by("course__course_name", "year", "name")
    )
    section_rows = []
    for section in sections:
        capacity = section.capacity or 0
        enrolled = section.enrolled_students or 0
        utilization = round((enrolled / capacity) * 100, 2) if capacity > 0 else 0

        if utilization < 70:
            utilization_status = "Low"
        elif utilization <= 90:
            utilization_status = "Normal"
        else:
            utilization_status = "High"

        section_rows.append(
            {
                "section": section,
                "capacity": capacity,
                "enrolled_students": enrolled,
                "utilization": utilization,
                "status": utilization_status,
            }
        )

    faculty_users = User.objects.filter(role="FACULTY").order_by("user_id")
    faculty_rows = []
    for faculty in faculty_users:
        assigned_subjects_qs = Subject.objects.filter(faculty=faculty)
        faculty_rows.append(
            {
                "faculty": faculty,
                "subjects_assigned_count": assigned_subjects_qs.count(),
                "students_enrolled_count": Enrollment.objects.filter(subject__in=assigned_subjects_qs).count(),
                "attendance_sessions_count": AttendanceSession.objects.filter(marked_by=faculty).count(),
            }
        )

    context.update(
        {
            "section_rows": section_rows,
            "faculty_rows": faculty_rows,
        }
    )
    return render(request, "core/admin_resources.html", context)


def admin_attendance_monitoring(request):
    context, response = _session_check(request, "ADMIN")
    if response:
        return response
    mode = request.GET.get("mode", "").strip().lower()

    low_attendance_qs = (
        AttendanceRecord.objects.values("student")
        .annotate(
            total_classes=Count("id"),
            total_present=Count("id", filter=Q(status="PRESENT")),
        )
        .filter(total_classes__gt=0)
        .annotate(
            attendance_percentage=ExpressionWrapper(
                (F("total_present") * 100.0) / F("total_classes"),
                output_field=FloatField(),
            )
        )
        .filter(attendance_percentage__lt=75)
        .order_by("attendance_percentage")
    )

    student_ids = [row["student"] for row in low_attendance_qs]
    profile_map = {
        profile.user_id: profile
        for profile in StudentProfile.objects.filter(user_id__in=student_ids).select_related("section")
    }

    low_attendance_students = []
    for row in low_attendance_qs:
        profile = profile_map.get(row["student"])
        low_attendance_students.append(
            {
                "student_name": profile.name if profile else row["student"],
                "section": str(profile.section) if profile and profile.section else "-",
                "attendance_percentage": round(row["attendance_percentage"], 2),
            }
        )

    today = timezone.localdate()
    today_code = WEEKDAY_CODE_MAP[today.weekday()]
    scheduled_today = ClassSchedule.objects.filter(day_of_week=today_code).select_related("faculty")
    scheduled_faculty_ids = scheduled_today.values_list("faculty_id", flat=True).distinct()
    faculty_marked_today_ids = AttendanceSession.objects.filter(
        date=today,
        marked_by__isnull=False,
    ).values_list("marked_by_id", flat=True).distinct()

    inactive_faculties = User.objects.filter(
        role="FACULTY",
        is_active=True,
        user_id__in=scheduled_faculty_ids,
    ).exclude(user_id__in=faculty_marked_today_ids)

    faculty_profile_map = {
        profile.user_id: profile.name
        for profile in FacultyProfile.objects.filter(user_id__in=inactive_faculties.values_list("user_id", flat=True))
    }

    inactive_faculty_rows = []
    for faculty in inactive_faculties:
        subjects = list(Subject.objects.filter(faculty=faculty).values_list("subject_name", flat=True))
        scheduled_count = scheduled_today.filter(faculty=faculty).count()
        inactive_faculty_rows.append(
            {
                "faculty_name": faculty_profile_map.get(faculty.user_id, faculty.user_id),
                "subjects": ", ".join(subjects) if subjects else "-",
                "scheduled_classes_today": scheduled_count,
            }
        )

    context.update(
        {
            "mode": mode,
            "show_students": mode in ("", "students"),
            "show_faculty": mode in ("", "faculty"),
            "low_attendance_students": low_attendance_students,
            "inactive_faculty_rows": inactive_faculty_rows,
        }
    )
    return render(request, "core/admin_attendance_monitoring.html", context)


def admin_operations_monitoring(request):
    context, response = _session_check(request, "ADMIN")
    if response:
        return response
    mode = request.GET.get("mode", "").strip().lower()

    section_utilization_rows = []
    sections = Section.objects.annotate(enrolled_students=Count("studentprofile")).select_related("course").order_by(
        "course__course_name", "year", "name"
    )
    for section in sections:
        capacity = section.capacity or 0
        utilization = round((section.enrolled_students / capacity) * 100, 2) if capacity > 0 else 0
        if utilization < 70:
            status = "Low"
        elif utilization <= 90:
            status = "Moderate"
        else:
            status = "High"
        section_utilization_rows.append(
            {
                "section": section,
                "capacity": capacity,
                "enrolled_students": section.enrolled_students,
                "utilization": utilization,
                "status": status,
            }
        )

    faculty_workload_rows = []
    faculty_users = User.objects.filter(role="FACULTY", is_active=True).order_by("user_id")
    faculty_profile_map = {
        profile.user_id: profile.name
        for profile in FacultyProfile.objects.filter(user_id__in=faculty_users.values_list("user_id", flat=True))
    }
    for faculty in faculty_users:
        assigned_subjects = Subject.objects.filter(faculty=faculty)
        faculty_workload_rows.append(
            {
                "faculty_name": faculty_profile_map.get(faculty.user_id, faculty.user_id),
                "subjects_assigned": assigned_subjects.count(),
                "students_covered": Enrollment.objects.filter(subject__in=assigned_subjects).count(),
                "attendance_sessions": AttendanceSession.objects.filter(marked_by=faculty).count(),
            }
        )

    busiest_stall = (
        Order.objects.filter(status__in=["PENDING", "PREPARING"])
        .values("stall__name")
        .annotate(active_orders=Count("id"))
        .order_by("-active_orders")
        .first()
    )
    pending_food_orders_count = Order.objects.filter(status="PENDING").count()

    context.update(
        {
            "mode": mode,
            "show_sections": mode in ("", "sections"),
            "show_faculty_workload": mode in ("", "faculty"),
            "show_canteen": mode in ("", "canteen"),
            "section_utilization_rows": section_utilization_rows,
            "faculty_workload_rows": faculty_workload_rows,
            "busiest_stall_name": busiest_stall["stall__name"] if busiest_stall else "No active orders",
            "busiest_stall_count": busiest_stall["active_orders"] if busiest_stall else 0,
            "pending_food_orders_count": pending_food_orders_count,
        }
    )
    return render(request, "core/admin_operations_monitoring.html", context)


def faculty_dashboard(request):
    context, response = _session_check(request, "FACULTY")
    if response:
        return response

    faculty_user = User.objects.filter(
        user_id=context["user_id"],
        role="FACULTY",
        is_active=True,
    ).first()
    if not faculty_user:
        return redirect("login")

    assigned_subjects = Subject.objects.filter(faculty=faculty_user).select_related("department", "course")
    sessions_by_faculty = AttendanceSession.objects.filter(marked_by=faculty_user)
    today = timezone.localdate()
    today_code = WEEKDAY_CODE_MAP[today.weekday()]
    today_classes = (
        ClassSchedule.objects.filter(
            faculty=faculty_user,
            day_of_week=today_code,
        )
        .select_related("subject", "section")
        .order_by("start_time")
    )

    context.update(
        {
            "assigned_subjects": assigned_subjects,
            "my_subjects_count": assigned_subjects.count(),
            "sessions_conducted_count": sessions_by_faculty.count(),
            "sessions_today_count": sessions_by_faculty.filter(date=today).count(),
            "today_date": today,
            "today_classes": today_classes,
        }
    )
    return render(request, "core/faculty_dashboard.html", context)


def student_dashboard(request):
    context, response = _session_check(request, "STUDENT")
    if response:
        return response

    student_user = User.objects.filter(
        user_id=context["user_id"],
        role="STUDENT",
        is_active=True,
    ).first()
    if not student_user:
        return redirect("login")

    total_sessions = AttendanceRecord.objects.filter(student=student_user).count()
    present_sessions = AttendanceRecord.objects.filter(
        student=student_user,
        status="PRESENT",
    ).count()

    required_percentage = 75
    attendance_percentage = (present_sessions / total_sessions * 100) if total_sessions > 0 else 0
    is_below_threshold = total_sessions > 0 and attendance_percentage < required_percentage
    needed_classes = 0
    if is_below_threshold:
        needed_classes = ceil(
            ((required_percentage / 100.0) * total_sessions - present_sessions)
            / (1 - (required_percentage / 100.0))
        )
        needed_classes = max(needed_classes, 0)

    enrolled_subjects = (
        Enrollment.objects.filter(student=student_user)
        .select_related("subject", "subject__faculty")
        .order_by("subject__semester", "subject__subject_code")
    )

    student_profile = StudentProfile.objects.filter(user=student_user).select_related("section").first()
    upcoming_remedials = RemedialSession.objects.none()
    today_classes = ClassSchedule.objects.none()
    if student_profile and student_profile.section_id:
        today_code = WEEKDAY_CODE_MAP[timezone.localdate().weekday()]
        today_classes = (
            ClassSchedule.objects.filter(
                section=student_profile.section,
                day_of_week=today_code,
            )
            .select_related("subject", "faculty")
            .order_by("start_time")
        )
        upcoming_remedials = (
            RemedialSession.objects.filter(
                section=student_profile.section,
                scheduled_date__gte=timezone.localdate(),
            )
            .select_related("subject", "created_by")
            .order_by("scheduled_date", "start_time")
        )

    my_orders = Order.objects.filter(student=student_user).order_by("-order_time")
    pending_orders_count = my_orders.filter(status="PENDING").count()
    last_order = my_orders.first()

    context.update(
        {
            "attendance_percentage": round(attendance_percentage, 2),
            "total_sessions": total_sessions,
            "present_sessions": present_sessions,
            "required_percentage": required_percentage,
            "is_below_threshold": is_below_threshold,
            "needed_classes": needed_classes,
            "enrolled_subjects": enrolled_subjects,
            "upcoming_remedials": upcoming_remedials,
            "today_classes": today_classes,
            "pending_orders_count": pending_orders_count,
            "last_order_status": last_order.status if last_order else "No orders yet",
        }
    )
    return render(request, "core/student_dashboard.html", context)


def student_timetable_view(request):
    context, response = _session_check(request, "STUDENT")
    if response:
        return response

    student_user = User.objects.filter(
        user_id=context["user_id"],
        role="STUDENT",
        is_active=True,
    ).first()
    if not student_user:
        return redirect("login")

    student_profile = StudentProfile.objects.filter(user=student_user).select_related("section").first()
    day_columns = ["MON", "TUE", "WED", "THU", "FRI"]
    time_slots = [
        ("09:00", "10:00"),
        ("10:00", "11:00"),
        ("11:00", "12:00"),
        ("14:00", "15:00"),
        ("15:00", "16:00"),
    ]

    slot_rows = [
        {
            "start_str": start_str,
            "end_str": end_str,
            "label": f"{start_str} - {end_str}",
            "cells": {day: None for day in day_columns},
            "ordered_cells": [],
        }
        for start_str, end_str in time_slots
    ]
    slot_index = {(row["start_str"], row["end_str"]): row for row in slot_rows}

    if student_profile and student_profile.section_id:
        schedules = (
            ClassSchedule.objects.filter(
                section=student_profile.section,
                day_of_week__in=day_columns,
            )
            .select_related("subject", "faculty")
            .order_by("day_of_week", "start_time")
        )

        for schedule in schedules:
            key = (
                schedule.start_time.strftime("%H:%M"),
                schedule.end_time.strftime("%H:%M"),
            )
            row = slot_index.get(key)
            if not row:
                continue
            row["cells"][schedule.day_of_week] = {
                "type": "CLASS",
                "subject_name": schedule.subject.subject_name,
                "faculty_name": schedule.faculty.user_id,
                "room": schedule.room,
            }

        upcoming_remedials = RemedialSession.objects.filter(
            section=student_profile.section,
            scheduled_date__gte=timezone.localdate(),
            start_time__isnull=False,
            end_time__isnull=False,
        ).select_related("subject", "created_by")

        weekday_map = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI"}
        for remedial in upcoming_remedials:
            day_code = weekday_map.get(remedial.scheduled_date.weekday())
            if day_code not in day_columns:
                continue
            key = (
                remedial.start_time.strftime("%H:%M"),
                remedial.end_time.strftime("%H:%M"),
            )
            row = slot_index.get(key)
            if not row:
                continue
            if row["cells"][day_code] is None:
                row["cells"][day_code] = {
                    "type": "REMEDIAL",
                    "subject_name": remedial.subject.subject_name,
                    "faculty_name": remedial.created_by.user_id,
                    "room": "Remedial",
                }

    for row in slot_rows:
        row["ordered_cells"] = [row["cells"][day] for day in day_columns]

    context.update(
        {
            "section": student_profile.section if student_profile else None,
            "day_columns": day_columns,
            "slot_rows": slot_rows,
        }
    )
    return render(request, "core/student_timetable.html", context)


def faculty_timetable_view(request):
    context, response = _session_check(request, "FACULTY")
    if response:
        return response

    faculty_user = User.objects.filter(
        user_id=context["user_id"],
        role="FACULTY",
        is_active=True,
    ).first()
    if not faculty_user:
        return redirect("login")

    day_columns = ["MON", "TUE", "WED", "THU", "FRI"]
    time_slots = [
        ("09:00", "10:00"),
        ("10:00", "11:00"),
        ("11:00", "12:00"),
        ("14:00", "15:00"),
        ("15:00", "16:00"),
    ]

    slot_rows = [
        {
            "start_str": start_str,
            "end_str": end_str,
            "label": f"{start_str} - {end_str}",
            "cells": {day: None for day in day_columns},
            "ordered_cells": [],
        }
        for start_str, end_str in time_slots
    ]
    slot_index = {(row["start_str"], row["end_str"]): row for row in slot_rows}

    schedules = (
        ClassSchedule.objects.filter(
            faculty=faculty_user,
            day_of_week__in=day_columns,
        )
        .select_related("subject", "section")
        .order_by("day_of_week", "start_time")
    )

    for schedule in schedules:
        key = (
            schedule.start_time.strftime("%H:%M"),
            schedule.end_time.strftime("%H:%M"),
        )
        row = slot_index.get(key)
        if not row:
            continue
        row["cells"][schedule.day_of_week] = {
            "subject_name": schedule.subject.subject_name,
            "section_name": schedule.section.name,
            "room": schedule.room,
        }

    for row in slot_rows:
        row["ordered_cells"] = [row["cells"][day] for day in day_columns]

    context.update(
        {
            "day_columns": day_columns,
            "slot_rows": slot_rows,
        }
    )
    return render(request, "core/faculty_timetable.html", context)
