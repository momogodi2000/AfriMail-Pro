from django.shortcuts import render

# Create your views here.

def homepage(request):
    return render(request, 'LandingPage/homepage.html')

def login(request):
    return render(request, 'Authentification/Login.html')

def register(request):
    return render(request, 'Authentification/register.html')

def ForgotPassword(request):
    return render(request, 'Authentification/Forgot_passwords.html')

def condiction(request):
    return render(request, 'LandingPage/conditions-utilisation.html')

def policy(request):
    return render(request, 'LandingPage/politique-confidentialite.html')

def admin_dashboard(request):
    return render(request, 'Dashboard/admin/admin_dashboard.html')