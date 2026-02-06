from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ["id", "role", "content", "created_at"]
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["customer_identifier", "company", "channel", "status", "created_at"]
    list_filter = ["channel", "status", "company"]
    search_fields = ["customer_identifier"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "role", "short_content", "created_at"]
    list_filter = ["role", "conversation__company"]
    readonly_fields = ["id", "created_at"]

    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    short_content.short_description = "Content"
