from django.db import models
from accounts.models import User


class NotificationLog(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
        ('INFO', 'Info'),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'}
    )
    message = models.TextField()
    notification_type = models.CharField(
        max_length=10,
        choices=NOTIFICATION_TYPE_CHOICES
    )
    triggered_on = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.notification_type} - {self.student.user_id}"
