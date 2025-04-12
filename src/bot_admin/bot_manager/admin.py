from django.contrib import admin
from .models import TelegramUser, MessageHistory, Reminder, Prompt, BotFile
from django.urls import reverse
from django.utils.html import format_html


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
	list_display = ('user_id', 'username', 'role', 'specialization', 'message_count', 'last_activity', 'view_messages')
	search_fields = ('user_id', 'username', 'first_name', 'last_name')
	list_filter = ('role', 'specialization', 'reminder_enabled')
	readonly_fields = (
	'user_id', 'username', 'first_name', 'last_name', 'joined_date', 'last_activity', 'message_count', 'role',
	'specialization')

	def view_messages(self, obj):
		url = reverse('admin:bot_manager_messagehistory_changelist') + f'?user__user_id={obj.user_id}'
		return format_html('<a href="{}">Просмотр сообщений</a>', url)

	view_messages.short_description = "Сообщения"

	def has_add_permission(self, request):
		return False

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
	list_display = ('timestamp', 'user', 'role', 'short_message')
	list_filter = ('role', 'timestamp')
	search_fields = ('message', 'user__username')
	readonly_fields = ('user', 'role', 'message', 'timestamp')

	def short_message(self, obj):
		return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message

	short_message.short_description = "Сообщение"

	def has_add_permission(self, request):
		return False

	def has_delete_permission(self, request, obj=None):
		return False

	def has_change_permission(self, request, obj=None):
		return False


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
	list_display = ('user', 'short_reminder_text', 'reminder_time', 'is_sent')
	list_filter = ('is_sent', 'reminder_time')
	search_fields = ('reminder_text', 'user__username')
	readonly_fields = ('user', 'reminder_text', 'reminder_time', 'is_sent')

	def short_reminder_text(self, obj):
		return obj.reminder_text[:100] + '...' if len(obj.reminder_text) > 100 else obj.reminder_text

	short_reminder_text.short_description = "Текст напоминания"

	def has_add_permission(self, request):
		return False

	def has_delete_permission(self, request, obj=None):
		return False

	def has_change_permission(self, request, obj=None):
		return False


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
	list_display = ('question_id', 'title', 'updated_at', 'edit_prompt')
	search_fields = ('title', 'prompt_text')
	readonly_fields = ('created_at', 'updated_at')

	def edit_prompt(self, obj):
		url = reverse('edit_prompt', args=[obj.id])
		return format_html('<a href="{}">Редактировать промпт</a>', url)

	edit_prompt.short_description = "Действия"

	def has_add_permission(self, request):
		return False

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(BotFile)
class BotFileAdmin(admin.ModelAdmin):
	list_display = ('name', 'file_type', 'uploaded_at', 'updated_at', 'edit_file')
	list_filter = ('file_type', 'uploaded_at')
	search_fields = ('name', 'description')

	def edit_file(self, obj):
		url = reverse('edit_file', args=[obj.id])
		return format_html('<a href="{}">Редактировать файл</a>', url)

	edit_file.short_description = "Действия"
