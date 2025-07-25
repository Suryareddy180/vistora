# Generated by Django 5.2.3 on 2025-06-16 15:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_rename_ameneties_hotel_amenities'),
    ]

    operations = [
        migrations.CreateModel(
            name='HotelBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('booking_start_date', models.DateField()),
                ('booking_end_date', models.DateField()),
                ('price', models.FloatField()),
                ('booking_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.hoteluser')),
                ('hotel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='accounts.hotel')),
            ],
        ),
    ]
