from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from django.core.mail import send_mail
from django.core import validators

from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField

import uuid

# Start mod_userModel branch

class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone_number, username, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            phone_number=phone_number,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone_number, username, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            username=username,
            phone_number=phone_number,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

# Create your models here.
class CustomUser(AbstractBaseUser):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    username = models.CharField(
        verbose_name='Uername',
        max_length=30,
        # validators=[username_validator],
        # error_messages={
        #     'unique': _("A user with that username already exists.")
    )
    phone_number = PhoneNumberField()
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = CustomUserManager()

    # パスワードと何で認証するかを決める　ここではパスワードとemail
    # AuthenticationFormでの認証は USERNAME_FIELD で指定したユーザー名フィールドを使用する。
    USERNAME_FIELD = 'email'
    # 「createsuperuser management」コマンドを使用してユーザーを作成するとき、プロンプ​​トに表示されるフィールド名のリスト。デフォルトは「REQUIRED_FIELDS = [‘username’]」です。
    REQUIRED_FIELDS = ['username', 'phone_number']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


def image_directory_path(instance, filename):
    print('{}.{}'.format(str(uuid.uuid4()), filename.split('.')[-1]))
    return '{}.{}'.format(str(uuid.uuid4()), filename.split('.')[-1])


class UserInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="user_info")
    nationality = CountryField(blank_label='(select country)',blank=False, null=True)
    age = models.IntegerField(blank=True, null=True)
    # sex_choice = ((0, 'Female'),(1, 'male'),(2, 'other'))
    gender = models.FloatField(validators=[validators.MinValueValidator(-1.0),
        validators.MaxValueValidator(1.0)], blank=True, null=True)
    gender_of_love = models.FloatField(validators=[validators.MinValueValidator(-1.0),
        validators.MaxValueValidator(1.0)], blank=True, null=True)
    introduction = models.TextField(blank=True,null=True)
    profile_image = models.ImageField(upload_to=image_directory_path, blank=True, null=True,default='media/no_image.png')
    count_send_new_messages_in_a_day = models.IntegerField(default=0)
    count_send_new_messages = models.IntegerField(blank=True,null=True,default=0)
    count_receive_new_messages = models.IntegerField(blank=True,null=True,default=0)
    count_login = models.IntegerField(blank=True,null=True,default=0)
    count_first_reply = models.IntegerField(blank=True,null=True,default=0)
    count_bad_messages = models.IntegerField(blank=True,null=True,default=0)
    priority = models.IntegerField(default=7)
    def __str__(self):
        return str(self.user)

class ReportReasons(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    choices = models.CharField(max_length=200, blank=False, null=True)
    def __str__(self):
        return self.choices

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reason = models.ForeignKey(ReportReasons, on_delete=models.CASCADE, related_name="reason")
    user_reported = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="reported")
    user_reporting = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="reporting")
    content = models.TextField(max_length=200,blank=True,null=True)
    def __str__(self):
        return 'from ' + str(self.user_reporting) + ' to ' + str(self.user_reported)

