import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import FacultyProfile, StudentProfile, User
from academics.models import (
    ClassSchedule,
    Course,
    Department,
    Enrollment,
    Section,
    Subject,
)
from attendance.models import AttendanceRecord, AttendanceSession
from canteen.models import MenuItem, Order, OrderItem, Stall, TimeSlot

try:
    from faker import Faker
except ImportError:
    Faker = None


class Command(BaseCommand):

    help = "Seed realistic university ecosystem"

    FACULTY_TARGET = 15
    STUDENT_TARGET = 450
    SECTION_TARGET = 12

    ATTENDANCE_SESSIONS_PER_SUBJECT = 30

    ORDER_TARGET = 700

    CLASS_SLOT_SPECS = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
    ]

    WEEK_DAYS = [
        "MON",
        "TUE",
        "WED",
        "THU",
        "FRI",
    ]

    STUDENT_PERSONA_WEIGHTS = {
        "TOPPER": 15,
        "AVERAGE": 45,
        "AT_RISK": 20,
        "CHRONIC_ABSENTEE": 10,
        "CANTEEN_HEAVY": 10,
    }

    FACULTY_PERSONA_WEIGHTS = {
        "HIGHLY_ACTIVE": 30,
        "NORMAL": 50,
        "OVERLOADED": 15,
        "INACTIVE": 5,
    }

    def __init__(self):
        super().__init__()

        self.faker = Faker() if Faker else None

        self.student_personas = {}
        self.faculty_personas = {}

        self._used_rolls = set(
            StudentProfile.objects.values_list(
                "roll_no",
                flat=True
            )
        )

        self._roll_counter = 200000

    def handle(self, *args, **options):

        random.seed()

        with transaction.atomic():

            departments = self._ensure_departments()

            courses = self._ensure_courses(
                departments
            )

            sections = self._ensure_sections(
                courses
            )

            faculty_users = self._ensure_faculty_users(
                departments
            )

            student_users = self._ensure_student_users(
                sections
            )

            subjects = self._ensure_subjects(
                courses
            )

            self._assign_faculty_to_subjects(
                subjects,
                faculty_users
            )

            self._create_enrollments(
                sections,
                subjects
            )

            self._generate_class_schedules(
                sections
            )

            self._generate_attendance_history(
                subjects,
                sections
            )

            stalls, menu_items = (
                self._ensure_canteen_data()
            )

            slots = self._ensure_timeslots()

            self._generate_orders(
                student_users,
                stalls,
                menu_items,
                slots,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Realistic university ecosystem generated successfully."
            )
        )

    # =====================================================
    # DEPARTMENTS
    # =====================================================

    def _ensure_departments(self):

        names = [
            "Computer Science",
            "Electronics",
            "Business Administration",
            "Mechanical Engineering",
        ]

        departments = []

        for name in names:

            dept, _ = Department.objects.get_or_create(
                name=name
            )

            departments.append(dept)

        return departments

    # =====================================================
    # COURSES
    # =====================================================

    def _ensure_courses(self, departments):

        dept_map = {
            d.name: d for d in departments
        }

        specs = [
            ("B.Tech CSE", "Computer Science", 4),
            ("B.Sc Data Science", "Computer Science", 3),
            ("B.Tech ECE", "Electronics", 4),
            ("MBA", "Business Administration", 2),
            ("BBA", "Business Administration", 3),
        ]

        courses = []

        for name, dept_name, duration in specs:

            course, _ = Course.objects.get_or_create(
                course_name=name,
                department=dept_map[dept_name],
                defaults={
                    "duration_years": duration
                }
            )

            courses.append(course)

        return courses

    # =====================================================
    # SECTIONS
    # =====================================================

    def _ensure_sections(self, courses):

        existing = list(Section.objects.all())

        if len(existing) >= self.SECTION_TARGET:
            return existing

        capacities = [
            40, 45, 50, 55,
            60, 65, 70, 80,
            90, 100, 110, 120
        ]

        labels = list("ABCDEFGHIJKL")

        created = []

        for idx in range(self.SECTION_TARGET):

            course = random.choice(courses)

            section, _ = Section.objects.get_or_create(
                name=f"SEC-{labels[idx]}",
                course=course,
                defaults={
                    "year": random.randint(1, 4),
                    "capacity": capacities[idx]
                }
            )

            created.append(section)

        return created

    # =====================================================
    # FACULTY
    # =====================================================

    def _assign_faculty_persona(self):

        return random.choices(
            list(self.FACULTY_PERSONA_WEIGHTS.keys()),
            weights=list(self.FACULTY_PERSONA_WEIGHTS.values()),
            k=1
        )[0]

    def _ensure_faculty_users(self, departments):

        faculty_users = []

        for _ in range(self.FACULTY_TARGET):

            user = User.objects.create(
                user_id=self._next_user_id("FAC"),
                role="FACULTY",
                is_active=random.choices(
                    [True, False],
                    weights=[92, 8],
                    k=1
                )[0]
            )

            user.set_password("faculty123")
            user.save()

            FacultyProfile.objects.create(
                user=user,
                name=self._fake_name(),
                department=random.choice(departments)
            )

            self.faculty_personas[
                user.user_id
            ] = self._assign_faculty_persona()

            faculty_users.append(user)

        return faculty_users

    # =====================================================
    # STUDENTS
    # =====================================================

    def _assign_student_persona(self):

        return random.choices(
            list(self.STUDENT_PERSONA_WEIGHTS.keys()),
            weights=list(self.STUDENT_PERSONA_WEIGHTS.values()),
            k=1
        )[0]

    def _ensure_student_users(self, sections):

        student_users = []

        overloaded_sections = random.sample(
            sections,
            k=3
        )

        for _ in range(self.STUDENT_TARGET):

            section = random.choice(sections)

            if random.random() < 0.35:
                section = random.choice(
                    overloaded_sections
                )

            user = User.objects.create(
                user_id=self._next_user_id("STU"),
                role="STUDENT",
                is_active=True
            )

            user.set_password("student123")
            user.save()

            StudentProfile.objects.create(
                user=user,
                name=self._fake_name(),
                roll_no=self._next_roll_no(),
                department=section.course.department,
                course=section.course,
                section=section,
                admission_year=random.randint(2021, 2025),
                parent_contact=self._fake_phone()
            )

            self.student_personas[
                user.user_id
            ] = self._assign_student_persona()

            student_users.append(user)

        return student_users

    # =====================================================
    # SUBJECTS
    # =====================================================

    def _ensure_subjects(self, courses):

        specs = [
            "Programming Fundamentals",
            "Data Structures",
            "Database Systems",
            "Operating Systems",
            "Cloud Computing",
            "Machine Learning",
            "Artificial Intelligence",
            "Computer Networks",
            "Statistics",
            "Marketing",
        ]

        subjects = []

        counter = 100

        for course in courses:

            for name in specs:

                counter += 1

                subject, _ = Subject.objects.get_or_create(
                    subject_code=f"SUB{counter}",
                    course=course,
                    defaults={
                        "subject_name": name,
                        "department": course.department,
                        "semester": random.randint(1, 8)
                    }
                )

                subjects.append(subject)

        return subjects

    # =====================================================
    # FACULTY ASSIGNMENT
    # =====================================================

    def _assign_faculty_to_subjects(
        self,
        subjects,
        faculty_users
    ):

        for subject in subjects:

            subject.faculty = random.choice(
                faculty_users
            )

            subject.save()

    # =====================================================
    # ENROLLMENTS
    # =====================================================

    def _create_enrollments(
        self,
        sections,
        subjects
    ):

        Enrollment.objects.all().delete()

        for section in sections:

            students = StudentProfile.objects.filter(
                section=section
            )

            course_subjects = Subject.objects.filter(
                course=section.course
            )[:5]

            for student in students:

                for subject in course_subjects:

                    Enrollment.objects.create(
                        student=student.user,
                        subject=subject
                    )

    # =====================================================
    # CLASS SCHEDULES
    # =====================================================

    def _generate_class_schedules(
        self,
        sections
    ):

        used_slots = set()

        rooms = [
            f"Room-{i}"
            for i in range(101, 141)
        ]

        for section in sections:

            subjects = Subject.objects.filter(
                course=section.course
            )[:5]

            for subject in subjects:

                weekly_classes = random.randint(3, 5)

                created = 0
                attempts = 0

                while (
                    created < weekly_classes
                    and attempts < 100
                ):

                    attempts += 1

                    day = random.choice(
                        self.WEEK_DAYS
                    )

                    start_t, end_t = random.choice(
                        self.CLASS_SLOT_SPECS
                    )

                    slot_key = (
                        section.id,
                        day,
                        start_t
                    )

                    if slot_key in used_slots:
                        continue

                    used_slots.add(slot_key)

                    ClassSchedule.objects.create(
                        section=section,
                        subject=subject,
                        faculty=subject.faculty,
                        day_of_week=day,
                        start_time=start_t,
                        end_time=end_t,
                        room=random.choice(rooms)
                    )

                    created += 1

    # =====================================================
    # ATTENDANCE
    # =====================================================

    def _get_attendance_probability(
        self,
        student_id
    ):

        persona = self.student_personas.get(
            student_id,
            "AVERAGE"
        )

        mapping = {
            "TOPPER": random.uniform(0.93, 0.99),
            "AVERAGE": random.uniform(0.76, 0.90),
            "AT_RISK": random.uniform(0.55, 0.74),
            "CHRONIC_ABSENTEE": random.uniform(0.30, 0.55),
            "CANTEEN_HEAVY": random.uniform(0.70, 0.85),
        }

        return mapping.get(persona, 0.80)

    def _generate_attendance_history(
        self,
        subjects,
        sections
    ):

        used_attendance_slots = set()

        dates = []

        for offset in range(1, 180):

            d = date.today() - timedelta(days=offset)

            if d.weekday() < 5:
                dates.append(d)

        for subject in subjects:

            possible_sections = Section.objects.filter(
                course=subject.course
            )

            for _ in range(
                self.ATTENDANCE_SESSIONS_PER_SUBJECT
            ):

                attempts = 0

                while True:

                    attempts += 1

                    if attempts > 50:
                        break

                    possible_sections_list = list(possible_sections)

                    if not possible_sections_list:
                        continue

                    section = random.choice(possible_sections_list)

                    session_date = random.choice(
                        dates
                    )

                    key = (
                        subject.id,
                        session_date,
                        section.id
                    )

                    if key not in used_attendance_slots:

                        used_attendance_slots.add(
                            key
                        )

                        break

                session = AttendanceSession.objects.create(
                    subject=subject,
                    section=section,
                    date=session_date,
                    start_time=time(
                        hour=random.choice(
                            [9, 10, 11, 14, 15]
                        )
                    ),
                    end_time=time(
                        hour=random.choice(
                            [10, 11, 12, 15, 16]
                        )
                    ),
                    marked_by=subject.faculty,
                    method="MANUAL",
                    confirmed=True
                )

                self._mark_attendance(session)

    def _mark_attendance(self, session):

        students = StudentProfile.objects.filter(
            section=session.section
        )

        records = []

        for student in students:

            probability = (
                self._get_attendance_probability(
                    student.user_id
                )
            )

            if session.date.weekday() == 0:
                probability -= 0.05

            status = (
                "PRESENT"
                if random.random() <= probability
                else "ABSENT"
            )

            records.append(
                AttendanceRecord(
                    session=session,
                    student=student.user,
                    status=status,
                    verified_by_faculty=True
                )
            )

        AttendanceRecord.objects.bulk_create(
            records
        )

    # =====================================================
    # CANTEEN
    # =====================================================

    def _ensure_canteen_data(self):

        stall_names = [
            "North Cafe",
            "Campus Grill",
            "Quick Sip",
            "Green Bowl",
            "Central Bites",
        ]

        menu_names = [
            ("Veg Sandwich", 60),
            ("Paneer Wrap", 80),
            ("Cold Coffee", 70),
            ("Fried Rice", 120),
            ("Fruit Salad", 65),
            ("Brownie", 50),
            ("Masala Dosa", 90),
            ("Pasta Bowl", 130),
        ]

        stalls = []
        menu_map = {}

        for stall_name in stall_names:

            stall = Stall.objects.create(
                name=stall_name,
                location=f"Block-{random.choice(['A', 'B', 'C'])}",
                max_orders_per_slot=random.randint(40, 90),
                average_prep_time=random.randint(5, 20),
                rating=round(
                    random.uniform(3.5, 4.9),
                    1
                ),
                is_active=True
            )

            stalls.append(stall)

            items = []

            for item_name, price in menu_names:

                item = MenuItem.objects.create(
                    stall=stall,
                    name=item_name,
                    price=Decimal(price),
                    is_available=True
                )

                items.append(item)

            menu_map[stall.id] = items

        return stalls, menu_map

    # =====================================================
    # TIMESLOTS
    # =====================================================

    def _ensure_timeslots(self):

        specs = [
            (8, 9, "SHORT"),
            (9, 10, "SHORT"),
            (12, 13, "LUNCH"),
            (13, 14, "LUNCH"),
            (14, 15, "LUNCH"),
        ]

        slots = []

        for start_h, end_h, typ in specs:

            slot = TimeSlot.objects.create(
                start_time=time(start_h),
                end_time=time(end_h),
                break_type=typ,
                is_active=True
            )

            slots.append(slot)

        return slots

    # =====================================================
    # ORDERS
    # =====================================================

    def _generate_orders(
        self,
        student_users,
        stalls,
        menu_items,
        slots
    ):

        for _ in range(self.ORDER_TARGET):

            student = random.choice(
                student_users
            )

            stall = random.choice(stalls)

            slot = random.choice(slots)

            order = Order.objects.create(
                student=student,
                stall=stall,
                timeslot=slot,
                status=random.choice([
                    "PENDING",
                    "PREPARING",
                    "READY",
                    "COMPLETED"
                ]),
                estimated_wait_time=random.randint(
                    5,
                    35
                ),
                recommendation_used=random.choice(
                    [True, False]
                ),
                total_price=Decimal("0.00")
            )

            selected_items = random.sample(
                menu_items[stall.id],
                k=random.randint(1, 3)
            )

            total = Decimal("0.00")

            for item in selected_items:

                qty = random.randint(1, 3)

                OrderItem.objects.create(
                    order=order,
                    menu_item=item,
                    quantity=qty
                )

                total += item.price * qty

            order.total_price = total

            order.order_time = timezone.make_aware(
                datetime.combine(
                    date.today() - timedelta(
                        days=random.randint(1, 45)
                    ),
                    time(
                        hour=random.choice(
                            [8, 9, 10, 12, 13, 14]
                        ),
                        minute=random.choice(
                            [0, 15, 30, 45]
                        )
                    )
                )
            )

            order.save()

    # =====================================================
    # HELPERS
    # =====================================================

    def _next_user_id(self, prefix):

        while True:

            candidate = (
                f"{prefix}{random.randint(10000, 99999)}"
            )

            if not User.objects.filter(
                user_id=candidate
            ).exists():

                return candidate

    def _next_roll_no(self):

        while self._roll_counter in self._used_rolls:
            self._roll_counter += 1

        value = self._roll_counter

        self._used_rolls.add(value)

        self._roll_counter += 1

        return value

    def _fake_name(self):

        if self.faker:
            return self.faker.name()

        return random.choice([
            "Aarav Sharma",
            "Isha Gupta",
            "Rohit Reddy",
            "Nisha Patel",
            "Meera Das",
        ])

    def _fake_phone(self):

        return f"9{random.randint(100000000, 999999999)}"