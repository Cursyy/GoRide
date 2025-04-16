from django.contrib import admin
from .models import AvatarItem, UserAvatar
# Register your models here.

class AvatarItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'condition')

class UserAvatarAdmin(admin.ModelAdmin):
    list_display = ('user', 'equipped_hat', 'equipped_shirt', 'equipped_accessory', 'equipped_background')

admin.site.register(AvatarItem, AvatarItemAdmin)
admin.site.register(UserAvatar, UserAvatarAdmin)