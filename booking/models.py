from django.db import models
from django.contrib.auth.hashers import make_password, check_password


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
    date = models.DateField()
    time_slot = models.CharField(max_length=50)
    purpose = models.TextField()
    number_of_players = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.ground} - {self.date}"

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
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # store hashed password

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

