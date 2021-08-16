from django.shortcuts import render,redirect
from django.conf import settings
from django.contrib.auth.models import User


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView, LogoutView
)
from django.views import generic
from .forms import MessageForm,NewTalkForm
from .models import Favorites,Message,Talks

from django.core import serializers
from django.http.response import JsonResponse

import uuid
import datetime

from django.db.models import Q

def mypage(request):
    return render(request,"postapp/mypage.html")

def talk_all(request):
    data = datetime.datetime.now()
    # 自分の関わっているトークを全て取得
    my_talks = Talks.objects.filter((Q(sending_user=request.user) | Q(receiving_user=request.user)))#.order_by('created_at').first()
    print(my_talks)
    params = {"data":data, "my_talks":my_talks}
    return render(request,"postapp/talk_all.html",params)



def talk_create(request): #新規トークフォーム
    if request.method == 'POST':
        form = NewTalkForm(request.POST)

        if form.is_valid():
            new_talk = Talks(sending_user=request.user, receiving_user_id=2) #to_user_id_idにどのようなidを入れるかで送り先が変わる
            new_talk.save()

            post = form.save(commit=False)

            post.talk = new_talk
            post.save()
            return redirect('postapp:talk_all')
        else:
            return render(request, 'postapp/talk_create.html', {'form': form})
    else:
        initial_dict = dict(sending_user_id=request.user.id,)
        form = NewTalkForm(initial=initial_dict)
        return render(request, 'postapp/talk_create.html', {'form': form})


def favorite_check(request,talk_id):
    talk = Talks.objects.get(id=talk_id)
    try:
        Exist_favorites = talk.favorites_set.all().filter(user_id=request.user)[0] in request.user.favorites_set.all()
    except:
        Exist_favorites =  False

    return Exist_favorites



def talk_detail(request,talk_id): #既存トークフォーム
    if request.method == 'POST':
        Exist_favorites = favorite_check(request,talk_id)
        form = MessageForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()

            initial_dict = {"sending_user_id":request.user.id, "talk":talk_id,}
            form = MessageForm(initial=initial_dict)
            messages = Message.objects.filter(talk_id=talk_id).all
            return redirect(request.META['HTTP_REFERER'])
            # return render(request, 'postapp/talk_detail.html', {'messages':messages, 'form': form ,'talk_id':talk_id , 'Exist_favorites':Exist_favorites})

        else:
            messages = Message.objects.filter(talk_id=talk_id).all
            return render(request, 'postapp/talk_detail.html', {'messages':messages, 'form': form ,'talk_id':talk_id , 'Exist_favorites':Exist_favorites})
    else:
        initial_dict = {"sending_user_id":request.user.id, "talk":talk_id,}
        form = MessageForm(initial=initial_dict)
        messages = Message.objects.filter(talk_id=talk_id).all
        Exist_favorites = favorite_check(request,talk_id)
        return render(request, 'postapp/talk_detail.html', {'messages':messages, 'form': form ,'talk_id':talk_id , 'Exist_favorites':Exist_favorites})


def talk_favorite_add(request,talk_id): #お気に入り追加

    talk = Talks.objects.get(id=talk_id)
    favorites = Favorites(talk=talk, user=request.user)
    favorites.save()

    return redirect(request.META['HTTP_REFERER'])


def talk_favorite_delete(request,talk_id): #お気に入り削除

    # print(Favorites.objects.filter(talk__id=talk_id))#, user_id=request.user))
    Favorites.objects.filter(Q(talk__id=talk_id) & Q(user=request.user)).delete()

    return redirect(request.META['HTTP_REFERER'])


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