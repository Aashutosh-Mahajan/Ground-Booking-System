from django.db import models
from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta
import random


class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    student_name = models.CharField(max_length=100)
    student_email = models.EmailField()
    student_branch = models.CharField(max_length=50, blank=True, null=True)  # new
    student_year = models.CharField(max_length=20, blank=True, null=True)    # new
    student_division = models.CharField(max_length=10, blank=True, null=True) # new
    roll_number = models.CharField(max_length=20, blank=True, null=True)

    ground = models.CharField(max_length=100)
    # Selected sport for this booking (e.g., Football, Basketball, etc.)
    sport = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField()
    time_slot = models.CharField(max_length=50)
    purpose = models.TextField()
    equipment = models.TextField(blank=True, null=True)  
    number_of_players = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.ground} - {self.date}"

    class Meta:
        indexes = [
            # Index to speed up FCFS/auto-reject lookups by sport/date/slot/status
            models.Index(fields=["date", "sport", "time_slot", "status"], name="idx_sport_date_slot_status"),
            models.Index(fields=["created_at"], name="idx_created_at"),
        ]
        constraints = [
            # Ensure only one Approved booking exists for a given (date, sport, time_slot)
            models.UniqueConstraint(
                fields=["date", "sport", "time_slot"],
                condition=Q(status="Approved"),
                name="uniq_approved_sport_slot"
            )
        ]

class Player(models.Model):
    BRANCH_CHOICES = [
        ('CSE', 'Computer Science & Engineering'),
        ('IT', 'Information Technology'),
        ('EXCS', 'Electronics & Computer Science'),
        ('EXTC', 'Electronics & Telecommunication'),
        ('BIOM', 'Biomedical Engineering'),
    ]

    YEAR_CHOICES = [
        ('FE', 'First Year'),
        ('SE', 'Second Year'),
        ('TE', 'Third Year'),
        ('BE', 'Final Year'),
    ]

    DIVISION_CHOICES = [
        ('A', 'Division A'),
        ('B', 'Division B'),
        ('C', 'Division C'),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="players"
    )

    name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50, choices=BRANCH_CHOICES)
    year = models.CharField(max_length=10, choices=YEAR_CHOICES)
    division = models.CharField(max_length=10, choices=DIVISION_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.branch} - {self.year}{self.division})"


class AdminUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)  # store hashed password

    def __str__(self):
        return self.username


class StudentUser(models.Model):
    full_name = models.CharField(max_length=500, null=True, blank=True)     # encrypted
    email = models.CharField(max_length=500, unique=True, null=True, blank=True)  # encrypted
    roll_number = models.CharField(max_length=500, null=True, blank=True)   # encrypted
    branch = models.CharField(max_length=50, null=True, blank=True)
    year = models.CharField(max_length=20, null=True, blank=True)
    division = models.CharField(max_length=10, null=True, blank=True)
    password = models.CharField(max_length=500, null=True, blank=True)      # encrypted

    def __str__(self):
        return self.email


class AllotedGroundBooking(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="alloted_bookings",
        null=True,  # ✅ allow empty
        blank=True  # ✅ allow empty in forms
    )
    date = models.DateField()
    ground = models.CharField(max_length=100)  
    time_slot = models.CharField(max_length=50)  
    allotted_to = models.CharField(max_length=100)  
    roll_number = models.CharField(max_length=20)
    purpose = models.TextField(blank=True, null=True)
    players = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.date} | {self.ground} | {self.time_slot}"


class OTPVerification(models.Model):
    email = models.CharField(max_length=500)          # encrypted
    otp = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    
    # Temporary storage of signup data (encrypted fields)
    full_name = models.CharField(max_length=500)      # encrypted
    roll_number = models.CharField(max_length=500)    # encrypted
    branch = models.CharField(max_length=50)
    year = models.CharField(max_length=20)
    division = models.CharField(max_length=10)
    password = models.CharField(max_length=500)       # encrypted
    
    def __str__(self):
        return f"{self.email} - {self.otp}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))
    
    class Meta:
        ordering = ['-created_at']

