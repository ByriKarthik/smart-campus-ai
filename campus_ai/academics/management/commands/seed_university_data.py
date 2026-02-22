import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import FacultyProfile, StudentProfile, User
from academics.models import ClassSchedule, Course, Department, Enrollment, Section, Subject
from attendance.models import AttendanceRecord, AttendanceSession
from canteen.models import MenuItem, Order, OrderItem, Stall, TimeSlot

try:
    from faker import Faker
except ImportError:  # pragma: no cover
    Faker = None


class Command(BaseCommand):
    help = "Seed realistic university data without deleting existing records."

    FACULTY_TARGET = 10
    STUDENT_TARGET = 300
    SECTION_TARGET = 10
    ATTENDANCE_SESSIONS_PER_SUBJECT = 30
    STALL_TARGET = 5
    MENU_ITEMS_PER_STALL = 10
    ORDER_TARGET = 200
    CLASS_SLOT_SPECS = [
        (time(hour=9, minute=0), time(hour=10, minute=0)),
        (time(hour=10, minute=0), time(hour=11, minute=0)),
        (time(hour=11, minute=0), time(hour=12, minute=0)),
        (time(hour=14, minute=0), time(hour=15, minute=0)),
        (time(hour=15, minute=0), time(hour=16, minute=0)),
    ]
    WEEK_DAYS = ["MON", "TUE", "WED", "THU", "FRI"]

    def __init__(self):
        super().__init__()
        self.faker = Faker() if Faker else None
        self._roll_start = 200000
        self._used_rolls = set(StudentProfile.objects.values_list("roll_no", flat=True))

    def handle(self, *args, **options):
        random.seed()
        with transaction.atomic():
            departments = self._ensure_departments()
            courses = self._ensure_courses(departments)
            sections = self._ensure_sections(courses)
            faculty_users = self._ensure_faculty_users(departments)
            student_users = self._ensure_student_users(sections)
            subjects = self._ensure_subjects(departments, courses)

            self._assign_faculty_to_subjects(subjects, faculty_users)
            self._enroll_students(section_map=self._build_section_student_map(student_users), sections=sections, subjects=subjects)
            self._generate_class_schedules(sections)
            self._generate_attendance_history(subjects, sections)

            stalls, menu_items = self._ensure_canteen_catalog()
            timeslots = self._ensure_canteen_timeslots()
            self._generate_canteen_orders(student_users, stalls, menu_items, timeslots)

        self.stdout.write(self.style.SUCCESS("University seed data generated successfully."))

    def _ensure_departments(self):
        department_names = [
            "Computer Science",
            "Electronics",
            "Business Administration",
            "Mechanical Engineering",
        ]
        departments = []
        for name in department_names:
            dept, _ = Department.objects.get_or_create(name=name)
            departments.append(dept)
        return departments

    def _ensure_courses(self, departments):
        course_specs = [
            ("B.Tech CSE", "Computer Science", 4),
            ("B.Sc Data Science", "Computer Science", 3),
            ("B.Tech ECE", "Electronics", 4),
            ("MBA", "Business Administration", 2),
            ("BBA", "Business Administration", 3),
            ("B.Tech Mechanical", "Mechanical Engineering", 4),
        ]
        dept_map = {dept.name: dept for dept in departments}
        courses = []
        for course_name, dept_name, duration in course_specs:
            course, _ = Course.objects.get_or_create(
                course_name=course_name,
                department=dept_map[dept_name],
                defaults={"duration_years": duration},
            )
            if course.duration_years != duration:
                course.duration_years = duration
                course.save(update_fields=["duration_years"])
            courses.append(course)
        return courses

    def _ensure_sections(self, courses):
        existing_sections = list(Section.objects.select_related("course").all())
        if len(existing_sections) >= self.SECTION_TARGET:
            for section in existing_sections[: self.SECTION_TARGET]:
                if section.capacity != 60:
                    section.capacity = 60
                    section.save(update_fields=["capacity"])
            return existing_sections

        created_sections = []
        section_labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        for idx in range(self.SECTION_TARGET - len(existing_sections)):
            course = random.choice(courses)
            year = random.randint(1, min(4, max(1, course.duration_years)))
            label = section_labels[(len(existing_sections) + idx) % len(section_labels)]
            section = Section.objects.create(
                name=f"SEC-{label}",
                course=course,
                year=year,
                capacity=60,
            )
            created_sections.append(section)
        return existing_sections + created_sections

    def _ensure_faculty_users(self, departments):
        faculty_users = list(User.objects.filter(role="FACULTY").order_by("user_id"))
        to_create = max(0, self.FACULTY_TARGET - len(faculty_users))

        for _ in range(to_create):
            user_id = self._next_user_id("FAC")
            user = User.objects.create(
                user_id=user_id,
                password="faculty123",
                role="FACULTY",
                is_active=True,
            )
            FacultyProfile.objects.get_or_create(
                user=user,
                defaults={
                    "name": self._fake_name(),
                    "department": random.choice(departments),
                },
            )
            faculty_users.append(user)

        for user in faculty_users:
            FacultyProfile.objects.get_or_create(
                user=user,
                defaults={
                    "name": self._fake_name(),
                    "department": random.choice(departments),
                },
            )
        return faculty_users

    def _ensure_student_users(self, sections):
        student_users = list(User.objects.filter(role="STUDENT").order_by("user_id"))
        to_create = max(0, self.STUDENT_TARGET - len(student_users))

        for _ in range(to_create):
            user_id = self._next_user_id("STU")
            section = random.choice(sections)
            user = User.objects.create(
                user_id=user_id,
                password="student123",
                role="STUDENT",
                is_active=True,
            )
            StudentProfile.objects.create(
                user=user,
                name=self._fake_name(),
                roll_no=self._next_roll_no(),
                department=section.course.department,
                course=section.course,
                section=section,
                admission_year=random.randint(2021, 2025),
                parent_contact=self._fake_phone(),
            )
            student_users.append(user)

        for user in student_users:
            if not StudentProfile.objects.filter(user=user).exists():
                section = random.choice(sections)
                StudentProfile.objects.create(
                    user=user,
                    name=self._fake_name(),
                    roll_no=self._next_roll_no(),
                    department=section.course.department,
                    course=section.course,
                    section=section,
                    admission_year=random.randint(2021, 2025),
                    parent_contact=self._fake_phone(),
                )
        return student_users

    def _ensure_subjects(self, departments, courses):
        subjects = list(Subject.objects.select_related("course", "department").all())

        subject_specs = [
            ("CS101", "Programming Fundamentals"),
            ("CS102", "Data Structures"),
            ("CS201", "Database Systems"),
            ("CS202", "Operating Systems"),
            ("DS101", "Statistics for Data Science"),
            ("DS201", "Machine Learning Basics"),
            ("EC101", "Digital Electronics"),
            ("EC201", "Signals and Systems"),
            ("ME101", "Engineering Mechanics"),
            ("ME201", "Thermodynamics"),
            ("BA101", "Business Economics"),
            ("BA201", "Marketing Principles"),
        ]
        for code, name in subject_specs * 3:
            course = random.choice(courses)
            semester_max = max(1, min(8, course.duration_years * 2))
            Subject.objects.get_or_create(
                subject_code=f"{code}-{course.id}",
                course=course,
                defaults={
                    "subject_name": f"{name} ({course.course_name})",
                    "department": course.department,
                    "semester": random.randint(1, semester_max),
                },
            )
        subjects = list(Subject.objects.select_related("course", "department").all())
        target_subjects = max(18, len(courses) * 3)
        while len(subjects) < target_subjects:
            course = random.choice(courses)
            semester_max = max(1, min(8, course.duration_years * 2))
            subject = Subject.objects.create(
                subject_code=f"GEN{random.randint(100, 999)}-{course.id}-{len(subjects)+1}",
                subject_name=f"Elective {len(subjects)+1}",
                department=course.department,
                course=course,
                semester=random.randint(1, semester_max),
            )
            subjects.append(subject)
        return subjects

    def _assign_faculty_to_subjects(self, subjects, faculty_users):
        for subject in subjects:
            selected_faculty = random.choice(faculty_users)
            if subject.faculty_id != selected_faculty.user_id:
                subject.faculty = selected_faculty
                subject.department = subject.course.department
                subject.save(update_fields=["faculty", "department"])

    def _build_section_student_map(self, student_users):
        section_map = {}
        profiles = StudentProfile.objects.filter(user__in=student_users).select_related("section")
        for profile in profiles:
            section_map.setdefault(profile.section_id, []).append(profile.user)
        return section_map

    def _enroll_students(self, section_map, sections, subjects):
        subjects_by_course = {}
        for subject in subjects:
            subjects_by_course.setdefault(subject.course_id, []).append(subject)

        enrollments_to_create = []
        existing_pairs = set(
            Enrollment.objects.values_list("student_id", "subject_id")
        )
        for section in sections:
            section_students = section_map.get(section.id, [])
            if not section_students:
                continue
            course_subjects = subjects_by_course.get(section.course_id, [])
            if not course_subjects:
                continue
            random.shuffle(course_subjects)
            picked_subjects = course_subjects[: min(len(course_subjects), random.randint(4, 6))]

            for student in section_students:
                for subject in picked_subjects:
                    key = (student.user_id, subject.id)
                    if key in existing_pairs:
                        continue
                    enrollments_to_create.append(Enrollment(student=student, subject=subject))
                    existing_pairs.add(key)

        if enrollments_to_create:
            Enrollment.objects.bulk_create(enrollments_to_create, batch_size=1000)

    def _generate_attendance_history(self, subjects, sections):
        section_ids_by_course = {}
        for section in sections:
            section_ids_by_course.setdefault(section.course_id, []).append(section.id)

        today = date.today()
        candidate_dates = []
        for day_offset in range(1, 180):
            d = today - timedelta(days=day_offset)
            if d.weekday() < 5:
                candidate_dates.append(d)

        for subject in subjects:
            possible_section_ids = section_ids_by_course.get(subject.course_id, [])
            if not possible_section_ids:
                continue

            existing_count = AttendanceSession.objects.filter(subject=subject).count()
            sessions_needed = max(0, self.ATTENDANCE_SESSIONS_PER_SUBJECT - existing_count)
            if sessions_needed == 0:
                continue

            random.shuffle(candidate_dates)
            created_sessions = []
            for d in candidate_dates:
                if len(created_sessions) >= sessions_needed:
                    break
                section_id = random.choice(possible_section_ids)
                start_hour = random.choice([9, 10, 11, 13, 14, 15])
                session, created = AttendanceSession.objects.get_or_create(
                    subject=subject,
                    section_id=section_id,
                    date=d,
                    defaults={
                        "start_time": time(hour=start_hour, minute=0),
                        "end_time": time(hour=min(23, start_hour + 1), minute=0),
                        "marked_by": subject.faculty,
                        "method": "MANUAL",
                        "confirmed": True,
                    },
                )
                if created:
                    created_sessions.append(session)

            for session in created_sessions:
                self._mark_session_attendance(session)

    def _mark_session_attendance(self, session):
        students = list(
            StudentProfile.objects.filter(section=session.section)
            .values_list("user_id", flat=True)
        )
        if not students:
            return

        present_ratio = random.uniform(0.70, 0.95)
        records_to_create = []
        existing_students = set(
            AttendanceRecord.objects.filter(session=session).values_list("student_id", flat=True)
        )
        for student_id in students:
            if student_id in existing_students:
                continue
            status = "PRESENT" if random.random() <= present_ratio else "ABSENT"
            records_to_create.append(
                AttendanceRecord(
                    session=session,
                    student_id=student_id,
                    status=status,
                    verified_by_faculty=True,
                )
            )
        if records_to_create:
            AttendanceRecord.objects.bulk_create(records_to_create, batch_size=1000)

    def _generate_class_schedules(self, sections):
        room_pool = [f"Room-{room_no}" for room_no in range(101, 131)]
        for section in sections:
            subject_ids = list(
                Enrollment.objects.filter(student__studentprofile__section=section)
                .values_list("subject_id", flat=True)
                .distinct()
            )
            if not subject_ids:
                continue

            for subject_id in subject_ids:
                subject = Subject.objects.filter(id=subject_id).select_related("faculty").first()
                if not subject or not subject.faculty_id:
                    continue

                existing_for_subject = ClassSchedule.objects.filter(
                    section=section,
                    subject=subject,
                ).count()

                target_for_subject = random.randint(3, 4)
                to_create = max(0, target_for_subject - existing_for_subject)
                if to_create == 0:
                    continue

                for _ in range(to_create):
                    occupied = set(
                        ClassSchedule.objects.filter(section=section)
                        .values_list("day_of_week", "start_time")
                    )
                    available_slots = [
                        (day, slot_start, slot_end)
                        for day in self.WEEK_DAYS
                        for slot_start, slot_end in self.CLASS_SLOT_SPECS
                        if (day, slot_start) not in occupied
                    ]
                    if not available_slots:
                        break

                    day_of_week, start_t, end_t = random.choice(available_slots)
                    ClassSchedule.objects.get_or_create(
                        section=section,
                        day_of_week=day_of_week,
                        start_time=start_t,
                        defaults={
                            "subject": subject,
                            "faculty": subject.faculty,
                            "end_time": end_t,
                            "room": random.choice(room_pool),
                        },
                    )

    def _ensure_canteen_catalog(self):
        stall_names = ["North Cafe", "Central Bites", "Green Bowl", "Quick Sip", "Campus Grill"]
        menu_bases = [
            ("Veg Sandwich", "Snacks", Decimal("60.00")),
            ("Paneer Wrap", "Snacks", Decimal("85.00")),
            ("Idli Plate", "Breakfast", Decimal("50.00")),
            ("Masala Dosa", "Breakfast", Decimal("80.00")),
            ("Pasta Bowl", "Meals", Decimal("120.00")),
            ("Fried Rice", "Meals", Decimal("110.00")),
            ("Lemon Tea", "Beverage", Decimal("25.00")),
            ("Cold Coffee", "Beverage", Decimal("70.00")),
            ("Fruit Salad", "Healthy", Decimal("65.00")),
            ("Brownie", "Dessert", Decimal("55.00")),
        ]

        stalls = []
        for name in stall_names[: self.STALL_TARGET]:
            stall, _ = Stall.objects.get_or_create(
                name=name,
                defaults={
                    "location": f"Block {random.choice(['A', 'B', 'C'])}",
                    "max_orders_per_slot": random.randint(35, 60),
                    "average_prep_time": random.randint(8, 18),
                    "rating": round(random.uniform(3.8, 4.8), 1),
                    "is_active": True,
                },
            )
            stalls.append(stall)

        menu_items_by_stall = {}
        for stall in stalls:
            stall_items = list(MenuItem.objects.filter(stall=stall).order_by("id"))
            if len(stall_items) < self.MENU_ITEMS_PER_STALL:
                existing_names = {item.name for item in stall_items}
                for base_name, category, base_price in menu_bases:
                    if len(stall_items) >= self.MENU_ITEMS_PER_STALL:
                        break
                    item_name = f"{base_name} {stall.name.split()[0]}"
                    if item_name in existing_names:
                        continue
                    item = MenuItem.objects.create(
                        stall=stall,
                        name=item_name,
                        category=category,
                        price=base_price + Decimal(random.randint(0, 20)),
                        is_available=True,
                    )
                    stall_items.append(item)
                    existing_names.add(item_name)
            menu_items_by_stall[stall.id] = stall_items[: self.MENU_ITEMS_PER_STALL]
        return stalls, menu_items_by_stall

    def _ensure_canteen_timeslots(self):
        slot_specs = [
            (8, 9, "SHORT"),
            (9, 10, "SHORT"),
            (10, 11, "SHORT"),
            (12, 13, "LUNCH"),
            (13, 14, "LUNCH"),
            (14, 15, "LUNCH"),
        ]
        slots = []
        for start_h, end_h, break_type in slot_specs:
            slot, _ = TimeSlot.objects.get_or_create(
                start_time=time(hour=start_h, minute=0),
                end_time=time(hour=end_h, minute=0),
                break_type=break_type,
                defaults={"is_active": True},
            )
            if not slot.is_active:
                slot.is_active = True
                slot.save(update_fields=["is_active"])
            slots.append(slot)
        return slots

    def _generate_canteen_orders(self, student_users, stalls, menu_items_by_stall, timeslots):
        if not student_users or not stalls or not timeslots:
            return

        status_choices = ["PENDING", "PREPARING", "READY", "COMPLETED", "CANCELLED"]
        status_weights = [0.15, 0.20, 0.20, 0.35, 0.10]

        for _ in range(self.ORDER_TARGET):
            student = random.choice(student_users)
            stall = random.choice(stalls)
            slot = random.choice(timeslots)
            status = random.choices(status_choices, weights=status_weights, k=1)[0]

            order = Order.objects.create(
                student=student,
                stall=stall,
                timeslot=slot,
                status=status,
                estimated_wait_time=round(random.uniform(5, 30), 2),
                recommendation_used=random.choice([True, False]),
                total_price=Decimal("0.00"),
            )

            available_items = menu_items_by_stall.get(stall.id, [])
            if not available_items:
                continue
            picked_count = random.randint(1, min(3, len(available_items)))
            picked_items = random.sample(available_items, k=picked_count)

            order_items = []
            total_price = Decimal("0.00")
            for item in picked_items:
                qty = random.randint(1, 3)
                order_items.append(OrderItem(order=order, menu_item=item, quantity=qty))
                total_price += item.price * qty

            OrderItem.objects.bulk_create(order_items)
            order.total_price = total_price.quantize(Decimal("0.01"))
            order.save(update_fields=["total_price"])

            past_dt = timezone.make_aware(
                datetime.combine(
                    date.today() - timedelta(days=random.randint(1, 60)),
                    time(hour=random.choice([8, 9, 10, 12, 13, 14]), minute=random.choice([0, 15, 30, 45])),
                )
            )
            Order.objects.filter(pk=order.pk).update(order_time=past_dt)

    def _next_user_id(self, prefix):
        while True:
            candidate = f"{prefix}{random.randint(10000, 99999)}"
            if not User.objects.filter(user_id=candidate).exists():
                return candidate

    def _next_roll_no(self):
        while self._roll_start in self._used_rolls:
            self._roll_start += 1
        roll_no = self._roll_start
        self._used_rolls.add(roll_no)
        self._roll_start += 1
        return roll_no

    def _fake_name(self):
        if self.faker:
            return self.faker.name()
        first = random.choice(["Aarav", "Isha", "Karan", "Meera", "Rohit", "Nisha", "Sanjay", "Pooja"])
        last = random.choice(["Sharma", "Patel", "Singh", "Reddy", "Gupta", "Nair", "Mehta", "Das"])
        return f"{first} {last}"

    def _fake_phone(self):
        if self.faker:
            return self.faker.msisdn()[:10]
        return f"9{random.randint(100000000, 999999999)}"
