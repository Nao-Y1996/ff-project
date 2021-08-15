from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
from users.models import CustomUser


# Create your models here.
class Favorites(models.Model):
    favorite_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    talk_id = models.IntegerField(null=True)
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.tali_id


class Talks(models.Model):
    talk_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    to_user_id = models.ForeignKey(CustomUser, related_name="tid" ,on_delete=models.CASCADE)
    from_user_id = models.ForeignKey(CustomUser, related_name="fid" ,on_delete=models.CASCADE)
    confirmed_by_to = models.BooleanField(default=False)
    confirmed_by_from = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)


class Message(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    talk_id = models.ForeignKey(Talks, on_delete=models.CASCADE)
    from_user_id = models.IntegerField(null=True)
    content = models.CharField(max_length=500)
    


    


# admin ユーザー名:superuser , パスワード:sora0214
