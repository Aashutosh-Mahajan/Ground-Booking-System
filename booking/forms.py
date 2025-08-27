from django import forms
from django.forms import formset_factory
from .models import Booking, Player

class BookingForm(forms.ModelForm):
    # Add non-model fields so no database is required
    student_branch = forms.ChoiceField(
        choices=[('', 'Select Branch'), ('CSE', 'CSE'), ('IT', 'IT'), ('EXCS', 'EXCS'), ('EXTC', 'EXTC'), ('BIOM', 'BIOM')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    student_year = forms.ChoiceField(
        choices=[('', 'Select Year'), ('FE', 'FE'), ('SE', 'SE'), ('TE', 'TE'), ('BE', 'BE')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    student_division = forms.ChoiceField(
        choices=[('', 'Select Division'), ('A', 'A'), ('B', 'B'), ('C', 'C')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Booking
        fields = ['student_name', 'roll_number', 'ground', 'date', 'time_slot', 'purpose', 'number_of_players']
        widgets = {
            'student_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter your full name'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter your roll number'}),
            'ground': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'time_slot': forms.Select(attrs={'class': 'form-select'}),
            'purpose': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Describe the purpose of your booking'}),
            'number_of_players': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ground'].choices = [
            ('', 'Select a ground'),
            ('Ground A', 'Ground A'),
            ('Ground B', 'Ground B')
        ]
        self.fields['time_slot'].choices = [
            ('', 'Select time slot'),
            ('9.00 - 11.00', '9.00 - 11.00'),
            ('11.00 - 13.00', '11.00 - 13.00'),
            ('13.00 - 15.00', '13.00 - 15.00'),
            ('15.00 - 17.00', '15.00 - 17.00'),
            ('17.00 - 19.00', '17.00 - 19.00')
        ]
        self.fields['number_of_players'].choices = [(i, str(i)) for i in range(1, 12)]
        # Ensure at least one player form is shown by default
        self.fields['number_of_players'].initial = 1
        # choices already set at field declaration for non-model fields

class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name', 'branch', 'year', 'division']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter player name'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.Select(attrs={'class': 'form-select'}),
            'division': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['branch'].choices = [
            ('', 'Select Branch'),
            ('CSE', 'CSE'),
            ('IT', 'IT'),
            ('EXCS', 'EXCS'),
            ('EXTC', 'EXTC'),
            ('BIOM', 'BIOM')
        ]
        self.fields['year'].choices = [
            ('', 'Select Year'),
            ('FE', 'FE'),
            ('SE', 'SE'),
            ('TE', 'TE'),
            ('BE', 'BE')
        ]
        self.fields['division'].choices = [
            ('', 'Select Division'),
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C')
        ]

# Create formset
PlayerFormSet = formset_factory(PlayerForm, extra=0)
