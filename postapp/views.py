import json
import logging
import random
import sys
from datetime import datetime, timezone, timedelta

import numpy as np
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect
from django_pandas.io import read_frame

from GPT.gpt_client import GPT
from ff import settings
from users.models import CustomUser, UserInfo
from .forms import MessageForm, NewTalkForm
from .models import Favorites, Message, Talks, Executedfunction

# そのユーザーとチャットができる期間
DAYS = settings.TALK_AVAILABLE_DAYS
HOURS = settings.TALK_AVAILABLE_HOURS
MINUTES = settings.TALK_AVAILABLE_MINUTES
# 1日に送信できるメッセージの上限数
NEW_POST_LIMIT = settings.NEW_POST_LIMIT
system_setting = """
You are the system that monitors the words or sentences, and determines if it is inappropriate.
Word or sentence is written in a variety of languages.
The following is a specification of the system  for generate your response in a pseudo-programming language.

input = (word or sentences)
if (input is inappropriate): 
    return 1
if else (it is not possible to determine whether the input is appropriate or not):
    return 0 
else:
    return 0

You have to return 1 or 0 as response regardless of language.
Therefore your response must be a single "1" or "0".
    """


def mypage(request):
    return render(request, "postapp/mypage.html")


def exist_favorites(request, talk):
    try:
        return talk.favorites_set.all().filter(user_id=request.user)[
            0] in request.user.favorites_set.all()
    except IndexError:
        return False


def is_talk_available(talk):
    now = datetime.now(timezone.utc)
    deadline = talk.created_at.replace(
        tzinfo=timezone.utc) + timedelta(days=DAYS) + timedelta(hours=HOURS) + timedelta(minutes=MINUTES)
    return now < deadline


def new_post_count_in_last_24_hours(sender):
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    return Talks.objects.filter(sending_user=sender, created_at__gte=twenty_four_hours_ago).count()


# 自分のトークの分類を行う
def my_talks_classification(request):
    # 自分の関わっているトークを4つに分類する
    unchecked_dead_talks = []  # 終了したトークの中で、相手の公開情報を確認していないトーク
    unread_talks = []  # 未読メッセージのあるトーク
    read_talks = []  # すべてのメッセージが既読であるトーク
    favorite_dead_talks = []  # お気に入りした終了トーク

    def was_read(talk):
        newest_message = Message.objects.filter(talk_id=talk.id).latest("created_at")
        if (talk.detail_opened is False) and (newest_message.sending_user != request.user):
            return False
        else:
            return True

    my_talks = Talks.objects.filter(Q(invalid=False), (
                Q(sending_user=request.user) | Q(receiving_user=request.user)))  # 自分の関わっているトークを全て取得

    for talk in my_talks:
        if not is_talk_available(talk):  # 期限終了の時
            if not talk.exist_reply:  # 返信がない時
                talk.invalidate()
                continue
            checked_userinfo = False
            if talk.sending_user == request.user and (not talk.confirmed_by_sending_user):
                checked_userinfo = True
            if talk.receiving_user == request.user and (not talk.confirmed_by_receiving_user):
                checked_userinfo = True
            if checked_userinfo:
                unchecked_dead_talks.append(talk)
            else:
                # お気に入りの有無でtalkを分類
                if exist_favorites(request, talk):
                    favorite_dead_talks.append(talk)
        else:
            if was_read(talk):
                read_talks.append(talk)
            else:
                unread_talks.append(talk)

    create_data = {}
    for i, talk in enumerate(my_talks):
        create_data[i] = str(talk.created_at).replace(' ', 'T')

    talk_count = len(favorite_dead_talks)  # お気に入りした終了トークの数を取得
    progress_message_count = len(unchecked_dead_talks) + len(unread_talks) + len(read_talks)  # 進行中のメッセージ数を取得

    params = {"data": datetime.now(),
              "my_talks": my_talks,
              'data_json': json.dumps(create_data),
              'unchecked_dead_talks': unchecked_dead_talks,
              'unread_talks': unread_talks,
              'read_talks': read_talks,
              'favorite_dead_talks': favorite_dead_talks,
              'talk_count': talk_count,
              'progress_message_count': progress_message_count,
              }
    return params


