from django.shortcuts import render, redirect
from content.models import ContentItem
from content.forms import QuickAddForm
from content.services import fetch_trending_movies
from watchlist.models import Watchlist


def home(request):
    db_items = list(ContentItem.objects.all())

    # ✅ HANDLE QUICK ADD FORM
    if request.method == "POST" and request.user.is_authenticated:
        form = QuickAddForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/")  # refresh page
    else:
        form = QuickAddForm()

    # ✅ FETCH API MOVIES
    try:
        api_movies = fetch_trending_movies()
    except:
        api_movies = []

    # ✅ WATCHLIST
    watchlist_ids = []
    if request.user.is_authenticated:
        watchlist_ids = list(
            Watchlist.objects.filter(user=request.user)
            .values_list('content_id', flat=True)
        )

    context = {
        "form": form,  # 🔥 BACK IN CONTEXT
        "trending": api_movies[:10],
        "comedy": [x for x in db_items if "comedy" in x.genre.lower()],
        "action": [x for x in db_items if "action" in x.genre.lower()],
        "youtube": [x for x in db_items if x.source_type == "youtube"],
        "watchlist_ids": watchlist_ids,
    }

    return render(request, "home.html", context)