from django.shortcuts import render

from django.views.decorators.cache import cache_page

from rest_framework.decorators import api_view, permission_classes

from rest_framework.permissions import AllowAny

from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from .models import StudentProfile

from .serializers import (
    StudentProfileSerializer,
    CustomTokenSerializer
)


@cache_page(60 * 5)

@api_view(['GET'])

@permission_classes([AllowAny])

def student_list_api(request):

    students = StudentProfile.objects.all()[:20]

    serializer = StudentProfileSerializer(
        students,
        many=True
    )

    return Response(serializer.data)


@api_view(['POST'])

@permission_classes([AllowAny])

def custom_token_obtain_view(request):

    serializer = CustomTokenSerializer(
        data=request.data
    )

    serializer.is_valid(
        raise_exception=True
    )

    user = serializer.validated_data["user"]

    refresh = RefreshToken()

    refresh['user_id'] = user.user_id

    refresh['role'] = user.role

    return Response({

        "refresh": str(refresh),

        "access": str(refresh.access_token),

        "user_id": user.user_id,

        "role": user.role,
    })