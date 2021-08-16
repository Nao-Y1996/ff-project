from django.contrib import admin
from postapp.models import Favorites,Talks,Message
# Register your models here.

admin.site.register(Favorites)
admin.site.register(Talks)
admin.site.register(Message)