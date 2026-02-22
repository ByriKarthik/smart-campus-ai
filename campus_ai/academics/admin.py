from django.contrib import admin
from .models import Department, Course, Subject, Enrollment, Section, ClassSchedule

admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Section)
admin.site.register(Subject)
admin.site.register(Enrollment)
admin.site.register(ClassSchedule)
