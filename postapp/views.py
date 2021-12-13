from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.models import User


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView, LogoutView
)
from django.views import generic
from .forms import MessageForm, NewTalkForm
from .models import Favorites, Message, Talks, Executedfunction
from users.models import CustomUser, UserInfo
from django.contrib import messages
from django.core import serializers
from django.http.response import JsonResponse

import uuid

from django.db.models import Q

import json
from django.http.response import JsonResponse
from datetime import date, datetime, timezone, timedelta
import random
import numpy as np
import sys
from django_pandas.io import read_frame
DAYS = 0
HOURS = 0
MINUTES = 0
SEND_NUM_LIMIT = 5

 # -----------------------（アルゴリズム検証）---------------------------
from algorithm_check import algorithm_checker_utils
timing_delete_talk = algorithm_checker_utils.TIMING_DELETE_TALK
import time
csv_controller2 = algorithm_checker_utils.csv_controller4user()
DAYS = algorithm_checker_utils.TALK_LIMIT_DAYS
 # -----------------------（アルゴリズム検証）---------------------------

def mypage(request):
    return render(request, "postapp/mypage.html")


def favorite_check(request, talk):
    try:
        Exist_favorites = talk.favorites_set.all().filter(user_id=request.user)[
            0] in request.user.favorites_set.all()
    except:
        Exist_favorites = False

    return Exist_favorites


def is_talk_active(talk):
    now = datetime.now(timezone.utc)
    deadline = talk.created_at.replace(
        tzinfo=timezone.utc) + timedelta(days=DAYS) + timedelta(hours=HOURS) + timedelta(minutes=MINUTES)
    if deadline < now:
        is_talk_active = False
    else:
        is_talk_active = True
    return is_talk_active


def talk_all(request):
    def was_read(talk):
        newest_message = Message.objects.filter(
            talk_id=talk.id).latest("created_at")
        if (talk.detail_opened is False) and (newest_message.sending_user != request.user):
            return False
        else:
            return True

    data = datetime.now()
    my_talks = Talks.objects.filter((Q(sending_user=request.user) | Q(
        receiving_user=request.user)))  # .order_by('-created_at')  # 自分の関わっているトークを全て取得

    unchecked_dead_talks = []
    unread_talks = []
    read_talks = []
    favorite_dead_talks = []
    for talk in my_talks:
        if not is_talk_active(talk):  # 期限終了の時
            messages = Message.objects.filter(talk_id=talk.id).all()
            # if not talk.exist_reply:# 返信がない時
            if messages.count() == 1:
                talk.delete()
                continue
            if talk.sending_user == request.user and talk.confirmed_by_sending_user == False:
                checked_userinfo = True
            elif talk.receiving_user == request.user and talk.confirmed_by_receiving_user == False:
                checked_userinfo = True
            else:
                checked_userinfo = False
            if checked_userinfo:
                unchecked_dead_talks.append(talk)
            else:
                # お気に入りの有無でtalkを分類
                if favorite_check(request, talk):
                    favorite_dead_talks.append(talk)
        else:
            if was_read(talk):
                read_talks.append(talk)
            else:
                unread_talks.append(talk)
    # print('='*20)
    # print(len(my_talks), len(unchecked_dead_talks) +
    #       len(unread_talks)+len(read_talks)+len(favorite_dead_talks))

    create_data = {}
    for i, talk in enumerate(my_talks):
        create_data[i] = str(talk.created_at).replace(' ', 'T')
    params = {"data": data, "my_talks": my_talks,
              'data_json': json.dumps(create_data),
              'unchecked_dead_talks': unchecked_dead_talks,
              'unread_talks': unread_talks,
              'read_talks': read_talks,
              'favorite_dead_talks': favorite_dead_talks,
              }
    return render(request, "postapp/talk_all.html", params)


