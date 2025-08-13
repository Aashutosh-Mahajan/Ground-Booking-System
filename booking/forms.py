from django import forms
from django.forms import formset_factory

class BookingForm(forms.Form):
    number_of_players = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 12)],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-3 border border-blue-600 rounded-lg focus:outline-none'
        })
    )

class PlayerForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg',
        'placeholder': 'Enter player name'
    }))
    branch = forms.ChoiceField(choices=[
        ('', 'Select Branch'), ('CSE', 'CSE'), ('IT', 'IT'), ('ECE', 'ECE'), ('ME', 'ME')
    ], widget=forms.Select(attrs={
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'
    }))
    year = forms.ChoiceField(choices=[
        ('', 'Select Year'), ('FE', 'First Year'), ('SE', 'Second Year'),
        ('TE', 'Third Year'), ('BE', 'Final Year')
    ], widget=forms.Select(attrs={
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'
    }))
    division = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg',
        'placeholder': 'Enter division'
    }))

# Create formset
PlayerFormSet = formset_factory(PlayerForm, extra=0)
