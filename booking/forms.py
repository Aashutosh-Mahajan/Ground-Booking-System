from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Booking, Player


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'student_name',
            'student_email',
            'roll_number',
            'ground',
            'date',
            'time_slot',
            'purpose',
            'number_of_players'
        ]
        widgets = {
            'student_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your full name'
            }),
            'student_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your email'
            }),
            'roll_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your roll number'
            }),
            'ground': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'time_slot': forms.Select(attrs={'class': 'form-select'}),
            'purpose': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Describe the purpose of your booking'
            }),
            'number_of_players': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ground choices
        self.fields['ground'].choices = [
            ('', 'Select a ground'),
            ('Ground A', 'Ground A'),
            ('Ground B', 'Ground B'),
            ('Ground C', 'Ground C'),
        ]

        # Time slot choices
        self.fields['time_slot'].choices = [
            ('', 'Select time slot'),
            ('9:00-11:00', '9:00 AM - 11:00 AM'),
            ('11:00-13:00', '11:00 AM - 1:00 PM'),
            ('13:00-15:00', '1:00 PM - 3:00 PM'),
            ('15:00-17:00', '3:00 PM - 5:00 PM'),
            ('17:00-19:00', '5:00 PM - 7:00 PM'),
        ]

        # Number of players choices
        self.fields['number_of_players'].choices = [
            ('', 'Select number of players')
        ] + [(i, str(i)) for i in range(1, 12)]
        self.fields['number_of_players'].initial = 1


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name', 'branch', 'year', 'division']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter player name'
            }),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.Select(attrs={'class': 'form-select'}),
            'division': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['branch'].choices = [
            ('', 'Select Branch'),
            ('CSE', 'Computer Science & Engineering'),
            ('IT', 'Information Technology'),
            ('EXCS', 'Electronics & Computer Science'),
            ('EXTC', 'Electronics & Telecommunication'),
            ('BIOM', 'Biomedical Engineering'),
        ]

        self.fields['year'].choices = [
            ('', 'Select Year'),
            ('FE', 'First Year (FE)'),
            ('SE', 'Second Year (SE)'),
            ('TE', 'Third Year (TE)'),
            ('BE', 'Final Year (BE)'),
        ]

        self.fields['division'].choices = [
            ('', 'Select Division'),
            ('A', 'Division A'),
            ('B', 'Division B'),
            ('C', 'Division C'),
        ]


# Custom formset that adjusts number of forms dynamically
class BasePlayerFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            num_players = self.instance.number_of_players or 1
            self.extra = num_players - self.total_form_count()
            if self.extra < 0:
                self.extra = 0

