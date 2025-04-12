from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('prompts/', views.prompts_list, name='prompts_list'),
    path('prompts/<int:prompt_id>/edit/', views.edit_prompt, name='edit_prompt'),
    path('files/', views.files_list, name='files_list'),
    path('files/add/', views.add_file, name='add_file'),
    path('files/<int:file_id>/edit/', views.edit_file, name='edit_file'),
    path('users/', views.users_list, name='users_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
]