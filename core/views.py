def live_tv_channel_schedule(request, channel_id):
    region = 'US'
    preferred_providers = []
    if request.user.is_authenticated:
        preference, _ = DiscoveryPreference.objects.get_or_create(user=request.user)
        region = preference.region
        preferred_providers = preference.preferred_providers

    channel = get_object_or_404(Channel, pk=channel_id, region=region)
    is_favorite = (
        request.user.is_authenticated
        and ChannelFavorite.objects.filter(user=request.user, channel=channel).exists()
    )
    guide_path = reverse('live_tv_guide')
    return_to = request.GET.get('return_to', '').strip()
    if not (
        return_to.startswith(guide_path)
        and url_has_allowed_host_and_scheme(
            return_to,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    ):
        return_to = guide_path

    now = timezone.now()
    today = timezone.localdate()

    try:
        horizon_days = int(os.getenv('EPG_DAYS', '2'))
    except ValueError:
        horizon_days = 2
    if horizon_days < 1 or horizon_days > 7:
        horizon_days = 2

    schedule_days = []
    for offset in range(horizon_days):
        schedule_date = today + timezone.timedelta(days=offset)
        if offset == 0:
            label = 'Today'
        elif offset == 1:
            label = 'Tomorrow'
        else:
            label = f'{schedule_date:%b} {schedule_date.day}'
        schedule_days.append({'date': schedule_date, 'label': label})

    schedule_day_counts = {}
    for schedule_date in (
        Airing.objects
        .filter(
            channel=channel,
            source_schedule_date__in=[item['date'] for item in schedule_days],
        )
        .values_list('source_schedule_date', flat=True)
    ):
        schedule_day_counts[schedule_date] = schedule_day_counts.get(schedule_date, 0) + 1
    for item in schedule_days:
        item['airing_count'] = schedule_day_counts.get(item['date'], 0)

    selected_date = today
    requested_date = request.GET.get('date', '').strip()
    if requested_date:
        try:
            candidate = date.fromisoformat(requested_date)
        except ValueError:
            candidate = None
        allowed_dates = {item['date'] for item in schedule_days}
        if candidate in allowed_dates:
            selected_date = candidate

    airings = list(
        Airing.objects
        .filter(
            channel=channel,
            source_schedule_date=selected_date,
        )
        .select_related('program')
        .order_by('starts_at')
    )
    selected_day_airing_count = len(airings)

    # Detect if the selected day is empty and find nearest populated dates for navigation
    is_empty_day = selected_day_airing_count == 0
    nearest_populated_dates = None
    if is_empty_day:
        # Find all populated dates within the EPG horizon
        populated_dates = [
            (date, count) for date, count in schedule_day_counts.items()
            if count > 0
        ]
        if populated_dates:
            # Sort by date to find nearest earlier and later populated dates
            populated_dates.sort(key=lambda x: x[0])
            selected_date_obj = selected_date
            # Find nearest earlier populated date (within horizon)
            nearest_earlier = None
            for date, _ in populated_dates:
                if date < selected_date_obj:
                    nearest_earlier = date
                else:
                    break
            # Find nearest later populated date (within horizon)
            nearest_later = None
            for date, _ in populated_dates:
                if date > selected_date_obj:
                    nearest_later = date
                else:
                    continue
            # Build list of navigation targets with their distance from selected day
            nav_targets = []
            for date, count in populated_dates:
                delta_days = (date - selected_date_obj).days
                nav_targets.append({
                    'date': date,
                    'count': count,
                    'delta_days': delta_days,
                    'is_earlier': date < selected_date_obj,
                    'is_later': date > selected_date_obj,
                })
            # Sort by absolute distance from selected day (nearest first)
            nav_targets.sort(key=lambda x: abs(x['delta_days']))
            nearest_populated_dates = nav_targets[:2]  # Keep at most earlier and later

    current_airing = next(
        (
            airing for airing in airings
            if airing.starts_at <= now < airing.ends_at
        ),
        None,
    )
    next_airing = next(
        (airing for airing in airings if airing.starts_at > now),
        None,
    )
    next_starts_in_minutes = None
    if next_airing is not None and next_airing.starts_at <= now + timezone.timedelta(hours=1):
        seconds_until_start = max(0, (next_airing.starts_at - now).total_seconds())
        next_starts_in_minutes = max(1, int((seconds_until_start + 59) // 60))

    current_destination = None
    current_destination_scope = ''
    current_ends_in_minutes = None
    if current_airing is not None:
        seconds_until_end = max(0, (current_airing.ends_at - now).total_seconds())
        current_ends_in_minutes = max(1, int((seconds_until_end + 59) // 60))
        channel_destinations = _rank_channel_destinations(
            list(
                ChannelDestination.objects.filter(
                    channel=channel,
                    destination_type__in=[
                        ChannelDestination.DestinationType.DIRECT,
                        ChannelDestination.DestinationType.TUNER,
                    ],
                )
            ),
            preferred_providers,
        )
        current_destination, current_destination_scope = _select_current_destination(
            airing=current_airing,
            channel_destination=channel_destinations[0] if channel_destinations else None,
            airing_destinations=AiringDestination.objects.filter(airing=current_airing),
            preferred_providers=preferred_providers,
        )

    health_context = epg_health_context(region, now=now)

    return render(request, 'live_tv/channel_schedule.html', {
        'channel': channel,
        'airings': airings,
        'schedule_now': now,
        'schedule_days': schedule_days,
        'schedule_selected_date': selected_date,
        'schedule_selected_day_airing_count': selected_day_airing_count,
        'schedule_return_path': return_to,
        'schedule_current_path': request.get_full_path(),
        'schedule_is_favorite': is_favorite,
        'schedule_current_airing_id': current_airing.id if current_airing else None,
        'schedule_current_destination': current_destination,
        'schedule_current_destination_scope': current_destination_scope,
        'schedule_current_ends_in_minutes': current_ends_in_minutes,
        'schedule_next_airing_id': next_airing.id if next_airing else None,
        'schedule_next_starts_in_minutes': next_starts_in_minutes,
        'is_empty_day': is_empty_day,
        'nearest_populated_dates': nearest_populated_dates,
        **health_context,
    })