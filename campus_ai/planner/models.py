from django.db import models

class RemedialSession(models.Model):
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
    )
    section = models.ForeignKey(
        "academics.Section",
        on_delete=models.CASCADE,
    )
    scheduled_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    code = models.CharField(max_length=10, unique=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        limit_choices_to={"role": "FACULTY"},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.subject.subject_code}"


class RemedialAttendance(models.Model):
    session = models.ForeignKey(
        RemedialSession,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        limit_choices_to={"role": "STUDENT"},
    )
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session", "student")

    def __str__(self):
        return f"{self.student.user_id} - {self.session.code}"
