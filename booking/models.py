from django.db import models

class Player(models.Model):
    name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    year = models.CharField(max_length=10)
    division = models.CharField(max_length=10)

class Booking(models.Model):
    ground = models.CharField(max_length=100)
    game_type = models.CharField(max_length=100)
    date = models.DateField()
    time = models.TimeField()
    duration = models.IntegerField()
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending')
    players = models.ManyToManyField(Player)
