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
from users.models import CustomUser

from django.core import serializers
from django.http.response import JsonResponse

import uuid
import datetime

from django.db.models import Q

import json
from django.http.response import JsonResponse
from datetime import date


def mypage(request):
    return render(request,"postapp/mypage.html")

def talk_all(request):
    data = datetime.datetime.now()
    my_talks = Talks.objects.filter((Q(sending_user=request.user) | Q(receiving_user=request.user))).order_by('-created_at')# 自分の関わっているトークを全て取得
    create_data = {}
    for i, talk in enumerate(my_talks):
        create_data[i] = str(talk.created_at).replace(' ', 'T')
    params = {"data":data, "my_talks":my_talks, 'data_json':json.dumps(create_data)}
    return render(request,"postapp/talk_all.html",params)



def talk_create(request): #新規トークフォーム
    if request.method == 'POST':
        form = NewTalkForm(request.POST)

        if form.is_valid():
            new_talk = Talks(sending_user=request.user, receiving_user=CustomUser.objects.get(id=3)) #idにどのようなidを入れるかで送り先が変わる
            new_talk.save()

            post = form.save(commit=False)

            post.talk = new_talk
            post.save()
            return redirect('postapp:talk_all')
        else:
            return render(request, 'postapp/talk_create.html', {'form': form})
    else:
        initial_dict = dict(sending_user=request.user,)
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

            initial_dict = {"sending_user":request.user, "talk":talk_id,}
            form = MessageForm(initial=initial_dict)
            messages = Message.objects.filter(talk_id=talk_id).all
            return redirect(request.META['HTTP_REFERER'])
            # return render(request, 'postapp/talk_detail.html', {'messages':messages, 'form': form ,'talk_id':talk_id , 'Exist_favorites':Exist_favorites})

        else:
            messages = Message.objects.filter(talk_id=talk_id).all
            return render(request, 'postapp/talk_detail.html', {'messages':messages, 'form': form ,'talk_id':talk_id , 'Exist_favorites':Exist_favorites})
    else:
        talk = Talks.objects.get(id=talk_id)
        # 返信がない かつ 自分がトークの開始者である 時はトーク詳細に入れない(トーク一覧に戻される)
        if (not talk.exist_reply) & (talk.sending_user==request.user):
            return redirect("postapp:talk_all")
        else:
            initial_dict = {"sending_user":request.user, "talk":talk_id,}
            form = MessageForm(initial=initial_dict)
            messages = Message.objects.filter(talk_id=talk_id).all
            Exist_favorites = favorite_check(request,talk_id)

            talk = Talks.objects.get(id=talk_id)
            if not talk.exist_reply:
                receiving_user = talk.receiving_user
                # このトークにおける受信者が、送信者となっているメッセージ(すなわち返信)の数
                reply_count = Message.objects.filter(Q(talk_id=talk_id) & Q(sending_user=receiving_user)).count()
                # print(reply)
                if reply_count != 0:
                    talk.exist_reply = True
                    talk.save()

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
