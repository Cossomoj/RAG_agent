from django.db import models
from django.utils import timezone

class TelegramUser(models.Model):
    user_id = models.BigIntegerField(primary_key=True, verbose_name="ID пользователя")
    username = models.CharField(max_length=100, blank=True, null=True, verbose_name="Имя пользователя")
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Имя")
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Фамилия")
    joined_date = models.DateTimeField(default=timezone.now, verbose_name="Дата регистрации")
    last_activity = models.DateTimeField(default=timezone.now, verbose_name="Последняя активность")
    message_count = models.IntegerField(default=0, verbose_name="Количество сообщений")
    role = models.CharField(max_length=50, blank=True, null=True, verbose_name="Роль")
    specialization = models.CharField(max_length=50, blank=True, null=True, verbose_name="Специализация")
    reminder_enabled = models.BooleanField(default=True, verbose_name="Уведомления включены")

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.username or 'Нет имени'} (ID: {self.user_id})"

class MessageHistory(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="messages", verbose_name="Пользователь")
    role = models.CharField(max_length=20, choices=[('user', 'Пользователь'), ('assistant', 'Бот')], verbose_name="Роль")
    message = models.TextField(verbose_name="Сообщение")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Время")

    class Meta:
        verbose_name = "История сообщений"
        verbose_name_plural = "История сообщений"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.role}: {self.message[:50]}..."

class Reminder(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="reminders", verbose_name="Пользователь")
    reminder_text = models.TextField(verbose_name="Текст напоминания")
    reminder_time = models.DateTimeField(verbose_name="Время напоминания")
    is_sent = models.BooleanField(default=False, verbose_name="Отправлено")

    class Meta:
        verbose_name = "Напоминание"
        verbose_name_plural = "Напоминания"
        ordering = ['reminder_time']

    def __str__(self):
        return f"Напоминание для {self.user} в {self.reminder_time}"

class Prompt(models.Model):
    question_id = models.IntegerField(unique=True, verbose_name="ID вопроса")
    title = models.CharField(max_length=200, verbose_name="Название промпта")
    prompt_text = models.TextField(verbose_name="Текст промпта")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Промпт"
        verbose_name_plural = "Промпты"
        ordering = ['question_id']

    def __str__(self):
        return f"{self.title} (ID: {self.question_id})"

class BotFile(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название файла")
    file = models.FileField(upload_to='bot_files/', verbose_name="Файл")
    file_type = models.CharField(max_length=50, choices=[
        ('txt', 'Текстовый файл'),
        ('py', 'Python скрипт'),
        ('json', 'JSON файл'),
        ('env', 'Файл окружения'),
        ('other', 'Другой')
    ], default='txt', verbose_name="Тип файла")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Файл бота"
        verbose_name_plural = "Файлы бота"
        ordering = ['-updated_at']

    def __str__(self):
        return self.name
