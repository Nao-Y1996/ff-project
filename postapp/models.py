from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
from users.models import CustomUser

# Create your models here.

class Talks(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    # to_user_id = models.ForeignKey(CustomUser, related_name="tid" ,on_delete=models.CASCADE)
    receiving_user = models.ForeignKey(CustomUser, related_name="tid" ,on_delete=models.CASCADE)
    # from_user_id = models.ForeignKey(CustomUser, related_name="fid" ,on_delete=models.CASCADE)
    sending_user = models.ForeignKey(CustomUser, related_name="fid" ,on_delete=models.CASCADE)
    confirmed_by_to = models.BooleanField(default=False)
    confirmed_by_from = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    exist_reply = models.BooleanField(default=False)
    latest_message_time = models.DateTimeField(default=timezone.now)
    detail_opened = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.sending_user) + '-' + str(self.receiving_user)



class Favorites(models.Model):
    favorite_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    talk = models.ForeignKey(Talks,on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_id","talk_id"],
                name="favorite_unique"
            ),
        ]

    # def __str__(self):
    #     return self.talk_id


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    talk = models.ForeignKey(Talks, on_delete=models.CASCADE)
    sending_user = models.ForeignKey(CustomUser, related_name="sending_user" ,on_delete=models.CASCADE)
    content = models.CharField(max_length=500)


# admin ユーザー名:superuser , パスワード:sora0214
