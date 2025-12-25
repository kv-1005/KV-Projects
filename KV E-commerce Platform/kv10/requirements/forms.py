from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, Category, Customer, Review, Coupon
from .models import Address

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'sale_price': forms.NumberInput(attrs={'step': '0.01'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

class CustomerProfileForm(forms.ModelForm):
    # Extra fields mapped to django.contrib.auth.models.User
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = Customer
        fields = [
            'phone', 'address', 'city', 'state', 'zip_code', 'country',
            'profile_picture', 'date_of_birth'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize extra fields from the related User
        if self.instance and getattr(self.instance, 'user_id', None):
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
        # Allow current user's email but prevent duplicates across users
        existing = User.objects.filter(email=email)
        if self.instance and getattr(self.instance, 'user_id', None):
            existing = existing.exclude(pk=self.instance.user.pk)
        if existing.exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def save(self, commit=True):
        customer: Customer = super().save(commit=False)
        # Update related User fields
        if customer and getattr(customer, 'user_id', None):
            user = customer.user
            user.first_name = self.cleaned_data.get('first_name', user.first_name)
            user.last_name = self.cleaned_data.get('last_name', user.last_name)
            email = self.cleaned_data.get('email')
            if email:
                user.email = email
            if commit:
                user.save()
        if commit:
            customer.save()
        return customer

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['label', 'first_name', 'last_name', 'phone', 'address', 'city', 'state', 'zip_code', 'country', 'is_default_shipping', 'is_default_billing']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.CharField(max_length=100, required=False)
    zip_code = forms.CharField(max_length=10, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create customer profile
            Customer.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', ''),
                address=self.cleaned_data.get('address', ''),
                city=self.cleaned_data.get('city', ''),
                state=self.cleaned_data.get('state', ''),
                zip_code=self.cleaned_data.get('zip_code', ''),
            )
        return user

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise forms.ValidationError('Rating must be between 1 and 5.')
        return rating

class CouponForm(forms.Form):
    code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Enter coupon code'}))

class CheckoutForm(forms.Form):
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('razorpay', 'Razorpay'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Digital Wallet'),
    ]

    # Shipping Information
    shipping_first_name = forms.CharField(max_length=50)
    shipping_last_name = forms.CharField(max_length=50)
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    shipping_city = forms.CharField(max_length=100)
    shipping_state = forms.CharField(max_length=100)
    shipping_zip_code = forms.CharField(max_length=10)
    shipping_country = forms.CharField(max_length=100, initial='India')
    shipping_phone = forms.CharField(max_length=15)

    # Billing Information
    billing_same_as_shipping = forms.BooleanField(required=False, initial=True)
    billing_first_name = forms.CharField(max_length=50, required=False)
    billing_last_name = forms.CharField(max_length=50, required=False)
    billing_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    billing_city = forms.CharField(max_length=100, required=False)
    billing_state = forms.CharField(max_length=100, required=False)
    billing_zip_code = forms.CharField(max_length=10, required=False)

    # Payment Information
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, widget=forms.RadioSelect)
    upi_id = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'yourname@upi'})
    )

    # Additional Information
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        # Validate UPI details when UPI is selected
        if payment_method == 'upi':
            upi_id = cleaned_data.get('upi_id', '').strip()
            if not upi_id:
                raise forms.ValidationError('UPI ID is required for UPI payment')
            import re
            upi_pattern = re.compile(r'^[\w\.-]{2,256}@[\w]{2,64}$')
            if not upi_pattern.match(upi_id):
                raise forms.ValidationError('Enter a valid UPI ID (e.g., name@bank)')

        # Validate billing information if not same as shipping
        if not cleaned_data.get('billing_same_as_shipping'):
            if not cleaned_data.get('billing_first_name'):
                raise forms.ValidationError("Billing first name is required")
            if not cleaned_data.get('billing_last_name'):
                raise forms.ValidationError("Billing last name is required")
            if not cleaned_data.get('billing_address'):
                raise forms.ValidationError("Billing address is required")
            if not cleaned_data.get('billing_city'):
                raise forms.ValidationError("Billing city is required")
            if not cleaned_data.get('billing_state'):
                raise forms.ValidationError("Billing state is required")
            if not cleaned_data.get('billing_zip_code'):
                raise forms.ValidationError("Billing zip code is required")

        return cleaned_data

class ProductSearchForm(forms.Form):
    SORT_CHOICES = [
        ('name', 'Name A-Z'),
        ('-name', 'Name Z-A'),
        ('price', 'Price Low to High'),
        ('-price', 'Price High to Low'),
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
    ]

    query = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search products...'}))
    category = forms.ModelChoiceField(queryset=Category.objects.filter(is_active=True), required=False, empty_label="All Categories")
    min_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'Min Price'}))
    max_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'Max Price'}))
    sort_by = forms.ChoiceField(choices=SORT_CHOICES, required=False, initial='-created_at')
    in_stock_only = forms.BooleanField(required=False, initial=False)

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError("Minimum price cannot be greater than maximum price")
        
        return cleaned_data

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name.strip()) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long")
        return name.strip()

class NewsletterForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address'}))
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email 
