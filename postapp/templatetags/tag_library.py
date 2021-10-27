from django import template
from math import modf
from postapp.models import Favorites,Message,Talks
register = template.Library()

#@register.filter(name="change_Range")
@register.simple_tag
def favorite_check(user,talk):
    try:
        Exist_favorites = talk.favorites_set.all().filter(user_id=user)[0] in user.favorites_set.all()
    except:
        Exist_favorites =  False

    return Exist_favorites

@register.simple_tag
def get_newest_message(talk_id):

    newest_message = Message.objects.filter(talk_id=talk_id).latest("created_at")#.order_by('-created_at')[0]
    newest_message = newest_message.content

    return newest_message
# def multiply(value1, value2):
#     return value1 * value2

# def change_Range(date_range):
#     # 経過年を算出
#     fst = date_range/365
#     # 整数と少数に分ける decimal=少数
#     decimal, year = modf(fst)

#     # 経過年を差し引いた経過月を算出
#     scd = (decimal*365)/(365/12)
#     decimal, month = modf(scd)

#     val = str(round(year))+' 年 '+str(round(month))+' か月'
#     return val