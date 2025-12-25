from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(value, days):
    """Add specified number of days to a date"""
    try:
        if hasattr(value, 'date'):
            # If it's a datetime object, get the date part
            date_value = value.date()
        else:
            # If it's already a date object
            date_value = value
        
        new_date = date_value + timedelta(days=int(days))
        return new_date.strftime("%B %d")
    except (ValueError, AttributeError, TypeError):
        return value

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def currency(value):
    """Format a number as currency"""
    try:
        return f"₹{float(value):,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"

@register.filter
def percentage(value):
    """Format a decimal as percentage"""
    try:
        return f"{float(value) * 100:.1f}%"
    except (ValueError, TypeError):
        return "0.0%"