def is_inappropriate(content):
    gpt_filter = GPT()
    result = gpt_filter.add_setting(system_setting).add_user_message(content).request()
    if result.startswith("1"):
        return True
    elif result.startswith("0"):
        return False
    else:
        logging.warning(
            "inappropriate_filter returned unexpected value. inappropriate_filter_prompt may need to be updated.")
        return False


# メッセージを送信する
def post(form: NewTalkForm, sender: CustomUser):
    receiver = decide_reciever(sender)  # 送信先決定
    new_talk = Talks(sending_user=sender,
                     receiving_user=receiver)  # idにどのようなidを入れるかで送り先が変わる
    new_talk.save()

    # トークを開始した日付の表示用のダミーメッセージを保存
    date_message = Message(content="date_data", is_date=1, sending_user=sender)
    date_message.talk = new_talk
    date_message.save()

    # 新規投稿した人にカウント
    sending_user_info = UserInfo.objects.get(user_id=sender)
    sending_user_info.count_send_new_messages += 1
    sending_user_info.count_send_new_messages_in_a_day += 1
    sending_user_info.save()

    # 新規投稿が送られた人にカウント
    recieving_user_info = UserInfo.objects.get(user_id=receiver.id)
    recieving_user_info.count_receive_new_messages += 1
    recieving_user_info.capacity_new_msg -= 1
    recieving_user_info.save()

    # メッセージの保存
    message = form.save(commit=False)
    message.talk = new_talk
    message.save()


# トーク一覧画面
def talk_all(request):
    params = my_talks_classification(request)

    # 投稿
    if request.method == 'POST':
        # 投稿上限数のチェック
        if new_post_count_in_last_24_hours(request.user) >= NEW_POST_LIMIT:
            messages.warning(request, f'投稿可能上限に達しました.24hで投稿できるのは7件までです.')
            return redirect("postapp:talk_all")

        form = NewTalkForm(request.POST)
        if form.is_valid():
            if is_inappropriate(form.cleaned_data["content"]):
                messages.warning(request, f'不適切な内容のためメッセージは削除されました.')
            else:
                post(form, request.user)
            return redirect('postapp:talk_all')
        else:
            return render(request, 'postapp/talk_create.html', {'form': form})

    else:
        if params["progress_message_count"] == 0:  # 進行中トークが無いためトーク一覧に新規投稿画面表示
            initial_dict = dict(sending_user=request.user)
            form = NewTalkForm(initial=initial_dict)
            params["form"] = form
            params["talk_exist"] = False
            return render(request, 'postapp/talk_all.html', params)
        else:  # トーク一覧へ
            params["talk_exist"] = True
            return render(request, "postapp/talk_all.html", params)


