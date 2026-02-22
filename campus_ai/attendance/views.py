import base64
import os
import uuid
from datetime import date

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from accounts.models import User
from academics.models import ClassSchedule, Subject, Enrollment, Section
from .models import AttendanceSession, AttendanceRecord
from ml.utils import get_present_students
from notifications.utils import send_absent_email


# =========================================================
# MAIN FACULTY ATTENDANCE VIEW
# =========================================================
def mark_attendance(request):
    """
    Faculty Attendance View
    - Subject + Section selection
    - Face recognition auto detection
    - Manual override
    - Email notification for absentees
    """

    # Keep existing flow, but prefer session faculty when available.
    faculty = None
    session_user_id = request.session.get("user_id")
    session_role = request.session.get("role")
    if session_user_id and session_role == "FACULTY":
        faculty = User.objects.filter(user_id=session_user_id, role="FACULTY", is_active=True).first()
    if not faculty:
        faculty = User.objects.get(user_id='FAC001')

    weekday_map = {
        0: "MON",
        1: "TUE",
        2: "WED",
        3: "THU",
        4: "FRI",
        5: "SAT",
        6: "SUN",
    }
    today_code = weekday_map[date.today().weekday()]
    today_schedules = ClassSchedule.objects.filter(
        faculty=faculty,
        day_of_week=today_code,
    ).select_related("subject", "section").order_by("start_time")

    current_time = timezone.localtime(timezone.now()).time()
    active_class = today_schedules.filter(
        start_time__lte=current_time,
        end_time__gte=current_time,
    ).first()

    subjects = Subject.objects.filter(
        id__in=today_schedules.values_list("subject_id", flat=True).distinct()
    ).select_related("course")

    selected_subject = None
    selected_section = None
    sections = []
    enrollments = []
    no_classes_today = not today_schedules.exists()

    # ==============================
    # GET REQUEST (Load Subject + Section)
    # ==============================
    subject_id = request.GET.get('subject')
    section_id = request.GET.get('section')

    if subject_id:
        selected_subject = Subject.objects.get(id=subject_id)

        # Get distinct sections for this subject from today's scheduled classes
        sections = Section.objects.filter(
            id__in=today_schedules.filter(subject=selected_subject).values_list("section_id", flat=True).distinct()
        )

        if section_id:
            selected_section = Section.objects.get(id=section_id)

            enrollments = Enrollment.objects.filter(
                subject=selected_subject,
                student__studentprofile__section=selected_section
            ).select_related(
                "student",
                "student__studentprofile"
            )
    elif active_class:
        selected_subject = active_class.subject
        selected_section = active_class.section
        sections = Section.objects.filter(
            id__in=today_schedules.filter(subject=selected_subject).values_list("section_id", flat=True).distinct()
        )
        enrollments = Enrollment.objects.filter(
            subject=selected_subject,
            student__studentprofile__section=selected_section
        ).select_related(
            "student",
            "student__studentprofile"
        )

    # ==============================
    # POST REQUEST (Submit Attendance)
    # ==============================
    if request.method == "POST":

        subject_id = request.POST.get("subject")
        section_id = request.POST.get("section")

        selected_subject = Subject.objects.get(id=subject_id)
        selected_section = Section.objects.get(id=section_id)

        enrollments = Enrollment.objects.filter(
            subject=selected_subject,
            student__studentprofile__section=selected_section
        ).select_related(
            "student",
            "student__studentprofile"
        )

        # ----------------------------
        # 1️⃣ Save Class Photo (if any)
        # ----------------------------
        class_photo_base64 = request.POST.get("class_captured_image")
        class_photo_file = request.FILES.get("class_uploaded_image")

        class_photo_path = None
        attendance_method = "MANUAL"

        if class_photo_base64 or class_photo_file:

            save_dir = os.path.join(
                settings.MEDIA_ROOT, "faces", "class_photos"
            )
            os.makedirs(save_dir, exist_ok=True)

            filename = f"class_{uuid.uuid4().hex}.png"
            class_photo_path = os.path.join(save_dir, filename)

            if class_photo_base64:
                header, imgstr = class_photo_base64.split(";base64,")
                image_bytes = base64.b64decode(imgstr)
            else:
                image_bytes = class_photo_file.read()

            with open(class_photo_path, "wb") as f:
                f.write(image_bytes)

            attendance_method = "FACE"

        # ----------------------------
        # 2️⃣ Run Face Recognition
        # ----------------------------
        auto_present_students = {}

        if class_photo_path:
            auto_present_students = get_present_students(class_photo_path)
            # format: {'STU001': 0.91}

        # ----------------------------
        # 3️⃣ Duplicate Session Protection
        # ----------------------------
        existing_session = AttendanceSession.objects.filter(
            subject=selected_subject,
            section=selected_section,
            date=date.today()
        ).first()

        if existing_session:
            messages.warning(
                request,
                "Attendance already marked for this subject & section today."
            )
            return redirect(
                f"{request.path}?subject={subject_id}&section={section_id}"
            )

        # ----------------------------
        # 4️⃣ Create Attendance Session
        # ----------------------------
        session = AttendanceSession.objects.create(
            subject=selected_subject,
            section=selected_section,
            date=date.today(),
            start_time="09:00",
            end_time="10:00",
            marked_by=faculty,
            method=attendance_method,
            confirmed=True
        )

        # ----------------------------
        # 5️⃣ Save Attendance Records
        # ----------------------------
        for enrollment in enrollments:
            student = enrollment.student

            status = "ABSENT"
            confidence = None

            # Auto detection result
            if student.user_id in auto_present_students:
                status = "PRESENT"
                confidence = auto_present_students[student.user_id]

            # Manual override
            if request.POST.get(student.user_id):
                status = "PRESENT"

            AttendanceRecord.objects.create(
                session=session,
                student=student,
                status=status,
                confidence_score=confidence,
                verified_by_faculty=True
            )

            # Email notification
            if status == "ABSENT":
                send_absent_email(student, selected_subject, session)

        messages.success(
            request,
            f"Attendance saved successfully ({attendance_method} mode)"
        )

        return redirect(
            f"{request.path}?subject={subject_id}&section={section_id}"
        )

    # ==============================
    # Render Page
    # ==============================
    return render(request, "attendance/mark_attendance.html", {
        "subjects": subjects,
        "selected_subject": selected_subject,
        "sections": sections,
        "selected_section": selected_section,
        "enrollments": enrollments,
        "today_code": today_code,
        "no_classes_today": no_classes_today,
        "active_class": active_class,
    })

# =========================================================
# AJAX VIEW — Auto Detect Attendance
# =========================================================
def auto_detect_attendance(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    class_photo_base64 = request.POST.get("class_captured_image")
    class_photo_file = request.FILES.get("class_uploaded_image")

    if not class_photo_base64 and not class_photo_file:
        return JsonResponse({"error": "No image provided"}, status=400)

    temp_dir = os.path.join(settings.MEDIA_ROOT, "faces", "temp")
    os.makedirs(temp_dir, exist_ok=True)

    filename = f"temp_{uuid.uuid4().hex}.png"
    image_path = os.path.join(temp_dir, filename)

    if class_photo_base64:
        header, imgstr = class_photo_base64.split(";base64,")
        image_bytes = base64.b64decode(imgstr)
    else:
        image_bytes = class_photo_file.read()

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    detected = get_present_students(image_path)

    return JsonResponse({
        "present_students": list(detected.keys()),
        "confidence": detected
    })
