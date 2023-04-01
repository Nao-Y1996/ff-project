import uuid

from django.db import models
from django.utils import timezone

from users.models import CustomUser


class Talks(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    receiving_user = models.ForeignKey(CustomUser, related_name="tid", on_delete=models.CASCADE)
    sending_user = models.ForeignKey(CustomUser, related_name="fid", on_delete=models.CASCADE)
    confirmed_by_sending_user = models.BooleanField(default=False)
    confirmed_by_receiving_user = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    exist_reply = models.BooleanField(default=False)
    latest_message_time = models.DateTimeField(default=timezone.now)
    detail_opened = models.BooleanField(default=False)
    invalid = models.BooleanField(default=False)

    def __str__(self):
        return str(self.sending_user) + '-' + str(self.receiving_user)

    def invalidate(self):
        self.invalid = True
        self.save()


class Favorites(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    talk = models.ForeignKey(Talks, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "talk_id"],
                name="favorite_unique"
            ),
        ]


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    talk = models.ForeignKey(Talks, on_delete=models.CASCADE)
    sending_user = models.ForeignKey(CustomUser, related_name="sending_user", on_delete=models.CASCADE)
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)
    is_date = models.BooleanField(default=False, null=False, blank=True)


class Executedfunction(models.Model):
    name = models.TextField(primary_key=True, max_length=200)
    executed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.name)