def decide_reciever(request):  # 送り先を決定するアルゴリズム
    found_reciever = False
    send_id = None
    all_user_info = UserInfo.objects.all()
    df = read_frame(all_user_info, fieldnames=['user',
                                            'priority_rank',
                                            'capacity_new_msg'])
    # print('-----------  df  -----------')
    # print(df)
    # print('----------------------------')
    cap = df['capacity_new_msg'].max() + 1
    # cap_min = df['capacity_new_msg'].min()
    exist_talk_count = 0
    while True:
        cap -= 1
        # print(f'capacity={cap}')
        for rank in range(1,16+1):
            # print(f'rank={rank}')
            df_candidates = df[(df['capacity_new_msg'] == cap) &
                            (df['priority_rank'] == rank)] # 今日の新規メッセージ受け取り残数がcap, 優先度ランクがrankのユーザーに絞る
            # print('----------  df_candidates  ------------')
            # print(df_candidates)
            # print('---------------------------------------')
            if len(df_candidates) == 0:
                continue # 調べているrankのユーザーがいない時は次のrankを調べる
            candidates_choice_list = list(range(len(df_candidates)))
            # 候補者からランダムに選択してチェック
            while True:
                # print(f'選択肢 --> {candidates_choice_list}')
                if len(candidates_choice_list) == 0:
                    break # 候補者を調べ切った時は次のrankを調べる
                # 絞ったユーザーの中からランダムに一人選択する
                rand_num = random.randint(0, len(candidates_choice_list)-1)
                candidate_choice = candidates_choice_list[rand_num]
                # print(f'選択 --> {candidate_choice} ')
                candidate_user_id = df_candidates.iloc[candidate_choice, 0] # candidate_choice行目 0列目のデータを取得(0列目はuserID)
                # print(f'ユーザーID {candidate_user_id}')
                candidate = CustomUser.objects.get(id=candidate_user_id)
                # print('候補者-->',candidate.username)
                # 候補者がadminならスキップする
                if candidate.username == 'admin':
                    # print('候補者がadminでした')
                    candidates_choice_list.pop(candidates_choice_list.index(candidate_choice)) # 候補者の選択肢からから現在選択されているユーザーを削除
                    # print(f'候補{candidate_choice}を削除')
                    continue
                talk = Talks.objects.filter( (Q(sending_user=request.user) & Q(receiving_user=candidate)) | (Q(sending_user=candidate) & Q(receiving_user=request.user)) )
                if len(talk) != 0: # 候補者とのトークがある時はスキップ
                    # print('すでに送信先の候補者とのトークが存在しています')
                    candidates_choice_list.pop(candidates_choice_list.index(candidate_choice)) # 候補者の選択肢からから現在選択されているユーザーを削除
                    # print(f'候補{candidate_choice}を削除')
                    exist_talk_count += 1
                    # print(f'exist_talk_count = {exist_talk_count}')
                    continue
                else:
                    if candidate == request.user: # 候補者が自分の時はスキップ
                        candidates_choice_list.pop(candidates_choice_list.index(candidate_choice)) # 候補者の選択肢からから現在選択されているユーザーを削除
                        # print('候補者が自分でした')
                        # print(f'候補{candidate_choice}を削除')
                        continue
                    else: # 候補者が自分でなければ送信先に決定
                        send_id = candidate.id
                        found_reciever = True
                if found_reciever:
                    break
            if found_reciever:
                break
        if found_reciever:
            break
        if exist_talk_count == len(df)-2: # -2はadminと自分を除くという意味
            print('送信先が見つかりません(すべてのユーザーとトーク中です)')
            # my_talk = Talks.objects.filter( (Q(sending_user=request.user) | Q(receiving_user=request.user)) )
            # print(f'現在のトーク数 = {len(my_talk)}')
            # time.sleep(3)
            break
    print(f'送信先 --> user_id={send_id} ')
    return send_id
        
def update_sending_priority_rank():
    all_users_info = UserInfo.objects.all()
    # メッセージ送信の優先度の判定基準となる各カウント数をDataFrameに格納
    df = read_frame(all_users_info, fieldnames=['count_receive_new_messages',  # 平均値より、少ない方が優先
                                            'count_first_reply',  # 平均値より、多い方が優先
                                            'count_send_new_messages',  # 平均値より、多い方が優先
                                            'count_login'])  # 平均値より、少ない方が優先
    # カウント数が平均値より少ないかを真偽値で表現
    binary_matrix = np.array(df) < np.mean(np.array(df), axis=0)
    # count_first_reply, count_send_new_messagesを「多い」に合わせるために真偽反転
    binary_matrix[:, 1] = np.logical_not(binary_matrix[:, 1])
    binary_matrix[:, 2] = np.logical_not(binary_matrix[:, 2])
    # ここまでの処理で、全ての項目で「優先」であるなら　True, True, True, True　となる
    # これを10進数に変換すると 15 になり、16から引くことで、優先ランキングが1となる
    upd_user_infos = []
    for i, user_info in enumerate(all_users_info):
        binarys = binary_matrix[i]
        binary = '0b'+str(int(binarys[0]))+str(int(binarys[1])) + \
            str(int(binarys[2]))+str(int(binarys[3])) # 10進数に変換
        priority_rank = 16 - int(binary, 2) # 優先ランキング
        user_info.priority_rank = priority_rank
        # 優先ランキングに基づくその日の新規メッセージの受け取り可能数を設定
        if priority_rank <= 5:
            capacity_new_msg = 3
        elif priority_rank <= 10:
            capacity_new_msg = 2
        else:
            capacity_new_msg = 1
        user_info.capacity_new_msg = capacity_new_msg
        upd_user_infos.append(user_info)
        # print('-------------')
        # print(df.iloc[i])
        # print(binarys)
        # print(priority_rank)
    update_columns = ['priority_rank', 'capacity_new_msg']
    UserInfo.objects.bulk_update(upd_user_infos, fields=update_columns)
    # 実行時刻を保存
    self_func_name = sys._getframe().f_code.co_name
    func = Executedfunction.objects.get(name=self_func_name)
    func.executed_at = datetime.now(timezone.utc)
    func.save()
    print(f'関数を実行しました：{self_func_name}, time --> {func.executed_at}')


