from django import forms
# from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
)
from django.contrib.auth import get_user_model
# from .models import CustomUser
from .models import UserInfo, Report, CustomUser

User = get_user_model()


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input'
            field.widget.attrs['placeholder'] = field.label

    class Meta:
        model = CustomUser
        fields = ('email', 'password')


class UserCreateForm(UserCreationForm):
    """ユーザー登録用フォーム"""

    class Meta:
        model = User
        fields = ('email', 'username')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email


class MyPasswordChangeForm(forms.ModelForm):
    """パスワード変更フォーム"""

    class Meta:
        model = User
        fields = ('password',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'signup_input_newform'


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
            field.widget.attrs['class'] = 'signup_input_newform'

    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email


class UserInfoUpdateForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = ('nationality', 'age', 'gender', 'gender_of_love',
                  'introduction', 'profile_image')
        widgets = {
            'gender': forms.NumberInput(attrs={'type': 'range', 'min': -1, 'max': 1, }),
            'gender_of_love': forms.NumberInput(attrs={'type': 'range', 'min': -1, 'max': 1, })
            # 'class': 'custom-range'
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('reason', 'content')


class UserReregistrationForm(forms.Form):
    """ユーザー再開用フォーム"""
    email = forms.EmailField(label='email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
