from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from .models import Prompt, BotFile, TelegramUser, MessageHistory
from .forms import PromptForm, BotFileForm
from django.db.models import Count, Max, Min, Avg
from django.utils import timezone
from datetime import timedelta


@login_required
def home(request):
	# Основная статистика
	total_users = TelegramUser.objects.count()
	active_users_week = TelegramUser.objects.filter(last_activity__gte=timezone.now() - timedelta(days=7)).count()
	total_messages = MessageHistory.objects.count()

	# Статистика по ролям и специализациям
	roles = TelegramUser.objects.exclude(role__isnull=True).values('role').annotate(count=Count('role')).order_by(
		'-count')
	specializations = TelegramUser.objects.exclude(specialization__isnull=True).values('specialization').annotate(
		count=Count('specialization')).order_by('-count')

	# Активность по дням недели
	last_week = timezone.now() - timedelta(days=7)
	daily_activity = MessageHistory.objects.filter(timestamp__gte=last_week).extra(
		select={'day': "strftime('%%w', timestamp)"}
	).values('day').annotate(count=Count('id')).order_by('day')

	# Преобразуем цифры дней недели в названия
	days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
	for item in daily_activity:
		item['day_name'] = days[int(item['day'])]

	context = {
		'total_users': total_users,
		'active_users_week': active_users_week,
		'total_messages': total_messages,
		'roles': roles,
		'specializations': specializations,
		'daily_activity': daily_activity,
	}
	return render(request, 'bot_manager/home.html', context)


@login_required
def prompts_list(request):
	prompts = Prompt.objects.all().order_by('question_id')
	return render(request, 'bot_manager/prompts_list.html', {'prompts': prompts})


@login_required
def edit_prompt(request, prompt_id):
	prompt = get_object_or_404(Prompt, id=prompt_id)

	if request.method == 'POST':
		form = PromptForm(request.POST, instance=prompt)
		if form.is_valid():
			form.save()
			messages.success(request, f'Промпт "{prompt.title}" успешно обновлен')
			return redirect('prompts_list')
	else:
		form = PromptForm(instance=prompt)

	return render(request, 'bot_manager/edit_prompt.html', {'form': form, 'prompt': prompt})


@login_required
def files_list(request):
	files = BotFile.objects.all().order_by('-updated_at')
	return render(request, 'bot_manager/files_list.html', {'files': files})


@login_required
def add_file(request):
	if request.method == 'POST':
		form = BotFileForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			messages.success(request, 'Файл успешно добавлен')
			return redirect('files_list')
	else:
		form = BotFileForm()

	return render(request, 'bot_manager/add_file.html', {'form': form})


@login_required
def edit_file(request, file_id):
	bot_file = get_object_or_404(BotFile, id=file_id)

	if request.method == 'POST':
		form = BotFileForm(request.POST, request.FILES, instance=bot_file)
		if form.is_valid():
			form.save()
			messages.success(request, f'Файл "{bot_file.name}" успешно обновлен')
			return redirect('files_list')
	else:
		form = BotFileForm(instance=bot_file)

	return render(request, 'bot_manager/edit_file.html', {'form': form, 'bot_file': bot_file})


@login_required
def users_list(request):
	users = TelegramUser.objects.all().order_by('-last_activity')
	return render(request, 'bot_manager/users_list.html', {'users': users})


@login_required
def user_detail(request, user_id):
	user = get_object_or_404(TelegramUser, user_id=user_id)
	messages_history = MessageHistory.objects.filter(user=user).order_by('-timestamp')[:50]

	# Статистика пользователя
	message_count = messages_history.count()
	first_message = MessageHistory.objects.filter(user=user).order_by('timestamp').first()
	last_message = MessageHistory.objects.filter(user=user).order_by('-timestamp').first()

	# Активность по дням недели
	last_month = timezone.now() - timedelta(days=30)
	daily_activity = MessageHistory.objects.filter(
		user=user,
		timestamp__gte=last_month
	).extra(
		select={'day': "strftime('%%w', timestamp)"}
	).values('day').annotate(count=Count('id')).order_by('day')

	# Преобразуем цифры дней недели в названия
	days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
	for item in daily_activity:
		item['day_name'] = days[int(item['day'])]

	context = {
		'tg_user': user,
		'messages_history': messages_history,
		'message_count': message_count,
		'first_message': first_message,
		'last_message': last_message,
		'daily_activity': daily_activity,
	}
	return render(request, 'bot_manager/user_detail.html', context)