def reset_count_for_priority_rank():
    all_user_info = UserInfo.objects.all()
    upd_user_infos = []
    for user_info in all_user_info:
        user_info.count_receive_new_messages = 0
        user_info.count_first_reply = 0
        user_info.count_send_new_messages = 0
        user_info.count_login = 0
        upd_user_infos.append(user_info)
    update_columns = ['count_receive_new_messages', 'count_first_reply', 'count_send_new_messages','count_login']
    UserInfo.objects.bulk_update(upd_user_infos, fields=update_columns)
    # 実行時刻を保存
    self_func_name = sys._getframe().f_code.co_name
    func = Executedfunction.objects.get(name=self_func_name)
    func.executed_at = datetime.now(timezone.utc)
    func.save()
    print(f'関数を実行しました：{self_func_name}, time --> {func.executed_at}')


def talk_create(request):  # 新規トークフォーム
    if request.method == 'POST':
        form = NewTalkForm(request.POST)

        if form.is_valid():

            send_id = decide_reciever(request)  # 送信先決定
            if send_id is None:
                messages.warning(
                request, f'すみません、送信相手が見つかりませんでした。時間を置いてから投稿してください')
                print('送信相手が見つかりません。予期せぬエラーが発生しました')
                return redirect("users:profile")
            else:
                # 新規投稿した人にカウント
                sending_user_info = UserInfo.objects.get(user_id=request.user)
                sending_user_info.count_send_new_messages += 1
                sending_user_info.count_send_new_messages_in_a_day += 1
                sending_user_info.save()

                # 新規投稿が送られた人にカウント
                recieving_user_info = UserInfo.objects.get(user_id=send_id)
                recieving_user_info.count_receive_new_messages += 1
                recieving_user_info.capacity_new_msg -= 1
                recieving_user_info.save()

                new_talk = Talks(sending_user=request.user, receiving_user=CustomUser.objects.get(
                    id=send_id))  # idにどのようなidを入れるかで送り先が変わる
                new_talk.save()

                post = form.save(commit=False)

                post.talk = new_talk
                post.save()
                # -----------------------（アルゴリズム検証）---------------------------
                # メッセージの受信回数をインクリメント
                recieving_user = CustomUser.objects.get(id=send_id)
                day_num = csv_controller2.get_day()
                csv_controller2.incriment_receive_num(file_name=recieving_user.username, idx_name='day'+day_num)
                # -----------------------（アルゴリズム検証）---------------------------
                return redirect('postapp:talk_all')
        else:
            return render(request, 'postapp/talk_create.html', {'form': form})
    else:
        user_info = UserInfo.objects.get(user_id=request.user)
        if user_info.count_send_new_messages_in_a_day >= SEND_NUM_LIMIT:
            messages.warning(
                request, f'本日の投稿可能上限に達しました。')
            return redirect("users:profile")
        initial_dict = dict(sending_user=request.user,)
        form = NewTalkForm(initial=initial_dict)
        return render(request, 'postapp/talk_create.html', {'form': form})


