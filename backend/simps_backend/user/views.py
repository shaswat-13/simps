from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.db import connection,IntegrityError
import bcrypt as bcrypt
# Create your views here.
def landing(request):
    return render(request, 'user/landing.html')

def login(request):
    return render(request,'user/login.html')

def signup(request):
    if (request.method == 'POST'):
        full_name = request.POST.get('Full Name')
        username = request.POST.get('Username')
        email = request.POST.get('Email')
        password = request.POST.get('Password').encode('utf-8')
        password_hash = bcrypt.hashpw(password,bcrypt.gensalt()).decode('utf-8')
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s",[email])
            existing_user = cursor.fetchone()
        if existing_user:
            return render(request,"user/signup.html",{"error":"An account with the email already exists."})
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO users (full_name,email,password_hash,username) VALUES(%s,%s,%s,%s)"
                cursor.execute(sql,[full_name,email,password_hash,username])
        except IntegrityError:
            return render(request,"user/signup.html",{"error":"An account with the email already exists."})    
        return redirect("users:login")

    return render(request,"user/signup.html")