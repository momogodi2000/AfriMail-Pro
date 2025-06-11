from django.urls import path
from . import views



urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('forgot-password/', views.ForgotPassword, name='forgot_password'),
    path('condiction/', views.condiction, name='condiction'),
    path('policy/', views.policy, name='policy'),


    # Admin Dashboard URLs
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
]