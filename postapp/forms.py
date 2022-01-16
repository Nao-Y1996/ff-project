from django.contrib.auth.forms import (
    AuthenticationForm
)
from django import forms
from .models import Message


class NewTalkForm(forms.ModelForm): #新規トーク作成

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'talk_create_position_form'

    class Meta:
        model = Message
        fields = ("id","sending_user","content")

class MessageForm(forms.ModelForm): #既存トーク

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'text1_detail'

    class Meta:
        model = Message
        fields = ("id","sending_user","content","talk")
