from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags

from datetime import datetime, date
import base64
from io import BytesIO
import qrcode
from xhtml2pdf import pisa
from barcode import Code128
from barcode.writer import ImageWriter

import google.generativeai as genai
from bs4 import BeautifulSoup
import re

from accounts.models import Hotel, HotelBooking, HotelUser

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

# ---------- Helpers ----------
def generate_pdf(template_src, context_dict):
    html = render_to_string(template_src, {**context_dict, 'for_pdf': True})
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

def generate_qr_code(booking, request):
    relative_url = reverse('booking_details', args=[booking.id])
    booking_url = request.build_absolute_uri(relative_url)
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(booking_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

def generate_barcode(booking):
    barcode_data = f"TKT-{booking.id + 1000}"
    barcode = Code128(barcode_data, writer=ImageWriter())
    buffer = BytesIO()
    barcode.write(buffer)
    return buffer.getvalue()

def strip_html_tags(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n").strip()

# ---------- Main Views ----------
@login_required(login_url='login_page')
def index(request):
    hotels = Hotel.objects.all()
    if request.GET.get('search'):
        hotels = hotels.filter(hotel_name__icontains=request.GET.get('search'))
    if request.GET.get('sort_by'):
        sort_by = request.GET.get('sort_by')
        if sort_by == "sort_low":
            hotels = hotels.order_by('hotel_offer_price')
        elif sort_by == "sort_high":
            hotels = hotels.order_by('-hotel_offer_price')
    hotels = hotels[:50]
    return render(request, 'home/index.html', {'hotels': hotels})

def index1(request):
    return render(request, 'home/index1.html')

def about(request):
    return render(request, 'home/about.html')

def contact(request):
    return render(request, 'home/contact.html')

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required(login_url='login_page')
def hotel_details(request, slug):
    hotel = get_object_or_404(Hotel, hotel_slug=slug)
    if request.method == "POST":
        start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d').date()
        days_count = (end_date - start_date).days

        if days_count <= 0:
            messages.warning(request, "Invalid booking dates.")
            return HttpResponseRedirect(request.path_info)

        total_price = hotel.hotel_offer_price * days_count
        booking_user = HotelUser.objects.get(pk=request.user.pk)

        booking = HotelBooking.objects.create(
            hotel=hotel,
            booking_user=booking_user,
            booking_start_date=start_date,
            booking_end_date=end_date,
            price=total_price,
            is_paid=False
        )
        return redirect('dummy_payment', booking_id=booking.id)
    return render(request, 'home/hotel_details.html', {'hotel': hotel})

@login_required(login_url='login_page')
def dummy_payment(request, booking_id):
    booking = get_object_or_404(HotelBooking, id=booking_id, booking_user=request.user)
    return render(request, 'home/dummy_payment.html', {'booking': booking})

@login_required(login_url='login_page')
def confirm_dummy_payment(request, booking_id):
    booking = get_object_or_404(HotelBooking, id=booking_id, booking_user=request.user)
    booking.is_paid = True
    booking.save()

    qr_code_data = generate_qr_code(booking, request)
    barcode_data = generate_barcode(booking)
    qr_code_base64 = base64.b64encode(qr_code_data).decode('utf-8')
    barcode_base64 = base64.b64encode(barcode_data).decode('utf-8')

    pdf_content = generate_pdf('home/ticket_template.html', {
        'booking': booking,
        'qr_code_base64': qr_code_base64,
        'barcode_base64': barcode_base64
    })

    email_html_content = render_to_string('home/ticket_template.html', {
        'booking': booking,
        'qr_code_base64': qr_code_base64,
        'barcode_base64': barcode_base64,
        'for_pdf': False
    })
    email_plain_text = strip_html_tags(email_html_content)

    subject = "Your VISTORA Booking Ticket"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = booking.booking_user.email
    email = EmailMessage(subject, email_plain_text, from_email, [to_email])
    email.content_subtype = "html"
    if pdf_content:
        email.attach('Vistora_Ticket.pdf', pdf_content, 'application/pdf')
    email.send(fail_silently=False)

    messages.success(request, "Payment successful! Your ticket PDF has been emailed.")
    return redirect('my_bookings')

@login_required(login_url='login_page')
def my_bookings(request):
    bookings = HotelBooking.objects.filter(booking_user=request.user)
    return render(request, 'accounts/my_bookings.html', {'bookings': bookings})

@login_required(login_url='login_page')
def booking_details(request, booking_id):
    booking = get_object_or_404(HotelBooking, id=booking_id, booking_user=request.user)
    return render(request, 'accounts/booking_details.html', {'booking': booking})

# ---------- Cancel & Delete Booking ----------
@login_required(login_url='login_page')
def cancel_booking(request, booking_id):
    booking = get_object_or_404(HotelBooking, id=booking_id, booking_user=request.user)
    if booking.booking_start_date > date.today():
        booking.delete()
        messages.success(request, "Booking cancelled successfully.")
    else:
        messages.warning(request, "You can only cancel future bookings.")
    return redirect('my_bookings')

@login_required(login_url='login_page')
def delete_booking(request, booking_id):
    try:
        booking = HotelBooking.objects.get(id=booking_id, booking_user=request.user)
        if booking.booking_end_date < date.today():
            booking.delete()
            messages.success(request, "Outdated booking deleted successfully.")
        else:
            messages.warning(request, "You can only delete past or outdated bookings.")
    except HotelBooking.DoesNotExist:
        messages.error(request, "Booking not found.")
    return redirect('my_bookings')

# ---------- AI Trip Planner ----------
@login_required(login_url='login_page')
def plan_trip(request):
    if request.method == "POST":
        destination = request.POST.get('destination', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        budget = request.POST.get('budget', '').strip()
        preferences = request.POST.get('preferences', '').strip()

        if not destination or not start_date or not end_date or not budget:
            messages.error(request, "All fields are required.")
            return render(request, 'home/plan_trip.html', request.POST)

        try:
            budget_value = float(budget)
            if budget_value <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Please enter a valid positive number for budget.")
            return render(request, 'home/plan_trip.html', request.POST)

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            if end_dt < start_dt:
                raise ValueError("End date before start date.")
            trip_days = (end_dt - start_dt).days + 1
        except Exception:
            messages.error(request, "Invalid dates. Please select a valid range.")
            return render(request, 'home/plan_trip.html', request.POST)

        # ✅ Fetch hotels without sorting
        hotels = Hotel.objects.filter(hotel_location__icontains=destination)[:5]

        day_sections = ""
        for i in range(1, trip_days + 1):
            day_sections += f"""
            <h2>Day {i}</h2>
            <ul>
                <li><strong>Morning:</strong> ...</li>
                <li><strong>Afternoon:</strong> ...</li>
                <li><strong>Evening:</strong> ...</li>
            </ul>
            """

        ai_prompt = f"""
        You are an expert travel planner. Design a personalized and engaging {trip_days}-day travel itinerary for a trip to {destination}, India, 
        from {start_date} to {end_date}, with a total budget of ₹{budget}.

        The traveler is interested in: {preferences or "a general mix of sightseeing, food, local culture, and relaxation"}.
        Respond in clean HTML only (no markdown or CSS). Use this structure:

        <h2>Overview</h2>
        <p>Summarize the trip in 2–3 lines.</p>

        {day_sections}

        <h2>Transport Tips</h2>
        <ul><li>2–3 helpful transport tips</li></ul>

        <h2>Budget Advice</h2>
        <ul><li>2–3 tips to manage the budget</li></ul>
        """

        ai_itinerary_html = "<p>Sorry, AI Trip Planner is currently unavailable. Please try again later.</p>"
        ai_itinerary_plaintext = "Sorry, AI Trip Planner is currently unavailable. Please try again later."

        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                ai_prompt,
                generation_config={"max_output_tokens": 1500 + (trip_days * 100)}
            )
            raw_response = response.text.strip()
            raw_response = re.sub(r'^```(html)?|```$', '', raw_response).strip()
            ai_itinerary_html = raw_response
            ai_itinerary_plaintext = strip_html_tags(raw_response)

        except Exception as e:
            print("⚠️ Gemini API Error:", e)
            messages.warning(request, "AI itinerary couldn't be generated. Showing fallback info.")

        return render(request, 'home/plan_trip_result.html', {
            'destination': destination,
            'start_date': start_date,
            'end_date': end_date,
            'budget': budget,
            'trip_days': trip_days,
            'hotels': hotels,
            'preferences': preferences,
            'ai_itinerary_html': ai_itinerary_html,
            'ai_itinerary_text': ai_itinerary_plaintext,
        })

    return render(request, 'home/plan_trip.html')


@login_required(login_url='login_page')
def download_trip_pdf(request):
    destination = request.GET.get('destination', 'Trip')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    budget = request.GET.get('budget', '')
    ai_itinerary_html = request.GET.get('ai_itinerary', '')

    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        trip_days = (end_dt - start_dt).days + 1
    except ValueError:
        trip_days = "N/A"

    context = {
        'destination': destination,
        'start_date': start_date,
        'end_date': end_date,
        'budget': budget,
        'trip_days': trip_days,
        'ai_itinerary_html': ai_itinerary_html
    }

    html = render_to_string('home/trip_pdf.html', {**context, 'for_pdf': True})
    buffer = BytesIO()
    pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=buffer)
    buffer.seek(0)
    filename = f"Vistora_Trip_{destination}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)
