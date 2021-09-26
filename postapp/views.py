from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.models import User


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView, LogoutView
)
from django.views import generic
from .forms import MessageForm, NewTalkForm
from .models import Favorites, Message, Talks
from users.models import CustomUser, UserInfo

from django.core import serializers
from django.http.response import JsonResponse

import uuid
import datetime

from django.db.models import Q

import json
from django.http.response import JsonResponse
from datetime import date


def mypage(request):
    return render(request, "postapp/mypage.html")


def favorite_check(request, talk_id):
    talk = Talks.objects.get(id=talk_id)
    try:
        Exist_favorites = talk.favorites_set.all().filter(user_id=request.user)[
            0] in request.user.favorites_set.all()
    except:
        Exist_favorites = False

    return Exist_favorites


def talk_all(request):
    def was_read(talk):
        newest_message = Message.objects.filter(talk_id=talk.id).first()
        print(newest_message.sending_user)
        if (talk.detail_opened is False) and (newest_message.sending_user != request.user):
            return False
        else:
            return True
    data = datetime.datetime.now()
    my_talks = Talks.objects.filter((Q(sending_user=request.user) | Q(
        receiving_user=request.user)))  # .order_by('-created_at')  # 自分の関わっているトークを全て取得

    unchecked_dead_talks = []
    unread_talks = []
    read_talks = []
    for talk in my_talks:
        if not is_active(talk):
            if talk.sending_user == request.user and talk.confirmed_by_to == False:
                checked_userinfo = True
            elif talk.receiving_user == request.user and talk.confirmed_by_from == False:
                checked_userinfo = True
            else:
                checked_userinfo = False
            if checked_userinfo:
                unchecked_dead_talks.append(talk)
        else:  # is_active(talk):
            if was_read(talk):
                read_talks.append(talk)
            else:
                unread_talks.append(talk)

    create_data = {}
    for i, talk in enumerate(my_talks):
        create_data[i] = str(talk.created_at).replace(' ', 'T')
    params = {"data": data, "my_talks": my_talks,
              'data_json': json.dumps(create_data),
              'unchecked_dead_talks': unchecked_dead_talks,
              'unread_talks':unread_talks,
              'read_talks':read_talks
              }
    return render(request, "postapp/talk_all.html", params)


def talk_create(request):  # 新規トークフォーム
    if request.method == 'POST':
        form = NewTalkForm(request.POST)

        if form.is_valid():
            new_talk = Talks(sending_user=request.user, receiving_user=CustomUser.objects.get(
                id=3))  # idにどのようなidを入れるかで送り先が変わる
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


def is_active(talk):
    now = datetime.datetime.now()
    deadline = talk.created_at.replace(
        tzinfo=None) + datetime.timedelta(days=14) + datetime.timedelta(hours=9) + datetime.timedelta(minutes=0)
    if deadline < now:
        is_talk_active = True
    else:
        is_talk_active = False
    return is_talk_active


def favorite_check(request, talk_id):
    talk = Talks.objects.get(id=talk_id)
    try:
        Exist_favorites = talk.favorites_set.all().filter(user_id=request.user)[
            0] in request.user.favorites_set.all()
    except:
        Exist_favorites = False

    return Exist_favorites