# 送り先を決定するアルゴリズム
def decide_reciever(sender: CustomUser):
    found_reciever = False
    receiver = None
    all_user_info = UserInfo.objects.all()
    df = read_frame(all_user_info, fieldnames=['user',
                                               'priority_rank',
                                               'capacity_new_msg'])
    cap = df['capacity_new_msg'].max() + 1
    exist_talk_count = 0
    while True:
        cap -= 1
        # print(f'capacity={cap}')
        for rank in range(1, 16 + 1):
            # print(f'rank={rank}')
            df_candidates = df[(df['capacity_new_msg'] == cap) &
                               (df['priority_rank'] == rank)]  # 今日の新規メッセージ受け取り残数がcap, 優先度ランクがrankのユーザーに絞る
            # print('----------  df_candidates  ------------')
            # print(df_candidates)
            # print('---------------------------------------')
            if len(df_candidates) == 0:
                continue  # 調べているrankのユーザーがいない時は次のrankを調べる
            candidates_choice_list = list(range(len(df_candidates)))
            # 候補者からランダムに選択してチェック
            while True:
                # print(f'選択肢 --> {candidates_choice_list}')
                if len(candidates_choice_list) == 0:
                    break  # 候補者を調べ切った時は次のrankを調べる
                # 絞ったユーザーの中からランダムに一人選択する
                rand_num = random.randint(0, len(candidates_choice_list) - 1)
                candidate_choice = candidates_choice_list[rand_num]
                # print(f'選択 --> {candidate_choice} ')
                candidate_user_id = df_candidates.iloc[candidate_choice, 0]  # candidate_choice行目 0列目のデータを取得(0列目はuserID)
                # print(f'ユーザーID {candidate_user_id}')
                candidate = CustomUser.objects.get(id=candidate_user_id)
                # print('候補者-->',candidate.username)
                # 候補者がadminならスキップする
                if candidate.username == 'admin':
                    # print('候補者がadminでした')
                    candidates_choice_list.pop(
                        candidates_choice_list.index(candidate_choice))  # 候補者の選択肢からから現在選択されているユーザーを削除
                    # print(f'候補{candidate_choice}を削除')
                    continue
                talk = Talks.objects.filter(Q(invalid=False), (Q(sending_user=sender) & Q(receiving_user=candidate)) | (
                        Q(sending_user=candidate) & Q(receiving_user=sender)))
                if len(talk) != 0:  # 候補者とのトークがある時はスキップ
                    # print('すでに送信先の候補者とのトークが存在しています')
                    candidates_choice_list.pop(
                        candidates_choice_list.index(candidate_choice))  # 候補者の選択肢からから現在選択されているユーザーを削除
                    # print(f'候補{candidate_choice}を削除')
                    exist_talk_count += 1
                    # print(f'exist_talk_count = {exist_talk_count}')
                    continue
                else:
                    if candidate == sender:  # 候補者が自分の時はスキップ
                        candidates_choice_list.pop(
                            candidates_choice_list.index(candidate_choice))  # 候補者の選択肢からから現在選択されているユーザーを削除
                        # print('候補者が自分でした')
                        # print(f'候補{candidate_choice}を削除')
                        continue
                    else:  # 候補者が自分でなければ送信先に決定
                        receiver = candidate
                        found_reciever = True
                if found_reciever:
                    break
            if found_reciever:
                break
        if found_reciever:
            break
        if exist_talk_count == len(df) - 2:  # -2はadminと自分を除くという意味
            logging.info('送信先が見つかりません(すべてのユーザーとトーク中です)')
            # my_talk = Talks.objects.filter( (Q(sending_user=request.user) | Q(receiving_user=request.user)) )
            # print(f'現在のトーク数 = {len(my_talk)}')
            # time.sleep(3)
            break
    logging.info(f'送信先 --> user_id={receiver.id} ')
    return receiver


# メッセージ送信先の優先度を更新する
def update_sending_priority_rank():
    # 優先度は4項目に対して、優先か否かが定義され、全部で16通りある
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
        binary = '0b' + str(int(binarys[0])) + str(int(binarys[1])) + \
                 str(int(binarys[2])) + str(int(binarys[3]))  # 10進数に変換
        priority_rank = 16 - int(binary, 2)  # 優先ランキング
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
    logging.info(f'関数を実行しました：{self_func_name}, time --> {func.executed_at}')


# 優先度の計算用のデータをリセットする
def reset_count_for_priority_rank():
    all_user_info = UserInfo.objects.all()
    upd_user_infos = []
    for user_info in all_user_info:
        user_info.count_receive_new_messages = 0
        user_info.count_first_reply = 0
        user_info.count_send_new_messages = 0
        user_info.count_login = 0
        upd_user_infos.append(user_info)
    update_columns = ['count_receive_new_messages', 'count_first_reply', 'count_send_new_messages', 'count_login']
    UserInfo.objects.bulk_update(upd_user_infos, fields=update_columns)
    # 実行時刻を保存
    self_func_name = sys._getframe().f_code.co_name
    func = Executedfunction.objects.get(name=self_func_name)
    func.executed_at = datetime.now(timezone.utc)
    func.save()
    logging.info(f'関数を実行しました：{self_func_name}, time --> {func.executed_at}')


