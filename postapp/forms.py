from django.contrib.auth.forms import (
    AuthenticationForm
)
from django import forms
from .models import Message


class NewTalkForm(forms.ModelForm): #新規トーク作成
    class Meta:
        model = Message
        fields = ("id","sending_user","content")


class MessageForm(forms.ModelForm): #既存トーク
    class Meta:
        model = Message
        fields = ("id","sending_user","content","talk")
