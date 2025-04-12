# Generated by Django 4.2.10 on 2025-04-11 18:19

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BotFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название файла')),
                ('file', models.FileField(upload_to='bot_files/', verbose_name='Файл')),
                ('file_type', models.CharField(choices=[('txt', 'Текстовый файл'), ('py', 'Python скрипт'), ('json', 'JSON файл'), ('env', 'Файл окружения'), ('other', 'Другой')], default='txt', max_length=50, verbose_name='Тип файла')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Файл бота',
                'verbose_name_plural': 'Файлы бота',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Prompt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_id', models.IntegerField(unique=True, verbose_name='ID вопроса')),
                ('title', models.CharField(max_length=200, verbose_name='Название промпта')),
                ('prompt_text', models.TextField(verbose_name='Текст промпта')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Промпт',
                'verbose_name_plural': 'Промпты',
                'ordering': ['question_id'],
            },
        ),
        migrations.CreateModel(
            name='TelegramUser',
            fields=[
                ('user_id', models.BigIntegerField(primary_key=True, serialize=False, verbose_name='ID пользователя')),
                ('username', models.CharField(blank=True, max_length=100, null=True, verbose_name='Имя пользователя')),
                ('first_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Имя')),
                ('last_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Фамилия')),
                ('joined_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата регистрации')),
                ('last_activity', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Последняя активность')),
                ('message_count', models.IntegerField(default=0, verbose_name='Количество сообщений')),
                ('role', models.CharField(blank=True, max_length=50, null=True, verbose_name='Роль')),
                ('specialization', models.CharField(blank=True, max_length=50, null=True, verbose_name='Специализация')),
                ('reminder_enabled', models.BooleanField(default=True, verbose_name='Уведомления включены')),
            ],
            options={
                'verbose_name': 'Пользователь Telegram',
                'verbose_name_plural': 'Пользователи Telegram',
                'ordering': ['-last_activity'],
            },
        ),
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_text', models.TextField(verbose_name='Текст напоминания')),
                ('reminder_time', models.DateTimeField(verbose_name='Время напоминания')),
                ('is_sent', models.BooleanField(default=False, verbose_name='Отправлено')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='bot_manager.telegramuser', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Напоминание',
                'verbose_name_plural': 'Напоминания',
                'ordering': ['reminder_time'],
            },
        ),
        migrations.CreateModel(
            name='MessageHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('user', 'Пользователь'), ('assistant', 'Бот')], max_length=20, verbose_name='Роль')),
                ('message', models.TextField(verbose_name='Сообщение')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='bot_manager.telegramuser', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'История сообщений',
                'verbose_name_plural': 'История сообщений',
                'ordering': ['-timestamp'],
            },
        ),
    ]
