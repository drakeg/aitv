from django import forms
from .models import ContentItem

class QuickAddForm(forms.ModelForm):
    class Meta:
        model = ContentItem
        fields = ['title', 'url', 'genre']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Title'}),
            'url': forms.TextInput(attrs={'placeholder': 'Paste URL'}),
            'genre': forms.TextInput(attrs={'placeholder': 'Genre'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Detect YouTube
        if "youtube.com" in instance.url or "youtu.be" in instance.url:
            instance.source_type = "youtube"
            # Extract video ID
            if "watch?v=" in instance.url:
                video_id = instance.url.split("watch?v=")[-1]
            elif "youtu.be/" in instance.url:
                video_id = instance.url.split("youtu.be/")[-1]
            else:
                video_id = ""
            # Set thumbnail
            if video_id:
                instance.thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        else:
            instance.source_type = "movie"
        if commit:
            instance.save()
        return instance
