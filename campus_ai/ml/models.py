from django.db import models
from accounts.models import User

class FaceEmbedding(models.Model):
    student = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'}
    )
    face_image = models.ImageField(upload_to='faces/')
    embedding_path = models.CharField(max_length=255)

    def __str__(self):
        return self.student.user_id