# 新規トークフォーム
def talk_create(request):
    if request.method == 'POST':

        print("メッセージ数 : " + str(new_post_count_in_last_24_hours(request.user)))
        if new_post_count_in_last_24_hours(request.user) >= NEW_POST_LIMIT:
            messages.warning(
                request, f'投稿可能上限に達しました.24hで投稿できるのは7件までです.')
            return redirect("postapp:talk_all")

        form = NewTalkForm(request.POST)
        if form.is_valid():
            if is_inappropriate(form.cleaned_data["content"]):
                messages.warning(request, f'不適切な内容のためメッセージは削除されました.')
            else:
                post(form, request.user)
            return redirect('postapp:talk_all')
        else:
            return render(request, 'postapp/talk_create.html', {'form': form})

    else:

        initial_dict = dict(sending_user=request.user, )
        form = NewTalkForm(initial=initial_dict)
        return render(request, 'postapp/talk_create.html', {'form': form})


def generate_reply(request, talk_id):
    gpt = GPT()
    talk = Talks.objects.get(id=talk_id)
    if not is_talk_available(talk):  # 終了トークなのに誤って送信が行われた場合
        return redirect(request.META['HTTP_REFERER'])
    messages = Message.objects.filter(talk_id=talk_id).order_by('-created_at').reverse()
    for message in list(messages):
        if message.is_date:
            continue
        if message.sending_user == request.user:
            gpt.add_user_message(message.content)
        else:
            gpt.add_assistant_message(message.content)

    try:
        reply = gpt.request()

        message = Message(content=reply, sending_user=talk.receiving_user)
        message.talk = talk
        message.save()

        talk.exist_reply = True
        talk.save()
    except Exception:
        pass

    return redirect(request.META['HTTP_REFERER'])


# 既存トークフォーム
def talk_detail(request, talk_id):
    try:
        talk = Talks.objects.get(id=talk_id)
    except:
        return redirect("postapp:talk_all")
    if request.method == 'POST':
        if not is_talk_available(talk):  # 終了トークなのに誤って送信が行われた場合
            return redirect(request.META['HTTP_REFERER'])

        # 最新メッセージの作成日時を取得し、その日の最終時刻に修正
        latest_message = Message.objects.filter(talk_id=talk.id).latest("created_at").created_at
        latest_message_date = datetime(latest_message.year, latest_message.month, latest_message.day).date()

        form = MessageForm(request.POST)
        if form.is_valid():
            if is_inappropriate(form.cleaned_data["content"]):
                messages.warning(request, f'不適切な内容のためメッセージは削除されました.')
                return redirect("postapp:talk_detail", talk_id=talk_id)

            # TODO 送信したメッセージが最新のメッセージと比較して日付を跨いでいる場合
            # print(latest_message_date)
            # print(latest_message_date + timedelta(days=1))
            # print(datetime.today())
            # if (latest_message_date + timedelta(days=1)) < datetime.today():
            #     print("日付追加！")
            #     # 日付表示用のMessage生成し、トークと紐付けて保存
            #     message = Message(content="date_data", is_date=1, sending_user=request.user)
            #     message.talk = talk
            #     message.save()

            # 送信したメッセージを保存
            post = form.save(commit=False)
            post.save()

            # トークを未読状態に更新
            talk.detail_opened = False
            talk.save()

            return redirect(request.META['HTTP_REFERER'])

        else:
            message = Message.objects.filter(talk_id=talk_id).all

            # talk_allの内容を取得し、更にデータを格納している
            params = my_talks_classification(request)
            params['message_list'] = message
            params['form'] = form
            params['detail_talk_id'] = talk_id
            params['Exist_favorites'] = exist_favorites(request, talk)
            return render(request, 'postapp/talk_detail.html', params)
    else:
        # 返信がない かつ 自分がトークの開始者である 時はトーク詳細に入れない(トーク一覧に戻される)
        if (not talk.exist_reply) & (talk.sending_user == request.user):
            return redirect("postapp:talk_all")

        # 最新のメッセージの送信者が自分ではない場合、トークを既読状態にする
        newest_message = Message.objects.filter(talk_id=talk_id).latest("created_at")
        if newest_message.sending_user != request.user:
            talk.detail_opened = True
            talk.save()

        is_active = is_talk_available(talk)
        # 返信がない　かつ　トーク可能時間外の場合、トークを削除して一覧画面へ戻る
        if (not talk.exist_reply) and (not is_active):
            talk.invalidate()
            messages.info(request, 'このトークは終了しています')
            return redirect("postapp:talk_all")

        # トーク可能時間外の場合、事後公開情報を表示する
        if not is_active:
            # トーク相手を取得
            if request.user == talk.sending_user:
                talk_partner = talk.receiving_user
            else:
                talk_partner = talk.sending_user
            # talk_allの内容を取得し、更にデータを格納している
            params = my_talks_classification(request)
            params['message_list'] = Message.objects.filter(talk_id=talk.id).all()
            params['detail_talk_id'] = talk_id
            params['Exist_favorites'] = exist_favorites(request, talk)
            params['talk_is_dead'] = not is_active
            params['user_info'] = UserInfo.objects.get(user_id=talk_partner)
            params['sending_user'] = talk_partner
            return render(request, 'postapp/talk_detail.html', params)

        # トーク可能時間内の場合
        if not talk.exist_reply:
            receiving_user = talk.receiving_user
            # このトークにおける受信者が、送信したメッセージ(すなわち返信)の数
            reply_count = Message.objects.filter(Q(talk_id=talk_id) & Q(sending_user=receiving_user)).count()

            if reply_count != 0:
                talk.exist_reply = True
                talk.save()

                user_info = UserInfo.objects.get(user_id=receiving_user)
                user_info.count_first_reply += 1
                user_info.save()

        # talk_allの内容を取得し、更にデータを格納している
        initial_dict = {
            "sending_user": request.user, "talk": talk_id, }
        params = my_talks_classification(request)
        params['message_list'] = Message.objects.filter(talk_id=talk_id).all
        params['detail_talk_id'] = talk_id
        params['Exist_favorites'] = exist_favorites(request, talk)
        params['off_hours'] = not is_active
        params['form'] = MessageForm(initial=initial_dict)
        return render(request, 'postapp/talk_detail.html', params)


