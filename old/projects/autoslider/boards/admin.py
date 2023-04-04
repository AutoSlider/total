from django.contrib import admin
from .models import Board

# Register your models here.

# admin.site.register(Board)
@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user_id', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'favorite')
    search_fields = ('title', 'input_type', 'note', 'user_id__email')

