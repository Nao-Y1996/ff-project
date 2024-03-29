from django import template
from math import modf
from postapp.models import Favorites,Message,Talks
from users.models import CustomUser
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

    newest_message = Message.objects.filter(talk_id=talk_id, is_date=False).latest("created_at")
    newest_message = newest_message.content

    return newest_message

@register.simple_tag
def integer_to_string(integer):
    
    string=str(integer)
    string="A"+string[2:]
    return string

@register.simple_tag
def get_talk_partner(user, talk):
    if talk.sending_user == user:
        talk_partner = talk.receiving_user
    else:
        talk_partner = talk.sending_user
    return talk_partner

@register.simple_tag
def check_is_detail(talk, detail_talk_id):
    if str(talk.id) == detail_talk_id:
        is_detail = 'is_detail_true'
    else:
        is_detail = ''
    return is_detail

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