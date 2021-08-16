from django.shortcuts import render,redirect
from django.conf import settings
from django.contrib.auth.models import User


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView, LogoutView
)
from django.views import generic
from .forms import LoginForm,MessageForm,NewTalkForm
from .models import Favorites,Message,Talks

from django.core import serializers
from django.http.response import JsonResponse

import uuid
import datetime

# Create your views here.


# class Top(generic.TemplateView):
#     template_name = 'top.html'


# class Login(LoginView):
#     """ログインページ"""
#     form_class = LoginForm
#     template_name = 'login.html'


# class Logout(LogoutView):
#     """ログアウトページ"""
#     template_name = 'top.html'

def mypage(request):
    return render(request,"mypage.html")

def talk_all(request):
    data = datetime.datetime.now()
    params = {"data":data}
    return render(request,"talk_all.html",params)

    #talk_list = serializers.serialize("json", Talks.objects.filter(to_user_id_id=request.user))
    #ret = { "talk_list": talk_list }
    #return JsonResponse(ret)


def talk_create(request): #新規トークフォーム
    if request.method == 'POST':
        form = NewTalkForm(request.POST)

        if form.is_valid():
            new_talks = Talks(from_user_id_id=request.user.id,to_user_id_id=3) #to_user_id_idにどのようなidを入れるかで送り先が変わる
            new_talks.save()

            post = form.save(commit=False)

            post.talk_id_id = new_talks.talk_id
            post.save()
            return render(request,'talk_all.html')
    else:
        initial_dict = {"from_user_id":request.user.id,
                        }
        form = NewTalkForm(initial=initial_dict)
        return render(request, 'talk_create.html', {'form': form})


def talk_detail(request,talk_id): #既存トークフォーム
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            message = Message.objects.filter(talk_id_id=talk_id)
            
            initial_dict = {"from_user_id":request.user.id, 
                            "talk_id":talk_id,
                            }
            form = MessageForm(initial=initial_dict)
            message = Message.objects.filter(talk_id_id=talk_id)
            return render(request, 'talk_detail.html', {'message':message, 'form': form})

        else:
            message = Message.objects.filter(talk_id_id=talk_id)
            return render(request, 'talk_detail.html', {'message':message, 'form': form})
    else:
        initial_dict = {"from_user_id":request.user.id, 
                        "talk_id":talk_id,
                        }
        form = MessageForm(initial=initial_dict)
        message = Message.objects.filter(talk_id_id=talk_id)
        return render(request, 'talk_detail.html', {'message':message, 'form': form})


    

"""
def formfunc(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('talk_detail')
    else:
        form = PostForm()
    return render(request, 'talk_detail.html', {'form': form})


def create_view(request):
    form = MessageForm(request.POST)
    if not form.is_valid():
        return HttpResponse('invalid', status=500)

    post = form.save()

    return HttpResponse(f'{post.id}', status=200)
"""