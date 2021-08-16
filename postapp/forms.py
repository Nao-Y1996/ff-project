from django.contrib.auth.forms import (
    AuthenticationForm
)
from django import forms
from .models import Message

class LoginForm(AuthenticationForm):
    """ログインフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label 


class NewTalkForm(forms.ModelForm): #新規トーク作成
    class Meta:
        model = Message
        fields = ("message_id","from_user_id","content")


class MessageForm(forms.ModelForm): #既存トーク
    class Meta:
        model = Message
        fields = ("message_id","from_user_id","content","talk_id")
