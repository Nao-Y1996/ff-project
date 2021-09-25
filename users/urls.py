from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name="users"
urlpatterns = [
    path('', views.Top, name='top'),
    path('profile', views.profile, name='profile'),
    # path('login', views.Login.as_view(), name='login'),
    path('login', views.Login, name='login'),
    path('logout',  views.Logout.as_view(), name='logout'),

    #新規登録用
    path('user_create/', views.UserCreate.as_view(), name='user_create'),
    path('user_create/done', views.UserCreateDone.as_view(), name='user_create_done'),
    path('user_create/complete/<token>/', views.UserCreateComplete.as_view(), name='user_create_complete'),
    
    # パスワード変更用
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_change/done/', views.PasswordChangeDone.as_view(), name='password_change_done'),
    
    # パスワードリセット用
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
    path('password_reset/confirm/<uidb64>/<token>/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('password_reset/complete/', views.PasswordResetComplete.as_view(), name='password_reset_complete'),
    
    # メールアドレスの変更
    path('email/change/', views.EmailChange.as_view(), name='email_change'),
    path('email/change/done/', views.EmailChangeDone.as_view(), name='email_change_done'),
    path('email/change/complete/<str:token>/', views.EmailChangeComplete.as_view(), name='email_change_complete'),
    
    # userinfoの編集
    path('userinfo/edit/<str:info_id>/', views.EditUserInfo, name='userinfo_edit'),
    
    # 通報
    path('report', views.report, name='report'),
    
    # 退会
    path('withdrawal', views.withdrawal, name='withdrawal'),
    
    # 再開
    path('reregistration', views.Reregistration, name='reregistration'),
    path('UserReregistrationComplete/<token>/', views.UserReregistrationComplete, name='UserReregistrationComplete'),
    
]
# 画像ファイルを扱うための記述
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
