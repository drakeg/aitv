from .models import SystemSettings

_REQUEST_CACHE_ATTR = '_aitv_system_settings'
_UNSET = object()


def get_system_settings(request):
    cached = getattr(request, _REQUEST_CACHE_ATTR, _UNSET)
    if cached is not _UNSET:
        return cached

    settings = (
        SystemSettings.objects
        .filter(pk=1)
        .only('site_name', 'welcome_message', 'default_region')
        .first()
    )
    setattr(request, _REQUEST_CACHE_ATTR, settings)
    return settings


def get_operator_region(request):
    settings = get_system_settings(request)
    return settings.default_region if settings is not None else 'US'
