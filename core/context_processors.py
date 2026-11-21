from .system_settings import get_system_settings


def operator_branding(request):
    settings = get_system_settings(request)
    if settings is None:
        return {
            'site_brand_name': 'aitv',
            'site_welcome_message': '',
            'site_show_guest_account_links': True,
        }
    return {
        'site_brand_name': settings.site_name or 'aitv',
        'site_welcome_message': settings.welcome_message,
        'site_show_guest_account_links': settings.show_guest_account_links,
    }
