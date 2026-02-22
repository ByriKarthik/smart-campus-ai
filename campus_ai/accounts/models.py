from django.db import models

class User(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('FACULTY', 'Faculty'),
        ('STUDENT', 'Student'),
    ]

    user_id = models.CharField(
        max_length=20,
        primary_key=True
    )
    password = models.CharField(
        max_length=128
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES
    )
    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.user_id

class StudentProfile(models.Model):
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'}
    )
    name = models.CharField(max_length=100)
    roll_no = models.IntegerField()
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        'academics.Course',
        on_delete=models.CASCADE
    )
    section = models.ForeignKey(
        'academics.Section',
        on_delete=models.CASCADE
    )

    admission_year = models.IntegerField()
    parent_contact = models.CharField(max_length=254)

    def __str__(self):
        return f"{self.roll_no} - {self.name}"


class FacultyProfile(models.Model):
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'FACULTY'}
    )
    name = models.CharField(max_length=100)
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name
