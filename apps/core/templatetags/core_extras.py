from django import template

register = template.Library()

@register.filter
def format_period(value):
    """
    Converts YYYYMM string to MM/YYYY format.
    Example: 202511 -> 11/2025
    """
    if not value or len(str(value)) != 6:
        return value

    value_str = str(value)
    return f"{value_str[4:]}/{value_str[:4]}"
