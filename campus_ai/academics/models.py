from django.db import models
from accounts.models import User


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    course_name = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )
    duration_years = models.IntegerField()

    def __str__(self):
        return self.course_name


class Subject(models.Model):
    subject_code = models.CharField(max_length=20)
    subject_name = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    semester = models.IntegerField()
    faculty = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'FACULTY'}
    )
    min_attendance_percentage = models.IntegerField(default=75)

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"


class Enrollment(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'}
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )
    enrolled_on = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student.user_id} enrolled in {self.subject.subject_code}"
class Section(models.Model):
    name = models.CharField(max_length=20)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    year = models.IntegerField()
    capacity = models.IntegerField(default=60)

    def __str__(self):
        return f"{self.course.course_name} - Year {self.year} - {self.name}"


class ClassSchedule(models.Model):
    DAY_CHOICES = [
        ("MON", "Monday"),
        ("TUE", "Tuesday"),
        ("WED", "Wednesday"),
        ("THU", "Thursday"),
        ("FRI", "Friday"),
        ("SAT", "Saturday"),
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
    )
    faculty = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "FACULTY"},
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
    )
    day_of_week = models.CharField(
        max_length=3,
        choices=DAY_CHOICES,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)

    class Meta:
        unique_together = ("section", "day_of_week", "start_time")
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.section} {self.day_of_week} {self.start_time}"
