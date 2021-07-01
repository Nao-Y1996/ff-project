from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from django.core.mail import send_mail

from phonenumber_field.modelfields import PhoneNumberField

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


# class UserInfo(models.Model):
#     user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
#     country = models.CharField(max_length=20)
#     age = models.IntegerField
#     sex = 
