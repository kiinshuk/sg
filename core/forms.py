from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Post, Comment


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input'})
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last name'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Password'})


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)

    class Meta:
        model = Profile
        fields = ('profile_pic', 'bio')
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Write your bio...'}),
            'profile_pic': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'class': 'form-input', 'placeholder': 'First name'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Last name'})


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('image', 'video', 'caption')
        widgets = {
            'caption': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Write a caption...'}),
            'image': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*', 'id': 'imageInput'}),
            'video': forms.FileInput(attrs={'class': 'form-input', 'accept': 'video/*', 'id': 'videoInput'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.TextInput(attrs={'class': 'comment-input', 'placeholder': 'Add a comment...'}),
        }
