from django.urls import path
from accounts import views

urlpatterns = [
    path('login/' , views.login_page, name='login_page'),
    path('register/' , views.register, name='register'),
    path('send_otp/<email>/' , views.send_otp, name='send_otp'),
    path('verify-otp/<email>/' , views.verify_otp, name='verify_otp'),
    path('login-vendor/' , views.login_vendor, name='login_vendor'),
    path('register-vendor/' , views.register_vendor, name='register_vendor'),
    path('about',views.about,name="aboutus"),
    path('contact',views.contact,name="contactus"),
    path('verify-account/<token>/', views.verify_email_token, name="verify_email_token"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('send_vendor_otp/<email>/', views.send_vendor_otp, name='send_vendor_otp'),
    path('verify-vendor-otp/<email>/', views.verify_vendor_otp, name='verify_vendor_otp'),
    path('add-hotel/', views.add_hotel, name="add_hotel"),
    path('upload-images/<slug:slug>/', views.upload_images, name='upload_images'),
    path('delete_image/<id>/' , views.delete_image , name="delete_image"),
    path('edit-hotel/<slug>/', views.edit_hotel, name="edit_hotel"),
    path('vendor_logout/', views.vendor_logout_view, name="vendor_logout_view"),
    path('delete-hotel/<slug:slug>/', views.delete_hotel, name='delete_hotel'),
    path('ai-assistant/', views.vendor_ai_assistant, name='vendor_ai_assistant'),
]