def talk_detail(request, talk_id):  # 既存トークフォーム
    if request.method == 'POST':
        Exist_favorites = favorite_check(request, talk_id)
        form = MessageForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()

            talk = Talks.objects.get(id=talk_id)
            talk.detail_opened = False
            talk.save()

            initial_dict = {"sending_user": request.user, "talk": talk_id, }
            form = MessageForm(initial=initial_dict)
            messages = Message.objects.filter(talk_id=talk_id).all
            return redirect(request.META['HTTP_REFERER'])
            # return render(request, 'postapp/talk_detail.html', {'messages':messages, 'form': form ,'talk_id':talk_id , 'Exist_favorites':Exist_favorites})

        else:
            messages = Message.objects.filter(talk_id=talk_id).all
            return render(request, 'postapp/talk_detail.html', {'messages': messages, 'form': form, 'talk_id': talk_id, 'Exist_favorites': Exist_favorites})
    else:
        talk = Talks.objects.get(id=talk_id)
        # 返信がない かつ 自分がトークの開始者である 時はトーク詳細に入れない(トーク一覧に戻される)
        if (not talk.exist_reply) & (talk.sending_user == request.user):
            return redirect("postapp:talk_all")
        else:
            print("*"*40)
            newest_message = Message.objects.filter(talk_id=talk_id).first()
            print(newest_message.sending_user)
            if newest_message.sending_user != request.user:
                talk.detail_opened = True
                talk.save()

            now = datetime.datetime.now()
            talk = Talks.objects.get(id=talk_id)
            created_at = talk.created_at.replace(
                tzinfo=None) + datetime.timedelta(days=0) + datetime.timedelta(hours=9) + datetime.timedelta(minutes=2)
            #left_time = created_at - data
            # print(left_time)

            # トーク可能時間内かどうか判定し時間外なら事後公開情報画面へ推移
            if created_at < now:
                Exist_favorites = favorite_check(request, talk_id)
                sending_user = talk.sending_user
                user_info = UserInfo.objects.get(user_id=sending_user)

                return render(request, 'postapp/post_release.html', {'user_info': user_info, 'sending_user': sending_user, 'Exist_favorites': Exist_favorites, 'talk_id': talk_id})

            else:
                initial_dict = {
                    "sending_user": request.user, "talk": talk_id, }
                form = MessageForm(initial=initial_dict)
                messages = Message.objects.filter(talk_id=talk_id).all
                Exist_favorites = favorite_check(request, talk_id)

                if not talk.exist_reply:
                    receiving_user = talk.receiving_user
                    # このトークにおける受信者が、送信者となっているメッセージ(すなわち返信)の数
                    reply_count = Message.objects.filter(
                        Q(talk_id=talk_id) & Q(sending_user=receiving_user)).count()
                    # print(reply)
                    if reply_count != 0:
                        talk.exist_reply = True
                        talk.save()

        return render(request, 'postapp/talk_detail.html', {'messages': messages, 'form': form, 'talk_id': talk_id, 'Exist_favorites': Exist_favorites})


def talk_favorite_add(request, talk_id):  # お気に入り追加

    talk = Talks.objects.get(id=talk_id)
    favorites = Favorites(talk=talk, user=request.user)
    favorites.save()

    return redirect(request.META['HTTP_REFERER'])


def talk_favorite_delete(request, talk_id):  # お気に入り削除

    # print(Favorites.objects.filter(talk__id=talk_id))#, user_id=request.user))
    Favorites.objects.filter(Q(talk__id=talk_id) &
                             Q(user=request.user)).delete()

    talk = Talks.objects.get(id=talk_id)
    CheckExist = not(Favorites.objects.filter(talk__id=talk_id).exists())

    if talk.confirmed_by_from == 1 & talk.confirmed_by_to == 1 & CheckExist:  # トークを削除するかの判定
        talk.delete()

    return redirect(request.META['HTTP_REFERER'])


def final_favorite_add(request, talk_id):  # お気に入り追加_最終チェック

    talk = Talks.objects.get(id=talk_id)
    favorites = Favorites(talk=talk, user=request.user)
    favorites.save()

    if talk.sending_user == request.user:
        talk.confirmed_by_to = 1
    else:
        talk.confirmed_by_from = 1

    talk.save()

    return redirect("postapp:talk_all")


def final_favorite_delete(request, talk_id):  # 状況に応じてトークの削除

    # print(Favorites.objects.filter(talk__id=talk_id))#, user_id=request.user))
    talk = Talks.objects.get(id=talk_id)

    if talk.sending_user == request.user:
        talk.confirmed_by_to = 1
    else:
        talk.confirmed_by_from = 1

    talk.save()

    CheckExist = not(Favorites.objects.filter(talk__id=talk_id).exists())

    if talk.confirmed_by_from == 1 & talk.confirmed_by_to == 1 & CheckExist:  # トークを削除するかの判定
        talk.delete()

    return redirect("postapp:talk_all")


def confirmed_add(request, talk_id):  # すでにお気に入りしているため、confirmed_byを1へ

    talk = Talks.objects.get(id=talk_id)

    if talk.sending_user == request.user:
        talk.confirmed_by_to = 1
    else:
        talk.confirmed_by_from = 1

    talk.save()

    return redirect("postapp:talk_all")
