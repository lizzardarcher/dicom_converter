
def admin_soft_context(request):
    path_parts = request.path.strip('/').split('/')
    segment = path_parts[-1] if path_parts else ''

    direction = {
        'panel': 'text-left',
        'notify': 'right',
        'float': 'float-right',
        'reverse_panel': 'text-right',
        'nav': 'ml-auto',
    }

    from django.utils.translation import get_language_bidi
    if get_language_bidi():
        direction['panel'] = 'text-right'
        direction['notify'] = 'left'
        direction['float'] = ''
        direction['reverse_panel'] = 'text-left'
        direction['nav'] = 'mr-auto'

    return {
        'segment': segment,
        'direction': direction,
    }
