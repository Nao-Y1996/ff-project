from django import forms
# from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
)
from django.contrib.auth import get_user_model
# from .models import CustomUser
from .models import UserInfo, Report

User = get_user_model()


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class UserCreateForm(UserCreationForm):
    """ユーザー登録用フォーム"""

    class Meta:
        model = User
        fields = ('email','username')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email


class MyPasswordChangeForm(PasswordChangeForm):
    """パスワード変更フォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MyPasswordResetForm(PasswordResetForm):
    """パスワード忘れたときのフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MySetPasswordForm(SetPasswordForm):
    """パスワード再設定用フォーム(パスワード忘れて再設定)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class EmailChangeForm(forms.ModelForm):
    """メールアドレス変更フォーム"""

    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email


# class CustomUserUpdateForm(forms.ModelForm):
#     model = CustomUser()
#     fields = ('username', )


class UserInfoUpdateForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = ('country', 'age', 'gender', 'gender_of_love', 'introduction', 'profile_image')
        widgets = {
         'gender': forms.NumberInput(attrs={'type': 'range', 'min':-1, 'max':1, 'class':'custom-range'}),
         'gender_of_love': forms.NumberInput(attrs={'type': 'range', 'min':-1, 'max':1, 'class':'custom-range'})
         }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('reason', 'user_reported', 'content')