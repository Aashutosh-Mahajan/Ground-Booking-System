from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Booking, Player, StudentUser
from django.core.exceptions import ValidationError


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
            'equipment',
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
                'placeholder': 'Enter your email address'
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
            'equipment': forms.Textarea(attrs={'class': 'form-input', 'readonly': 'readonly', 'rows': 3}),
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


class StudentSignupForm(forms.Form):
    BRANCH_CHOICES = [
        ('', 'Select Branch'),
        ('CSE', 'Computer Science & Engineering'),
        ('IT', 'Information Technology'),
        ('EXCS', 'Electronics & Computer Science'),
        ('EXTC', 'Electronics & Telecommunication'),
        ('BIOM', 'Biomedical Engineering'),
    ]

    YEAR_CHOICES = [
        ('', 'Select Year'),
        ('FE', 'First Year (FE)'),
        ('SE', 'Second Year (SE)'),
        ('TE', 'Third Year (TE)'),
        ('BE', 'Final Year (BE)'),
    ]

    DIVISION_CHOICES = [
        ('', 'Select Division'),
        ('A', 'Division A'),
        ('B', 'Division B'),
        ('C', 'Division C'),
    ]

    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your full name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your college email'
        })
    )
    
    roll_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your roll number'
        })
    )
    
    branch = forms.ChoiceField(
        choices=BRANCH_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200'
        })
    )
    
    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200'
        })
    )
    
    division = forms.ChoiceField(
        choices=DIVISION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter password'
        })
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
            'placeholder': 'Confirm password'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if StudentUser.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError('Passwords do not match.')
        
        return cleaned_data


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200 text-center text-2xl tracking-widest',
            'placeholder': '000000',
            'maxlength': '6',
            'autocomplete': 'off'
        })
    )


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your registered email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not StudentUser.objects.filter(email=email).exists():
            raise ValidationError('No account found with this email address.')
        return email


class ResetPasswordForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200 text-center text-2xl tracking-widest',
            'placeholder': '000000',
            'maxlength': '6',
            'autocomplete': 'off'
        })
    )
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter new password'
        })
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
            'placeholder': 'Confirm new password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('Passwords do not match.')
        
        return cleaned_data

