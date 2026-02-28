let page = 1;
let sort = 'random';
let loading = false;
let hasNext = true;

function toggleSort() {
    sort = sort === 'random' ? 'az' : 'random';
    document.getElementById('toggle-sort').textContent =
        sort === 'random' ? 'Switch to A-Z' : 'Switch to Random';
    page = 1;
    hasNext = true;
    document.getElementById('collection').innerHTML = '';
    loadReleases();
}

function getFormatIcon(format) {
    if (format === 'CD') return '/static/icons/cd.png';
    if(format === 'Cassette') return '/static/icons/cassette.png';
    return '/static/icons/vinyl.png';
}

function loadReleases() {
    if (loading || !hasNext) return
    loading = true;
    document.getElementById('loading').style.display = 'block';

    fetch(`/api/releases?page=${page}&sort=${sort}`)
        .then(response => response.json())
        .then(data => {
            const collection = document.getElementById('collection');
            data.releases.forEach(release => {
                const div = document.createElement('div');
                div.className = 'release';
                const icons = release.formats.map(f =>
                    `<img src="${getFormatIcon(f)}" class="format-icon" title=${f}>`)
                .join('');
            div.innerHTML = `
                    <div class="cover-wrapper">
                        <img src="${release.cover_image_url}" alt="${release.title}">
                        <div class="format-icons">${icons}</div>
                    </div>
                    <h2>${release.title}</h2>
                    <p>${release.artist}</p>
                `;
                collection.appendChild(div);
                });
                hasNext = data.has_next;
                page++;
                loading = false;
                document.getElementById('loading').style.display = 'none';
            });
    }

    window.addEventListener('scroll', () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 300) {
            loadReleases();
    }
});

loadReleases();