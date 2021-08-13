from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import CustomUser
from django.conf import settings
from django.contrib.auth import get_user_model
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

from .forms import LoginForm, UserCreateForm, MyPasswordChangeForm, MyPasswordResetForm, MySetPasswordForm, EmailChangeForm, UserInfoUpdateForm, ReportForm
from .models import UserInfo, Report, ReportReasons,CustomUser
User = get_user_model()

# ログインユーザー自身以外は遷移できないようにするクラス
class OnlyYouMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        # 今ログインしてるユーザーのpkと、そのユーザー情報ページのpkが同じか、又はスーパーユーザーなら許可
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_admin


@login_required
def Top(request):
    user_info = request.user.user_info
    if user_info.country==None:
        print('-----------------国が登録されていないので登録ページに飛ぶ---------------')
        form = UserInfoUpdateForm(instance=user_info)
        return render(request, 'users/userinfo_update.html', {'form':form})
    else:
        return render(request, 'users/top.html')

@login_required
def profile(request,pk):
    '''
    現状、pk(ログインユーザーのid)は使わないが、受け取れるようにしておく
    '''
    return render(request,'users/profile.html', {'pk':pk})
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

# class Profile(LoginRequiredMixin, OnlyYouMixin, generic.TemplateView):
#     raise_exception = False # LoginRequiredMixinの設定（Falseにするとログインページへ、Trueだと403）
#     form_class = ReportForm
#     template_name = 'users/profile.html'

def report(request):
    if request.method=='POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            #送信内容を1個ずつ取り出してReportを新規作成する（ModelFormを使う意味ない..もっと良い方法がありそう）
            post = request.POST
            reason = ReportReasons.objects.get(id=int(post['reason']))
            user_reported = CustomUser.objects.get(id=int(post['user_reported']))
            user_reporting = request.user
            content = post['content']
            report = Report(reason=reason, user_reported=user_reported,\
                user_reporting=user_reporting, content=content)
            report.save()
            return render(request, 'users/top.html')
        else:
            return render(request, 'users/report.html',{'form':form})
    else:
        form = ReportForm()
        return render(request, 'users/report.html',{'form':form})

class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'users/login.html'


class Logout(LogoutView):
    """ログアウトページ"""
    template_name = 'users/top.html'


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

        subject = render_to_string('users/mail_template/create/subject.txt', context)
        message = render_to_string('users/mail_template/create/message.txt', context)

        user.email_user(subject, message)
        return redirect('users:user_create_done')


class UserCreateDone(generic.TemplateView):
    """ユーザー仮登録したよ"""
    template_name = 'users/user_create_done.html'


class UserCreateComplete(generic.TemplateView):
    """メール内URLアクセス後のユーザー本登録"""
    template_name = 'users/user_create_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

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


def EditUserInfo(request, info_id):
    user_info = UserInfo.objects.get(id=info_id)
    if user_info.user != request.user:
        return redirect('users:profile', pk=request.user.id)
    if request.method == 'POST':
        # return reverse('users:profile', kwargs={'pk': request.user.id})
        # messages.success(request, 'レコードを新規追加しました。')
        form = UserInfoUpdateForm(request.POST, request.FILES, instance=user_info)
        if form.is_valid():
            print('==========------------------============')
            form.save()
            return redirect('users:profile', pk=request.user.id)
        else:
            print('======================')
            print(form.errors)
            # return redirect('users:profile', pk=request.user.id)
            return render(request, 'users/userinfo_update.html', {'form':form})
    else:
        form = UserInfoUpdateForm(instance=user_info)
        return render(request, 'users/userinfo_update.html', {'form':form})


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

        subject = render_to_string('users/mail_template/email_change/subject.txt', context)
        message = render_to_string('users/mail_template/email_change/message.txt', context)
        send_mail(subject, message, None, [new_email])

        return redirect('users:email_change_done')


class EmailChangeDone(LoginRequiredMixin, generic.TemplateView):
    """メールアドレスの変更メールを送ったよ"""
    template_name = 'users/email_change_done.html'


class EmailChangeComplete(LoginRequiredMixin, generic.TemplateView):
    """リンクを踏んだ後に呼ばれるメアド変更ビュー"""
    template_name = 'users/email_change_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

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
