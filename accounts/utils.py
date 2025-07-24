import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont
import os
from accounts.models import *


def generateRandomToken():
    return str(uuid.uuid4())


def sendEmailToken(email, token):
    subject = "Verify Your Email Address"
    message = f"""Hi Please verify you email account by clicking this link 
    http://127.0.0.1:8000/account/verify-account/{token}

    """
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )




def sendOTPtoEmail(email, otp):
    subject = "OTP for Account Login"
    message = f"""Hi, use this OTP to login
     {otp} 

    """
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )


def generateSlug(hotel_name):
    slug = f"{slugify(hotel_name)}-" + str(uuid.uuid4()).split('-')[0]
    if Hotel.objects.filter(hotel_slug = slug).exists():
        return generateSlug(hotel_name)
    return slug



def generate_ai_ticket(booking):
    # Create a blank white image
    img = Image.new('RGB', (600, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Load a font (adjust path as needed)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Linux
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\Arial.ttf"  # Windows fallback

    font = ImageFont.truetype(font_path, 20)

    # Draw text
    draw.text((20, 30), f"Hotel Booking Ticket", font=font, fill=(0, 0, 0))
    draw.text((20, 80), f"Name: {booking.booking_user.first_name} {booking.booking_user.last_name}", font=font, fill=(0, 0, 0))
    draw.text((20, 120), f"Hotel: {booking.hotel.hotel_name}", font=font, fill=(0, 0, 0))
    draw.text((20, 160), f"Check-in: {booking.booking_start_date}", font=font, fill=(0, 0, 0))
    draw.text((20, 200), f"Check-out: {booking.booking_end_date}", font=font, fill=(0, 0, 0))
    draw.text((20, 240), f"Amount Paid: ₹{booking.price}", font=font, fill=(0, 0, 0))
    draw.text((20, 280), "Status: CONFIRMED", font=font, fill=(34, 139, 34))

    # Save to media folder
    ticket_path = f"media/tickets/ticket_{booking.id}.png"
    os.makedirs(os.path.dirname(ticket_path), exist_ok=True)
    img.save(ticket_path)

    # Save path to booking (optional)
    booking.ticket_image = f"tickets/ticket_{booking.id}.png"
    booking.save()
