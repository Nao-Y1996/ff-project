from django.contrib.auth.forms import (
    AuthenticationForm
)
from django import forms
from .models import Message


class NewTalkForm(forms.ModelForm): #新規トーク作成

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control-text'
            field.widget.attrs['onkeyup'] = "ShowLength(value);"

    content = forms.CharField( required=True,widget=forms.Textarea,
                               min_length=1, max_length=500,
                               error_messages={'required': 'Required',"max_length":"ddd"
                                               })

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
