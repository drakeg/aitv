from .models import SystemSettings


def operator_branding(request):
    settings = (
        SystemSettings.objects
        .filter(pk=1)
        .only('site_name', 'welcome_message')
        .first()
    )
    if settings is None:
        return {
            'site_brand_name': 'aitv',
            'site_welcome_message': '',
        }
    return {
        'site_brand_name': settings.site_name or 'aitv',
        'site_welcome_message': settings.welcome_message,
    }