# お気に入り追加
def talk_favorite_add(request, talk_id):
    talk = Talks.objects.get(id=talk_id)
    favorites = Favorites(talk=talk, user=request.user)
    favorites.save()

    return redirect(request.META['HTTP_REFERER'])


# お気に入り削除
def talk_favorite_delete(request, talk_id):
    Favorites.objects.filter(Q(talk__id=talk_id) &
                             Q(user=request.user)).delete()

    talk = Talks.objects.get(id=talk_id)
    CheckExist = not (Favorites.objects.filter(talk__id=talk_id).exists())

    if talk.confirmed_by_receiving_user == 1 & talk.confirmed_by_sending_user == 1 & CheckExist:  # トークを削除するかの判定
        talk.invalidate()
        return redirect("postapp:talk_all")

    return redirect(request.META['HTTP_REFERER'])


# お気に入り追加_最終チェック
def final_favorite_add(request, talk_id):
    talk = Talks.objects.get(id=talk_id)
    favorites = Favorites(talk=talk, user=request.user)
    favorites.save()

    if talk.sending_user == request.user:
        talk.confirmed_by_sending_user = 1
    else:
        talk.confirmed_by_receiving_user = 1

    talk.save()

    return redirect("postapp:talk_all")


# 状況に応じてトークの削除
def final_favorite_delete(request, talk_id):
    talk = Talks.objects.get(id=talk_id)

    if talk.sending_user == request.user:
        talk.confirmed_by_sending_user = 1
    else:
        talk.confirmed_by_receiving_user = 1

    talk.save()

    CheckExist = not (Favorites.objects.filter(talk__id=talk_id).exists())

    if talk.confirmed_by_receiving_user == 1 & talk.confirmed_by_sending_user == 1 & CheckExist:  # トークを削除するかの判定
        talk.invalidate()

    return redirect("postapp:talk_all")


# すでにお気に入りしているため、confirmed_byを1へ
def confirmed_add(request, talk_id):
    talk = Talks.objects.get(id=talk_id)

    if talk.sending_user == request.user:
        talk.confirmed_by_sending_user = 1
    else:
        talk.confirmed_by_receiving_user = 1

    talk.save()

    return redirect("postapp:talk_all")
