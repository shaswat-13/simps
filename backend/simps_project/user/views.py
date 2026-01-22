from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.db import connection,IntegrityError
from django.contrib import auth
import bcrypt as bcrypt


# Create your views here.
def landing(request):
    return render(request, 'user/landing.html')

def login(request):
    errors =[]
    if (request.method == 'POST'):
        identifier = request.POST.get('Email')
        login_pw = request.POST.get('Password')
        with connection.cursor() as cursor:
            cursor.execute("SELECT password_hash,user_id FROM users WHERE email = %s OR username = %s",[identifier,identifier])
            stored_hash = cursor.fetchone() 
        if (stored_hash == None):
            errors.append("User with this email/username doesn't exist")   
        is_correct = bcrypt.checkpw(login_pw.encode('utf-8'),stored_hash[0].encode('utf-8'))
        if (not is_correct):
            errors.append("Invalid username or password")
        if (errors):
            context = {"error":errors[0],"form_data":request.POST}
            return render(request,"user/login.html",context)
        
        #setting session

        request.session['user_id']=stored_hash[1]
        request.session.set_expiry(7*24*60*60)
        
        #redirect to dashboard
        return redirect("users:landing")
    return render(request,"user/login.html")

def signup(request):
    errors=[]
    if (request.method == 'POST'):
        full_name = request.POST.get('Full_Name')
        username = request.POST.get('Username','').strip()
        email = request.POST.get('Email')
        password = request.POST.get('Password').encode('utf-8')
        confirm_pw = request.POST.get('Confirm_password').encode('utf-8')
        password_hash = bcrypt.hashpw(password,bcrypt.gensalt()).decode('utf-8')

        if(password!=confirm_pw):
            errors.append("Passwords do not match.")
        #Checking email and username validity
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s",[email])
            existing_user = cursor.fetchone()
        if existing_user:
            errors.append("An account with the email already exists.")
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s",[username])
            existing_username = cursor.fetchone()
        if not is_valid_email(email):
            errors.append("Please enter a valid email.")
        if existing_username:
            errors.append("Username taken. Try another one.")
        
        if ' ' in username:
            errors.append("Username cannot contain spaces.")
        if (errors):
            context = {"error":errors[0],"form_data":request.POST}
            return render(request, "user/signup.html",context)      

        try:
            #Adding account to DB
            with connection.cursor() as cursor:
                sql = "INSERT INTO users (full_name,email,password_hash,username) VALUES(%s,%s,%s,%s)"
                cursor.execute(sql,[full_name,email,password_hash,username])
        except IntegrityError:
            return render(request, "user/signup.html",{"error":errors[0]}) 
        
        return redirect("users:login")

    return render(request,"user/signup.html")


#function to check email validity
def is_valid_email(identifier):
    if (identifier.count("@") !=1):
        return False
    
    local, domain = identifier.split("@")
    if (not local):
        return False
    if ("." not in domain):
        return False
    
    if (domain.startswith(".") or domain.endswith(".")):
        return False
    
    return True