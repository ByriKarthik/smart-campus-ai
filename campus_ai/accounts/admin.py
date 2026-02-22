from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import User, StudentProfile, FacultyProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'role', 'is_active')
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


admin.site.register(StudentProfile)
admin.site.register(FacultyProfile)
