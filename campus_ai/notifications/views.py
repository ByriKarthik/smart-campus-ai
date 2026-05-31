from rest_framework.decorators import api_view

from rest_framework.response import Response

from rest_framework import status

from .tasks import send_attendance_alert


@api_view(['POST'])

def trigger_alert(request):

    student_name = request.data.get(
        "student_name",
        "Unknown Student"
    )

    task = send_attendance_alert.delay(
        student_name
    )

    return Response({

        "message": "Alert task queued",

        "student_name": student_name,

        "task_id": task.id

    }, status=status.HTTP_201_CREATED)