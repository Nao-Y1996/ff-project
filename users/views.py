from django.contrib.auth import logout
from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import CustomUser
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views import generic
from django.core.mail import send_mail
from django.views.generic import FormView, UpdateView
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import LoginForm, UserCreateForm, MyPasswordChangeForm, MyPasswordResetForm, \
    MySetPasswordForm, EmailChangeForm, UserInfoUpdateForm, ReportForm, UserReregistrationForm  # WithdrawalForm
from .models import UserInfo, Report, ReportReasons, CustomUser
from datetime import datetime, timezone
from dateutil import tz
from postapp.views import update_count_for_priority, update_seiding_priority
from postapp.models import Executedfunction
import urllib
from urllib.parse import urlparse

from django.forms.models import modelformset_factory
from django.db import transaction
User = get_user_model()

# ログインユーザー自身以外は遷移できないようにするクラス
class OnlyYouMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        # 今ログインしてるユーザーのpkと、そのユーザー情報ページのpkが同じか、又はスーパーユーザーなら許可
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_admin


def Top(request):
    # ログインしていたら
    if request.user.is_authenticated:
        user_info = request.user.user_info
        # 国情報登録していなかったら
        if user_info.nationality == None:
            form = UserInfoUpdateForm(instance=user_info)
            return redirect('users:userinfo_edit', info_id=user_info.id)
        else:
            return redirect('users:profile')
    else:
        return render(request, 'users/top.html')


@login_required
def profile(request):
    user_info = request.user.user_info
    # 国が登録されていない時は登録ページに飛ぶ
    if user_info.nationality == None:
        form = UserInfoUpdateForm(instance=user_info)
        return redirect('users:userinfo_edit', info_id=user_info.id)
    else:
        exist_profile_image = bool(user_info.profile_image)
        if exist_profile_image:
            profile_image = 'media/'+str(user_info.profile_image)
        else:
            profile_image = 'media/no_image.png'
    return render(request, 'users/profile.html', {'profile_image': profile_image})
    # if request.method == 'POST':
    #     if form.is_valid():
    #         form = ReportForm(request.POST)
    #         form.save()
    #         return redirect('users:profile', pk=request.user.id)
    #     else:
    #         return render(request, 'users/profile.html', {'form':form})
    # else:
    #     form = ReportForm()
    #     return render(request,'users/profile.html', {'form':form, 'id':pk})


@login_required
def report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            # 送信内容を1個ずつ取り出してReportを新規作成する（ModelFormを使う意味ない..もっと良い方法がありそう）
            post = request.POST
            reason = ReportReasons.objects.get(id=post['reason'])
            user_reported = CustomUser.objects.get(id=post['user_reported'])
            user_reporting = request.user
            content = post['content']
            report = Report(reason=reason, user_reported=user_reported,
                            user_reporting=user_reporting, content=content)
            report.save()
            return redirect('users:profile')
        else:
            return render(request, 'users/report.html', {'form': form})
    else:
        form = ReportForm()
        return render(request, 'users/report.html', {'form': form})


