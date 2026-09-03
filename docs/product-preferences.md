# Personalized discovery

aitv should prioritize watchable content while allowing each viewer to decide what appears in discovery.

## Default behavior

- The public/default experience does not globally suppress a genre or program type. News is treated like any other category.
- Signed-in users can save their own preferred discovery categories to their account.
- Preferences can include or exclude Comedy, Crime, Drama, News, Reality, Science Fiction, Action, Documentary, Soap/Soap Opera, and other supported genres independently.
- A user's choices affect live and trending discovery rows, not another user's results.
- Soap/Soap Opera is normalized to the `Soap` preference so upstream wording differences do not bypass a user's category choice.
- Live-source cards expose genre and network/service information whenever the upstream source provides it.
- Provider/watch actions remain primary; metadata destinations remain secondary.

## Profile data and notifications

- Profile stores optional first name, last name, and email address on the user's Django account.
- Regional availability and discovery-category settings remain account-specific.
- Users can opt in to future email alerts for new episodes/releases associated with titles they save.
- Release notification opt-in requires a saved email address and defaults off.
- This sprint stores the delivery preference only; release detection and outbound email delivery are separate implementation work and must not send mail until that workflow exists and is explicitly configured.

Personalization applies to discovery results only. A user's saved catalog is never silently deleted or hidden because of discovery preferences.