def talk_detail(request, talk_id):  # 既存トークフォーム
    talk = Talks.objects.get(id=talk_id)
    if request.method == 'POST':
        if not is_talk_active(talk):  # 終了トークなのに誤って送信が行われた場合
            return redirect(request.META['HTTP_REFERER'])
        else:
            Exist_favorites = favorite_check(request, talk)
            form = MessageForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.save()

                # talk = Talks.objects.get(id=talk_id)
                talk.detail_opened = False
                talk.save()


                initial_dict = {
                    "sending_user": request.user, "talk": talk_id, }
                form = MessageForm(initial=initial_dict)
                messages = Message.objects.filter(talk_id=talk_id).all
                return redirect(request.META['HTTP_REFERER'])
                # return render(request, 'postapp/talk_detail.html', {'messages':messages, 'form': form ,'talk_id':talk_id , 'Exist_favorites':Exist_favorites})

            else:
                messages = Message.objects.filter(talk_id=talk_id).all
                return render(request, 'postapp/talk_detail.html', {'messages': messages, 'form': form, 'talk_id': talk_id, 'Exist_favorites': Exist_favorites})
    else:
        # 返信がない かつ 自分がトークの開始者である 時はトーク詳細に入れない(トーク一覧に戻される)
        if (not talk.exist_reply) & (talk.sending_user == request.user):
            return redirect("postapp:talk_all")
        else:
            flag = False
            newest_message = Message.objects.filter(talk_id=talk_id).latest(
                "created_at")  # .order_by('-created_at')[0]
            if newest_message.sending_user != request.user:
                talk.detail_opened = True
                talk.save()
            # トーク可能時間内かどうか判定し時間外なら事後公開情報画面へ推移
            if not is_talk_active(talk):
                Exist_favorites = favorite_check(request, talk)
                sending_user = talk.sending_user
                user_info = UserInfo.objects.get(user_id=sending_user)
                messages = Message.objects.filter(talk_id=talk_id).all
                flag = True
                return render(request, 'postapp/talk_detail.html', {'flag': flag, 'messages': messages, 'user_info': user_info, 'sending_user': sending_user, 'Exist_favorites': Exist_favorites, 'talk_id': talk_id})
            else:
                initial_dict = {
                    "sending_user": request.user, "talk": talk_id, }
                form = MessageForm(initial=initial_dict)
                messages = Message.objects.filter(talk_id=talk_id).all
                Exist_favorites = favorite_check(request, talk)

                if not talk.exist_reply:
                    receiving_user = talk.receiving_user
                    # このトークにおける受信者が、送信者となっているメッセージ(すなわち返信)の数
                    reply_count = Message.objects.filter(
                        Q(talk_id=talk_id) & Q(sending_user=receiving_user)).count()
                    # print(reply)
                    if reply_count != 0:
                        talk.exist_reply = True
                        talk.save()

                        user_info = UserInfo.objects.get(
                            user_id=receiving_user)
                        user_info.count_first_reply += 1
                        user_info.save()

        return render(request, 'postapp/talk_detail.html', {'flag': flag, 'messages': messages, 'form': form, 'talk_id': talk_id, 'Exist_favorites': Exist_favorites})


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

    if talk.confirmed_by_receiving_user == 1 & talk.confirmed_by_sending_user == 1 & CheckExist:  # トークを削除するかの判定
        talk.delete()

    return redirect(request.META['HTTP_REFERER'])


def final_favorite_add(request, talk_id):  # お気に入り追加_最終チェック

    talk = Talks.objects.get(id=talk_id)
    favorites = Favorites(talk=talk, user=request.user)
    favorites.save()

    if talk.sending_user == request.user:
        talk.confirmed_by_sending_user = 1
    else:
        talk.confirmed_by_receiving_user = 1

    talk.save()

    return redirect("postapp:talk_all")


def final_favorite_delete(request, talk_id):  # 状況に応じてトークの削除

    # print(Favorites.objects.filter(talk__id=talk_id))#, user_id=request.user))
    talk = Talks.objects.get(id=talk_id)

    if talk.sending_user == request.user:
        talk.confirmed_by_sending_user = 1
    else:
        talk.confirmed_by_receiving_user = 1

    talk.save()

    CheckExist = not(Favorites.objects.filter(talk__id=talk_id).exists())

    if talk.confirmed_by_receiving_user == 1 & talk.confirmed_by_sending_user == 1 & CheckExist:  # トークを削除するかの判定
        talk.delete()

    return redirect("postapp:talk_all")


def confirmed_add(request, talk_id):  # すでにお気に入りしているため、confirmed_byを1へ

    talk = Talks.objects.get(id=talk_id)

    if talk.sending_user == request.user:
        talk.confirmed_by_sending_user = 1
    else:
        talk.confirmed_by_receiving_user = 1

    talk.save()

    return redirect("postapp:talk_all")