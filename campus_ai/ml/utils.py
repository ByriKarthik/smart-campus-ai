import os
import cv2
import numpy as np
from numpy.linalg import norm
from django.conf import settings


# =========================================================
# LOAD HAAR CASCADE (ONCE)
# =========================================================
CASCADE_PATH = os.path.join(
    settings.BASE_DIR,
    'ml',
    'data',
    'haarcascade_frontalface_default.xml'
)

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

if face_cascade.empty():
    raise RuntimeError("Haar Cascade XML not loaded properly")


# =========================================================
# FACE EMBEDDING EXTRACTION
# =========================================================
def extract_face_embedding(face_img):
    """
    Convert a detected face image into a numeric embedding.
    Steps:
    - Convert to grayscale
    - Resize to fixed size
    - Normalize pixel values
    - Flatten to vector
    """
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)

    # Resize to standard size
    resized = cv2.resize(gray, (100, 100))

    # Normalize (0–1 range)
    normalized = resized / 255.0

    return normalized.flatten().astype("float32")


# =========================================================
# COSINE SIMILARITY
# =========================================================
def cosine_similarity(vec1, vec2):
    """
    Returns similarity score between 0 and 1.
    Higher = more similar.
    """
    if norm(vec1) == 0 or norm(vec2) == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / (norm(vec1) * norm(vec2)))


# =========================================================
# MAIN FUNCTION: AUTO ATTENDANCE
# =========================================================
FACE_MATCH_THRESHOLD = 0.92
def get_present_students(class_image_path, threshold=FACE_MATCH_THRESHOLD):
    """
    Detect faces from class image and match with stored embeddings.

    Returns:
    {
        "STU001": 0.92,
        "STU002": 0.88
    }
    """

    detected_students = {}

    # Load class image
    img = cv2.imread(class_image_path)
    if img is None:
        return detected_students

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces in class image
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=6,
        minSize=(60, 60)
    )

    embeddings_dir = os.path.join(settings.MEDIA_ROOT, 'embeddings')
    if not os.path.exists(embeddings_dir):
        return detected_students

    # For each detected face
    for (x, y, w, h) in faces:
        face_img = img[y:y + h, x:x + w]
        test_embedding = extract_face_embedding(face_img)

        best_match_id = None
        best_similarity = 0.0

        # Compare with stored embeddings
        for file in os.listdir(embeddings_dir):
            if not file.endswith('.npy'):
                continue

            student_id = file.replace('.npy', '')
            stored_embedding = np.load(
                os.path.join(embeddings_dir, file)
            )

            similarity = cosine_similarity(
                test_embedding,
                stored_embedding
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = student_id

        # Accept match only if confidence is strong
        if best_match_id and best_similarity >= threshold:
            detected_students[best_match_id] = round(best_similarity, 2)

    return detected_students
