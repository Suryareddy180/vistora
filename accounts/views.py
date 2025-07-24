import random
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify

from accounts.models import *
from accounts.utils import sendEmailToken, generateRandomToken, sendOTPtoEmail, generateSlug


def login_page(request):
    if not request.user.is_authenticated and request.GET.get('next'):
        messages.warning(request, "Please login to continue")

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        hotel_user = HotelUser.objects.filter(email=email)

        if not hotel_user.exists():
            messages.warning(request, "No Account Found.")
            return redirect('login_page')

        if not hotel_user[0].is_verified:
            messages.warning(request, "Account not verified")
            return redirect('login_page')

        hotel_user = authenticate(username=hotel_user[0].username, password=password)

        if hotel_user:
            messages.success(request, "Login Success")
            login(request, hotel_user)
            next_url = request.GET.get('next')
            return redirect(next_url) if next_url else redirect('index_main')

        messages.warning(request, "Invalid credentials")
        return redirect('login_page')

    return render(request, 'accounts/login.html')


def register(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone_number = request.POST.get('phone_number')

        hotel_user = HotelUser.objects.filter(Q(email=email) | Q(phone_number=phone_number))

        if hotel_user.exists():
            messages.warning(request, "Account exists with Email or Phone Number.")
            return redirect('/account/register/')

        token = generateRandomToken()
        hotel_user = HotelUser.objects.create(
            username=phone_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            email_token=token
        )
        hotel_user.set_password(password)
        hotel_user.save()

        print(f"[DEBUG] Email Token Saved: {token}")  # Debug print
        sendEmailToken(email, token)

        messages.success(request, "An email has been sent to verify your account.")
        return redirect('/account/register/')

    return render(request, 'accounts/register.html')


from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import HotelUser, HotelVendor  # Make sure both are imported

def verify_email_token(request, token):
    try:
        hotel_user = HotelUser.objects.get(email_token=token)
        hotel_user.is_verified = True
        hotel_user.email_token = None  # Optional: remove token after use
        hotel_user.save()
        messages.success(request, "User email verified successfully!")
        return redirect('/account/login/')
    except HotelUser.DoesNotExist:
        pass  # Try the next one

    try:
        hotel_vendor = HotelVendor.objects.get(email_token=token)
        hotel_vendor.is_verified = True
        hotel_vendor.email_token = None
        hotel_vendor.save()
        messages.success(request, "Vendor email verified successfully!")
        return redirect('/account/login-vendor/')
    except HotelVendor.DoesNotExist:
        return HttpResponse("Invalid Token")


def send_otp(request, email):
    hotel_user = HotelUser.objects.filter(email=email)
    if not hotel_user.exists():
        messages.warning(request, "No Account Found.")
        return redirect('/account/login/')

    otp = random.randint(1000, 9999)
    hotel_user.update(otp=otp)

    sendOTPtoEmail(email, otp)
    return redirect(f'/account/verify-otp/{email}/')


def verify_otp(request, email):
    try:
        hotel_user = HotelUser.objects.get(email=email)
    except HotelUser.DoesNotExist:
        messages.error(request, "No account associated with this email.")
        return redirect('/account/login/')

    if request.method == "POST":
        otp = request.POST.get('otp')

        if otp == str(hotel_user.otp):
            messages.success(request, "Login Success")
            login(request, hotel_user)
            return redirect('index_main')

        messages.warning(request, "Wrong OTP")
        return redirect(f'/account/verify-otp/{email}/')

    return render(request, 'accounts/verify_otp.html')


def login_vendor(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        hotel_user = HotelVendor.objects.filter(email=email)

        if not hotel_user.exists():
            messages.warning(request, "No Account Found.")
            return redirect('/account/login-vendor/')

        if not hotel_user[0].is_verified:
            messages.warning(request, "Account not verified")
            return redirect('/account/login-vendor/')

        hotel_user = authenticate(username=hotel_user[0].username, password=password)

        if hotel_user:
            messages.success(request, "Login Success")
            login(request, hotel_user)
            return redirect('/account/dashboard/')

        messages.warning(request, "Invalid credentials")
        return redirect('/account/login-vendor/')
    return render(request, 'accounts/login_vendor.html')


def register_vendor(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        business_name = request.POST.get('business_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone_number = request.POST.get('phone_number')

        hotel_user = HotelUser.objects.filter(Q(email=email) | Q(phone_number=phone_number))
        if hotel_user.exists():
            messages.warning(request, "Account exists with Email or Phone Number.")
            return redirect('/account/register-vendor/')

        token = generateRandomToken()
        hotel_user = HotelVendor.objects.create(
            username=phone_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            business_name=business_name,
            email_token=token
        )
        hotel_user.set_password(password)
        hotel_user.save()

        print(f"[DEBUG] Vendor Email Token Saved: {token}")  # Debug
        sendEmailToken(email, token)

        messages.success(request, "An email has been sent to verify your account.")
        return redirect('/account/register-vendor/')

    return render(request, 'accounts/register_vendor.html')

def send_vendor_otp(request, email):
    hotel_vendor = HotelVendor.objects.filter(email=email)
    if not hotel_vendor.exists():
        messages.warning(request, "No Account Found.")
        return redirect('/account/login-vendor/')

    otp = random.randint(1000, 9999)
    hotel_vendor.update(otp=otp)

    sendOTPtoEmail(email, otp)
    return redirect(f'/account/verify-vendor-otp/{email}/')

def verify_vendor_otp(request, email):
    try:
        hotel_vendor = HotelVendor.objects.get(email=email)
    except HotelVendor.DoesNotExist:
        messages.error(request, "No vendor account associated with this email.")
        return redirect('/account/login-vendor/')

    if request.method == "POST":
        otp = request.POST.get('otp')
        if otp == str(hotel_vendor.otp):
            messages.success(request, "Login Success")
            login(request, hotel_vendor)
            return redirect('/account/dashboard/')

        messages.warning(request, "Wrong OTP")
        return redirect(f'/account/verify-vendor-otp/{email}/')

    return render(request, 'accounts/verify_otp.html')



from django.contrib.auth.decorators import login_required
from .models import Hotel

@login_required(login_url='login_vendor')
def dashboard(request):
    hotels = Hotel.objects.filter(hotel_owner=request.user)
    context = {'hotels': hotels}
    return render(request, 'accounts/vendor_dashboard.html', context)



@login_required(login_url='login_vendor')
def add_hotel(request):
    if request.method == "POST":
        hotel_name = request.POST.get('hotel_name')
        hotel_description = request.POST.get('hotel_description')
        hotel_price = request.POST.get('hotel_price')
        hotel_offer_price = request.POST.get('hotel_offer_price')
        hotel_location = request.POST.get('hotel_location')
        hotel_slug = generateSlug(hotel_name)

        hotel_vendor = HotelVendor.objects.get(id=request.user.id)

        hotel_obj = Hotel.objects.create(
            hotel_name=hotel_name,
            hotel_description=hotel_description,
            hotel_price=hotel_price,
            hotel_offer_price=hotel_offer_price,
            hotel_location=hotel_location,
            hotel_slug=hotel_slug,
            hotel_owner=hotel_vendor
        )

        amenities = request.POST.getlist('amenities')  # ← fixed spelling
        for amenity_id in amenities:
            amenity = Ameneties.objects.get(id=amenity_id)
            hotel_obj.amenities.add(amenity)

        messages.success(request, "Hotel Created")
        return redirect('/account/dashboard/')

    ameneties = Ameneties.objects.all()
    return render(request, 'accounts/add_hotel.html', context={'ameneties': ameneties})

@login_required(login_url='login_vendor')
def upload_images(request, slug):
    hotel_obj = get_object_or_404(Hotel, hotel_slug=slug)

    if request.method == "POST":
        if 'image' in request.FILES:
            image = request.FILES['image']
            print("Uploaded Image:", image)

            HotelImages.objects.create(
                hotel=hotel_obj,
                image=image
            )
            messages.success(request, "Image uploaded successfully!")
        else:
            messages.error(request, "No image selected. Please choose a file to upload.")
        return HttpResponseRedirect(request.path_info)

    return render(request, 'accounts/upload_images.html', {
        'images': hotel_obj.hotel_images.all()
    })

@login_required(login_url='login_vendor')
def delete_image(request, id):
    print(id)
    print("#######")
    hotel_image = HotelImages.objects.get(id = id)
    hotel_image.delete()
    messages.success(request, "Hotel Image deleted")
    return redirect('/account/dashboard/')


@login_required(login_url='login_vendor')
def edit_hotel(request, slug):
    try:
        hotel_obj = Hotel.objects.get(hotel_slug=slug)
    except Hotel.DoesNotExist:
        return HttpResponse("Hotel not found", status=404)

    if request.user.id != hotel_obj.hotel_owner.id:
        return HttpResponse("You are not authorized", status=403)

    if request.method == "POST":
        hotel_obj.hotel_name = request.POST.get('hotel_name')
        hotel_obj.hotel_description = request.POST.get('hotel_description')
        hotel_obj.hotel_price = request.POST.get('hotel_price')
        hotel_obj.hotel_offer_price = request.POST.get('hotel_offer_price')
        hotel_obj.hotel_location = request.POST.get('hotel_location')

        selected_amenities = request.POST.getlist('ameneties')
        hotel_obj.amenities.set(selected_amenities)

        hotel_obj.save()

        messages.success(request, "Hotel Details Updated")
        return HttpResponseRedirect(request.path_info)

    ameneties = Ameneties.objects.all()
    return render(request, 'accounts/edit_hotel.html', context={
        'hotel': hotel_obj,
        'ameneties': ameneties
    })
@login_required(login_url='login_vendor')
def delete_hotel(request, slug):
    try:
        hotel_obj = Hotel.objects.get(hotel_slug=slug)
        if request.user.id != hotel_obj.hotel_owner.id:
            return HttpResponse("Unauthorized", status=401)

        hotel_obj.delete()
        messages.success(request, "Hotel deleted successfully.")
    except Hotel.DoesNotExist:
        messages.error(request, "Hotel does not exist.")

    return redirect('/account/dashboard/')

def about(request):
    return render(request,'accounts/about.html')
def contact(request):
    return render(request,'accounts/contact.html')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

@login_required(login_url='login_vendor')
def vendor_ai_assistant(request):
    ai_response = ""
    if request.method == "POST":
        feature = request.POST.get("feature")
        hotel_name = request.POST.get("hotel_name")
        location = request.POST.get("location")
        price = request.POST.get("price")
        features = request.POST.get("features")

        # 🎯 Improved dynamic prompt
        prompt = ""
        if feature == "description":
            prompt = f"""
Write a clean, professional, and attractive hotel description for:
Hotel: {hotel_name}
Location: {location}
Features: {features}
Target Audience: travelers in India

Respond in plain text with no stars (*), hashtags (#), or markdown. Use headings and paragraphs only where needed. Keep tone elegant and inviting. Example style:

"Escape to Paradise at [Hotel Name], [Location]
Experience the magic of [Location] at [Hotel Name], a luxurious haven nestled amidst natural beauty. Wake up to crisp mountain air and breathtaking views. Our hotel combines traditional charm with modern amenities. Each room is designed for comfort, with thoughtful touches throughout.

Relax and rejuvenate after a day of exploring. Enjoy our swimming pool, high-speed Wi-Fi, and onsite dining serving authentic cuisine.

Book your stay today and create unforgettable memories. Visit [Website] or call [Phone Number] to reserve."
"""
        elif feature == "pricing":
            prompt = f"""
Suggest a competitive nightly price for:
Hotel: {hotel_name}
Location: {location}
Current Price: ₹{price}
Features: {features}
Consider seasonality, demand, location popularity, and similar hotels in the area. Provide only the recommended price and a one-line justification.
"""
        elif feature == "taglines":
            prompt = f"""
Generate 3 catchy marketing taglines for:
Hotel: {hotel_name}
Location: {location}
Features: {features}
Keep them short, modern, and appealing. No hashtags or emojis.
"""

        # Call Gemini API
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            ai_response = response.text.strip()
        except Exception as e:
            print("Gemini Error:", e)
            ai_response = "⚠️ AI could not process your request. Please try again later."

    return render(request, 'accounts/ai_assistant.html', {
        'ai_response': ai_response
    })



def vendor_logout_view(request):
    logout(request)
    return redirect('index')