document.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-watch-options]');
    if (!button) return;

    const results = button.parentElement.querySelector('[data-watch-options-results]');
    if (!results) return;

    button.disabled = true;
    const originalLabel = button.textContent;
    button.textContent = 'Checking…';

    try {
        const response = await fetch(button.dataset.watchOptionsUrl, {
            headers: {'Accept': 'application/json'},
            credentials: 'same-origin',
        });
        if (!response.ok) throw new Error(`Watch options lookup failed: ${response.status}`);

        const data = await response.json();
        results.replaceChildren();

        if (!data.providers || data.providers.length === 0) {
            const message = document.createElement('div');
            message.className = 'small text-muted';
            message.textContent = 'No US streaming provider is listed yet.';
            results.appendChild(message);
        } else {
            for (const provider of data.providers) {
                const row = document.createElement('div');
                row.className = 'watch-provider-row';

                const name = document.createElement('strong');
                name.textContent = provider.name;
                row.appendChild(name);

                const access = document.createElement('span');
                access.className = 'small text-muted';
                access.textContent = provider.access;
                row.appendChild(access);

                results.appendChild(row);
            }

            if (data.link) {
                const link = document.createElement('a');
                link.href = data.link;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.className = 'btn btn-sm btn-primary w-100 mt-1';
                link.textContent = '▶ Open watch options';
                results.appendChild(link);
            }
        }

        results.hidden = false;
        button.textContent = '✓ Watch options loaded';
    } catch (error) {
        console.error(error);
        results.hidden = false;
        results.textContent = 'Could not load watch options.';
        button.textContent = originalLabel;
    } finally {
        button.disabled = false;
    }
});
