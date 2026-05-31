from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import User, StudentProfile, FacultyProfile
from ml.models import FaceEmbedding


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'role', 'is_active', 'face_status', 'enroll_face_action')
    readonly_fields = ('enroll_face_link',)

    fieldsets = (
        (None, {
            'fields': ('user_id', 'password', 'role', 'is_active')
        }),
        ('Face Enrollment', {
            'fields': ('enroll_face_link',),
        }),
    )

    def enroll_face_link(self, obj):
        if obj.role == 'STUDENT':
            url = reverse('face_enroll', args=[obj.user_id])
            return format_html(
                '<a class="button" href="{}">Enroll / Update Face</a>',
                url
            )
        return "Not applicable"

    enroll_face_link.short_description = "Face Enrollment"

    def face_status(self, obj):
        if obj.role != "STUDENT":
            return "-"
        exists = FaceEmbedding.objects.filter(student=obj).exists()
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            "green" if exists else "crimson",
            "Enrolled" if exists else "Not Enrolled",
        )

    face_status.short_description = "Face Status"

    def enroll_face_action(self, obj):
        if obj.role != "STUDENT":
            return "-"
        url = reverse("face_enroll", args=[obj.user_id])
        return format_html('<a href="{}">Enroll Face</a>', url)

    enroll_face_action.short_description = "Face Enrollment"


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "roll_no", "user", "department", "course", "section", "parent_email", "face_status", "enroll_face")
    search_fields = ("name", "roll_no", "user__user_id")
    list_filter = ("department", "course", "section")

    def face_status(self, obj):
        exists = FaceEmbedding.objects.filter(student=obj.user).exists()
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            "green" if exists else "crimson",
            "Enrolled" if exists else "Not Enrolled",
        )

    face_status.short_description = "Face Status"

    def enroll_face(self, obj):
        url = reverse("face_enroll", args=[obj.user.user_id])
        return format_html('<a href="{}">Enroll / Update Face</a>', url)

    enroll_face.short_description = "Face Enrollment"

admin.site.register(FacultyProfile)
