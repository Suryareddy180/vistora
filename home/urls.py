from django.urls import path
from home import views

urlpatterns = [
    path('' , views.index1 , name="index"),
    path('index',views.index,name="index_main"),
    path('about',views.about,name="about"),
    path('contact',views.contact,name="contact"),
    path('logout/', views.logout_view, name="logout_view"),
    path('hotel-details/<slug>/', views.hotel_details, name="hotel_details"),
    path('dummy-payment/<int:booking_id>/', views.dummy_payment, name='dummy_payment'),
    path('confirm-dummy-payment/<int:booking_id>/', views.confirm_dummy_payment, name='confirm_dummy_payment'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('delete-booking/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking-details/<int:booking_id>/', views.booking_details, name='booking_details'),
    path('plan-trip/', views.plan_trip, name='plan_trip'),
    path('download-trip-pdf/', views.download_trip_pdf, name='download_trip_pdf'),

]