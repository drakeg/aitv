import re
from urllib.parse import parse_qs, urlparse

from django import forms

from .models import ContentAvailability, ContentItem
from .providers import detect_provider, ensure_direct_availability

YOUTUBE_HOSTS = {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'}
YOUTUBE_ID_RE = re.compile(r'^[A-Za-z0-9_-]{11}$')


def extract_youtube_video_id(url):
    """Return a YouTube video ID for supported canonical URL shapes."""
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower()
    if host not in YOUTUBE_HOSTS:
        return None

    if host == 'youtu.be':
        candidate = parsed.path.strip('/').split('/', 1)[0]
    elif parsed.path == '/watch':
        candidate = parse_qs(parsed.query).get('v', [''])[0]
    else:
        parts = [part for part in parsed.path.split('/') if part]
        candidate = parts[1] if len(parts) >= 2 and parts[0] in {'shorts', 'embed'} else ''

    candidate = candidate.strip()
    return candidate if YOUTUBE_ID_RE.fullmatch(candidate) else None


class ContentItemForm(forms.ModelForm):
    class Meta:
        model = ContentItem
        fields = ['title', 'url', 'genre', 'content_type']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Title'}),
            'url': forms.URLInput(attrs={'placeholder': 'Paste direct watch/source URL'}),
            'genre': forms.TextInput(attrs={'placeholder': 'Genre'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_url = self.instance.url if self.instance.pk else ''
        self._original_source_type = self.instance.source_type if self.instance.pk else ''

    def clean_title(self):
        return self.cleaned_data['title'].strip()

    def clean_genre(self):
        return self.cleaned_data['genre'].strip()

    def save(self, commit=True):
        instance = super().save(commit=False)
        video_id = extract_youtube_video_id(instance.url)
        provider = detect_provider(instance.url)

        if video_id:
            instance.source_type = 'youtube'
            instance.content_type = ContentItem.ContentType.VIDEO
            instance.thumbnail = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
        elif provider:
            instance.source_type = provider['source_type']
            if self._original_source_type == 'youtube':
                instance.thumbnail = None
        elif not instance.external_source:
            instance.source_type = 'manual'
            if self._original_source_type == 'youtube':
                instance.thumbnail = None

        if commit:
            instance.save()
            if self._original_url and self._original_url != instance.url:
                ContentAvailability.objects.filter(
                    content=instance,
                    url=self._original_url,
                ).delete()
            ensure_direct_availability(instance)
        return instance


class QuickAddForm(ContentItemForm):
    pass
