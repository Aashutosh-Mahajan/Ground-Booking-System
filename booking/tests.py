from django.test import TestCase, Client
from django.urls import reverse
from .models import Booking
from datetime import date


class StudentHistoryViewTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.email = 'student@example.com'
		# Create some bookings
		Booking.objects.create(
			student_name='Test Student',
			student_email=self.email,
			ground='Ground A',
			sport='Football',
			date=date.today(),
			time_slot='07:00 AM - 09:00 AM',
			purpose='Practice',
			number_of_players=5,
			status='Approved'
		)
		Booking.objects.create(
			student_name='Test Student',
			student_email=self.email,
			ground='Ground B',
			sport='Cricket',
			date=date.today(),
			time_slot='04:00 PM - 06:00 PM',
			purpose='Match',
			number_of_players=7,
			status='Rejected'
		)

	def test_history_requires_login(self):
		resp = self.client.get(reverse('student_history'))
		self.assertEqual(resp.status_code, 302)  # redirected to login

	def test_history_lists_bookings(self):
		# Simulate login via session
		session = self.client.session
		session['student_email'] = self.email
		session.save()

		resp = self.client.get(reverse('student_history'))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'My Booking History')
		self.assertContains(resp, 'Ground A')
		self.assertContains(resp, 'Ground B')

	def test_history_status_filter(self):
		session = self.client.session
		session['student_email'] = self.email
		session.save()

		resp = self.client.get(reverse('student_history') + '?status=Approved')
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'Approved')
		self.assertNotContains(resp, 'Rejected')
