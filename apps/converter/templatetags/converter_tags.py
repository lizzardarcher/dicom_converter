from django import template

register = template.Library()


@register.simple_tag
def user_initials(user):
    if user.first_name and user.last_name:
        return f'{user.first_name[0]}{user.last_name[0]}'.upper()
    if user.first_name:
        return user.first_name[:2].upper()
    return user.username[:2].upper()

