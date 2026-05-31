from rest_framework import serializers


class SubjectAttendanceSerializer(
    serializers.Serializer
):

    subject = serializers.CharField()

    present_classes = serializers.IntegerField()

    absent_classes = serializers.IntegerField()

    attendance_percentage = serializers.FloatField()


class StudentAttendanceSerializer(
    serializers.Serializer
):

    student_id = serializers.CharField()

    student_name = serializers.CharField()

    overall_attendance = serializers.FloatField()

    subjects = SubjectAttendanceSerializer(
        many=True
    )