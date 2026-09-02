from urllib.parse import parse_qs, urlparse

from django import forms

from .models import ContentItem

YOUTUBE_HOSTS = {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'}


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
    return candidate if len(candidate) == 11 else None


class ContentItemForm(forms.ModelForm):
    class Meta:
        model = ContentItem
        fields = ['title', 'url', 'genre']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Title'}),
            'url': forms.URLInput(attrs={'placeholder': 'Paste URL'}),
            'genre': forms.TextInput(attrs={'placeholder': 'Genre'}),
        }

    def save(self, commit=True):
        previous_source_type = self.instance.source_type if self.instance.pk else ''
        instance = super().save(commit=False)
        video_id = extract_youtube_video_id(instance.url)

        if video_id:
            instance.source_type = 'youtube'
            instance.thumbnail = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
        else:
            instance.source_type = 'movie'
            if previous_source_type == 'youtube':
                instance.thumbnail = None

        if commit:
            instance.save()
        return instance


class QuickAddForm(ContentItemForm):
    pass
