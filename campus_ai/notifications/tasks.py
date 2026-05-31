from celery import shared_task

import time


@shared_task
def send_attendance_alert(student_name):

    print(
        f"Sending attendance alert to {student_name}"
    )

    time.sleep(5)

    return f"Alert sent to {student_name}"