def Login(request):
    if request.method == 'POST':
        email = request.POST['username']
        password = request.POST['password']
        # 退会済みかどうかのチェック
        try:
            user = CustomUser.objects.get(email=email)
            if not user.is_active:
                messages.warning(
                    request, f'You have already withdrawn from this site.')
                form = LoginForm({"email": email, "password": password})
                return render(request, 'users/login.html', {'form': form})
        except CustomUser.DoesNotExist:
            pass
        # パスワードとメールで認証
        user = authenticate(request, email=email, password=password)
        if user is not None:
            last_login = user.last_login # UTC
            now = datetime.now(timezone.utc)
            # 初回ログインをしたらログインカウントをインクリメント
            if last_login is None:
                user.user_info.count_login += 1
                user.user_info.save()
            else:
                # 24時間以上、メッセージ送信の優先順位が更新されていなかったら更新
                priority_updated_at = Executedfunction.objects.get(name='update_seiding_priority').executed_at
                if ((now - priority_updated_at).seconds > 24*60*60):
                    update_seiding_priority()
                else:
                    pass
                # 24時間以上ぶりにログインしたらログインカウントをインクリメント
                if ((now - last_login).seconds > 24*60*60):
                    user.user_info.count_login += 1
                    user.user_info.save()
                elif user.user_info.count_login == 0:
                    user.user_info.count_login += 1
                    user.user_info.save()
                else:
                    pass
                # 1週間以上、更新関数が実行されていなかったら実行する
                count_updated_at = Executedfunction.objects.get(name='update_count_for_priority').executed_at
                if ((now - count_updated_at).seconds > 7*24*60*60):
                    update_count_for_priority()
                else:
                    pass
            login(request, user)  # ログイン
            return redirect('postapp:talk_all')
        else:
            # form = LoginForm(initial={"username":email, 'password':password}) # htmlで　form.errosでエラーが出なくなってしまう
            form = LoginForm(request, request.POST)
            form.is_valid()
            # form.add_error(None, 'LOGIN_ID、またはPASSWORDが違います。')
            return render(request, 'users/login.html', {'form': form})
    else:
        form = LoginForm()
        return render(request, 'users/login.html', {'form': form})


class Logout(LogoutView):
    """ログアウトページ"""
    template_name = 'users/top.html'


def Reregistration(request):
    if request.method == 'POST':
        """ユーザー再登録"""
        # template_name = 'users/reregistration.html'
        form = UserReregistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except CustomUser.DoesNotExist:
                form.add_error(None, 'The user with such email does not exist')
                return render(request, 'users/reregistration.html', {'form': form})
            except:
                import traceback
                traceback.print_exc()
                pass
                return render(request, 'users/reregistration.html', {'form': form})
            if user.is_active:
                form.add_error(
                    None, 'Your account is active. Please try login')
                return render(request, 'users/reregistration.html', {'form': form})
            else:
                # アクティベーションURLの送付
                current_site = get_current_site(request)
                domain = current_site.domain
                context = {
                    'protocol': request.scheme,
                    'domain': domain,
                    'token': dumps(user.pk),
                    'user': user,
                }
            # subject = render_to_string(
            #     'users/mail_template/create/subject.txt', context)
            subject = 'Reregistration'
            message = render_to_string(
                'users/mail_template/reregistration/message.txt', context)
            user.email_user(subject, message)
            messages.info(
                request, f'メールを確認してください。再登録用のリンクを登録されたメールアドレス宛にに送信しました。')
            return redirect('users:top')
        else:
            return render(request, 'users/reregistration.html', {'form': form})
    else:
        form = UserReregistrationForm()
        return render(request, 'users/reregistration.html', {'form': form})


def UserReregistrationComplete(request, **kwargs):
    # template_name = 'users/user_create_complete.html'
    timeout_seconds = getattr(
        settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

    # def get(self, request, **kwargs):
    user_create_completed = False
    token = kwargs.get('token')
    try:
        user_pk = loads(token, max_age=timeout_seconds)

    # 期限切れ
    except SignatureExpired:
        return HttpResponseBadRequest()

    # tokenが間違っている
    except BadSignature:
        return HttpResponseBadRequest()

    # tokenは問題なし
    else:
        try:
            user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            return HttpResponseBadRequest()
        else:
            if not user.is_active:
                # 問題なければ本登録とする
                user.is_active = True
                user.save()
                user_create_completed = True
                # return super().get(request, **kwargs)
    messages.info(
        request, f'再開処理を完了しました。ログインできます。')
    form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

# --------------------------------------------------------------


class UserCreate(generic.CreateView):
    """ユーザー仮登録"""
    template_name = 'users/user_create.html'
    form_class = UserCreateForm

    def form_valid(self, form):
        """仮登録と本登録用メールの発行."""
        # 仮登録と本登録の切り替えは、is_active属性を使う。
        # 退会処理も、is_activeをFalseにするだけにしておく。
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': self.request.scheme,
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
        }

        subject = render_to_string(
            'users/mail_template/create/subject.txt', context)
        message = render_to_string(
            'users/mail_template/create/message.txt', context)

        user.email_user(subject, message)
        return redirect('users:user_create_done')


