from django.db import models

class Player(models.Model):
    name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    year = models.CharField(max_length=10)
    division = models.CharField(max_length=10)

class Booking(models.Model):
    student_name = models.CharField(max_length=100)
    student_email = models.EmailField(blank=True, null=True)
    roll_number = models.CharField(max_length=20, unique=True)
    ground = models.CharField(max_length=100)
    date = models.DateField()
    time_slot = models.CharField(max_length=50)
    purpose = models.TextField()
    number_of_players = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student_name} - {self.ground} - {self.date}"
