import base64
import os
import uuid
import numpy as np
import cv2

from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.models import User
from .models import FaceEmbedding


def face_enroll(request, user_id):
    student = get_object_or_404(User, user_id=user_id, role='STUDENT')

    if request.method == 'POST':
        captured_image = request.POST.get('captured_image')
        uploaded_image = request.FILES.get('uploaded_image')

        # 🔹 Step 1: get image
        if captured_image:
            header, imgstr = captured_image.split(';base64,')
            image_bytes = base64.b64decode(imgstr)
            filename = f"{student.user_id}_{uuid.uuid4().hex}.png"
        elif uploaded_image:
            image_bytes = uploaded_image.read()
            filename = uploaded_image.name
        else:
            messages.error(request, "No image provided")
            return redirect(request.path)

        # 🔹 Step 2: save image
        faces_dir = os.path.join(settings.MEDIA_ROOT, 'faces')
        os.makedirs(faces_dir, exist_ok=True)

        image_path = os.path.join(faces_dir, filename)
        with open(image_path, 'wb') as f:
            f.write(image_bytes)

        # 🔹 Step 3: OpenCV face detection
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        cascade_path = os.path.join(
            settings.BASE_DIR,
            'ml',
            'data',
            'haarcascade_frontalface_default.xml'
        )
        face_cascade = cv2.CascadeClassifier(cascade_path)

        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.3, minNeighbors=5
        )

        if len(faces) == 0:
            messages.error(request, "No face detected. Try again.")
            return redirect(request.path)

        # 🔹 Step 4: take first detected face
        x, y, w, h = faces[0]
        face = gray[y:y+h, x:x+w]

        # 🔹 Step 5: normalize face
        face = cv2.resize(face, (100, 100))
        face_vector = face.flatten() / 255.0  # normalize

        # 🔹 Step 6: save embedding
        embed_dir = os.path.join(settings.MEDIA_ROOT, 'embeddings')
        os.makedirs(embed_dir, exist_ok=True)

        embed_path = os.path.join(
            embed_dir, f"{student.user_id}.npy"
        )
        np.save(embed_path, face_vector)

        # 🔹 Step 7: save DB record
        FaceEmbedding.objects.update_or_create(
            student=student,
            defaults={
                'face_image': f"faces/{filename}",
                'embedding_path': embed_path
            }
        )

        messages.success(request, "Face enrolled successfully")
        return redirect('/admin/accounts/user/')

    return render(request, 'ml/face_enroll.html', {
        'student': student
    })