class UserCreateDone(generic.TemplateView):
    """ユーザー仮登録したよ"""
    template_name = 'users/user_create_done.html'


class UserCreateComplete(generic.TemplateView):
    """メール内URLアクセス後のユーザー本登録"""
    template_name = 'users/user_create_complete.html'
    timeout_seconds = getattr(
        settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録."""
        user_create_completed = False
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    # 問題なければ本登録とする
                    user.is_active = True
                    user.save()
                    user_create_completed = True
                    # return super().get(request, **kwargs)
        if user_create_completed:
            user_info = UserInfo(user=user)
            user_info.save()
            return super().get(request, **kwargs)

        return HttpResponseBadRequest()


@login_required
def EditUserInfo(request, info_id):
    user_info = UserInfo.objects.get(id=info_id)
    if user_info.user != request.user:
        return redirect('users:profile')
    if request.method == 'POST':
        # return reverse('users:profile', kwargs={'pk': request.user.id})
        
        form = UserInfoUpdateForm(
            request.POST, request.FILES, instance=user_info)
        if form.is_valid():
            form.save()
            messages.success(request, 'Successful Update')
            return redirect("postapp:talk_all")
        else:
            # return redirect('users:profile', pk=request.user.id)
            return render(request, 'users/userinfo_update.html', {'form': form})
    else:
        form = UserInfoUpdateForm(instance=user_info)
        return render(request, 'users/userinfo_update.html', {'form': form})


# --------------------------------------------------------------
class PasswordChange(PasswordChangeView):
    """パスワード変更ビュー"""
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change.html'


class PasswordChangeDone(PasswordChangeDoneView):
    """パスワード変更しました"""
    template_name = 'users/password_change_done.html'


# --------------------------------------------------------------
class PasswordReset(PasswordResetView):
    """パスワードリセット用URLの送付ページ"""
    subject_template_name = 'users/mail_template/password_reset/subject.txt'
    email_template_name = 'users/mail_template/password_reset/message.txt'
    template_name = 'users/password_reset_form.html'
    form_class = MyPasswordResetForm
    success_url = reverse_lazy('users:password_reset_done')


class PasswordResetDone(PasswordResetDoneView):
    """パスワードリセット用URLを送りましたページ"""
    template_name = 'users/password_reset_done.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    """新パスワード入力ページ"""
    form_class = MySetPasswordForm
    success_url = reverse_lazy('users:password_reset_complete')
    template_name = 'users/password_reset_confirm.html'


class PasswordResetComplete(PasswordResetCompleteView):
    """新パスワード設定しましたページ"""
    template_name = 'users/password_reset_complete.html'


# --------------------------------------------------------------
class EmailChange(LoginRequiredMixin, generic.FormView):
    """メールアドレスの変更"""
    template_name = 'users/email_change_form.html'
    form_class = EmailChangeForm

    def form_valid(self, form):
        user = self.request.user
        new_email = form.cleaned_data['email']

        # URLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(new_email),
            'user': user,
        }

        subject = render_to_string(
            'users/mail_template/email_change/subject.txt', context)
        message = render_to_string(
            'users/mail_template/email_change/message.txt', context)
        send_mail(subject, message, None, [new_email])

        return redirect('users:email_change_done')


class EmailChangeDone(LoginRequiredMixin, generic.TemplateView):
    """メールアドレスの変更メールを送ったよ"""
    template_name = 'users/email_change_done.html'


class EmailChangeComplete(LoginRequiredMixin, generic.TemplateView):
    """リンクを踏んだ後に呼ばれるメアド変更ビュー"""
    template_name = 'users/email_change_complete.html'
    timeout_seconds = getattr(
        settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        token = kwargs.get('token')
        try:
            new_email = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            User.objects.filter(email=new_email, is_active=False).delete()
            request.user.email = new_email
            request.user.save()
            return super().get(request, **kwargs)


# --------------------------------------------------------------


@login_required
def withdrawal(request):
    if request.method == 'POST':
        user = request.user
        try:
            user.is_active = False
            user.save()
            logout(request)
            return redirect('users:top')
        except:
            return render(request, 'users/withdrawal.html')
    else:
        # form = WithdrawalForm
        return render(request, 'users/withdrawal.html')



def EmailPasswordView(request):
     
    template_name = 'users/profile.html'
 
    # フォームセット定義
    MyFormSet_1= modelformset_factory(
        model=CustomUser,
        form=EmailChangeForm,
        extra=1, # セットの表示数 defaultは1
        max_num=1 # 最大表示数 defaultは1
    )
    MyFormSet_2= modelformset_factory(
        model=CustomUser,
        form=MyPasswordChangeForm,
        extra=2, # セットの表示数 defaultは1
        max_num=2 # 最大表示数 defaultは1
    )
 
    if request.method == 'GET' :

        # フォームの初期値を指定する場合
        """ form_1_initial = [{
            'field_1' : 'initial_value_1',
            'field_2' : 'initial_value_2',
        }]
        form_2_initial = [{
            'field_1' : 'initial_value_1',
            'field_2' : 'initial_value_2',
        }] """
        # フォームセットのオブジェクト生成
        form_set_1 = MyFormSet_1(
            #initial=form_1_initial,
            # 新規作成フォームのみ表示(既存レコードは表示しない)
            queryset=CustomUser.objects.none()
        )
        form_set_2 = MyFormSet_2(
            #initial=form_2_initial,
            queryset=CustomUser.objects.none()
        )

    else : # POST
        
        # POSTされたデータをコピー（直接編集しようとすると怒られる）
        post_form_set_1 = request.POST.copy()
        post_form_set_2 = request.POST.copy()
 
        # 'form-TOTAL_FORMS'をもともとのextraの値に上書き
        post_form_set_1['form-TOTAL_FORMS'] = 1
        post_form_set_2['form-TOTAL_FORMS'] = 1
 
        # 改めてオブジェクト生成
        form_set_1 = MyFormSet_1(post_form_set_1 )
        form_set_2 = MyFormSet_2(post_form_set_2 )
 
        if form_set_1.is_valid():
            post_form_set_1 = form_set_1.save(commit=False)

            user = request.user
            new_email = form_set_1.save(commit=False)
            print("*"*40)
            print(new_email)

            # URLの送付
            current_site = get_current_site(request)
            domain = current_site.domain
            context = {
                'protocol': 'https' if request.is_secure() else 'http',
                'domain': domain,
                'token': dumps(new_email),
                'user': user,
            }

            subject = render_to_string(
                'users/mail_template/email_change/subject.txt', context)
            message = render_to_string(
                'users/mail_template/email_change/message.txt', context)
            send_mail(subject, message, None, [new_email])

            return redirect('users:email_change_done')
            
            
            
            """ # 保存処理
            with transaction.atomic() :
                # 各々save
                for p in post_form_set_1 :
                    # さらに他のフォームを併設している場合、そこでsaveしたレコードのPKを使う場合はobject.pkでとれる
                    #p.parent_pk = other_post.pk
                    p.save() """
            messages.info(request, f'保存しました。')
            return redirect('postapp:talk_all')
        
        if  form_set_2.is_valid():
            
            post_form_set_2 = form_set_2.save(commit=False)
            # 保存処理
            with transaction.atomic() :
                # 各々save
                for p in post_form_set_2 :
                    p.save()
            messages.info(request, f'保存しました。')
            return redirect('postapp:talk_all')
 
    # レンダリング
    context = {
        'form_set_1': form_set_1,
        'form_set_2': form_set_2,
    }
    return render(request, 'users/profile.html', context)