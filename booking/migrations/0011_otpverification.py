# Generated migration for OTPVerification model

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0010_booking_idx_sport_date_slot_status_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OTPVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('otp', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_verified', models.BooleanField(default=False)),
                ('full_name', models.CharField(max_length=100)),
                ('roll_number', models.CharField(max_length=20)),
                ('branch', models.CharField(max_length=50)),
                ('year', models.CharField(max_length=20)),
                ('division', models.CharField(max_length=10)),
                ('password', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
