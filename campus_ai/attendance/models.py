from django.db import models
from accounts.models import User
from academics.models import Subject


class AttendanceSession(models.Model):
    """
    Represents one attendance event for a subject & section.
    """

    METHOD_CHOICES = [
        ('MANUAL', 'Manual'),
        ('FACE', 'Face Recognition'),
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )
    section = models.ForeignKey(
        'academics.Section',
        on_delete=models.CASCADE
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'FACULTY'}
    )

    method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES,
        help_text="How attendance was generated (Manual / Face Recognition)"
    )

    confirmed = models.BooleanField(
        default=False,
        help_text="Final confirmation by faculty"
    )
    class Meta:
        unique_together = ('subject', 'date', 'section')
    def __str__(self):
        return f"{self.subject.subject_code} | {self.date} | Section {self.section}"


class AttendanceRecord(models.Model):
    """
    Individual student attendance record for a session.
    """

    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
    ]

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records'
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'}
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Face recognition confidence (0–1). Null for manual attendance."
    )

    verified_by_faculty = models.BooleanField(
        default=False,
        help_text="Faculty has verified this record"
    )

    class Meta:
        unique_together = ('session', 'student')
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"

    def __str__(self):
        return (
            f"{self.student.user_id} | "
            f"{self.session.subject.subject_code} | "
            f"{self.status}"
        )
