from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from .models import StudentProfile, User


class StudentProfileSerializer(serializers.ModelSerializer):

    user_id = serializers.CharField(
        source='user.user_id'
    )

    class Meta:
        model = StudentProfile

        fields = [
            'user_id',
            'name',
            'roll_no',
            'admission_year',
            'parent_contact',
        ]

class CustomTokenSerializer(
    serializers.Serializer
):

    user_id = serializers.CharField()

    password = serializers.CharField(
        write_only=True
    )

    def validate(self, data):

        user_id = data.get("user_id")

        password = data.get("password")

        try:

            user = User.objects.get(
                user_id=user_id
            )

        except User.DoesNotExist:

            raise serializers.ValidationError(
                "Invalid credentials"
            )

        if not user.check_password(password):

            raise serializers.ValidationError(
                "Invalid credentials"
            )

        if not user.is_active:

            raise serializers.ValidationError(
                "User account inactive"
            )

        data["user"] = user

        return data