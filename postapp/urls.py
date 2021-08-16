from django.urls import path
from . import views

app_name = 'postapp'

urlpatterns = [
    # path('', views.Top.as_view(), name='top'),
    # path('login/', views.Login.as_view(), name='login'),
    # path('logout/', views.Logout.as_view(), name='logout'),
    # path('mypage/', views.mypage, name='mypage'),
    path('talk_all/', views.talk_all, name='talk_all'),
    path('talk_create/', views.talk_create, name='talk_create'),
    path('talk_detail/<str:talk_id>/', views.talk_detail, name='talk_detail'),
    path('talk_favorite_add/<str:talk_id>/', views.talk_favorite_add, name='talk_favorite_add'),
    path('talk_favorite_delete/<str:talk_id>/', views.talk_favorite_delete, name='talk_favorite_delete'),

]