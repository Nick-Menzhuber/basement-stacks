let page = 1;
let sort = 'random';
let loading = false;
let hasNext = true;

function toggleSort() {
    sort = sort === 'random' ? 'az' : 'random';
    document.getElementById('toggle-sort').textContent =
        sort === 'random' ? 'A-Z View' : 'Random View';
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


let searchTimeout = null;
let isSearching = false;

document.getElementById('search-bar').addEventListener('input', function() {
    clearTimeout(searchTimeout);
    const query = this.value.trim();
    
    if (query === '') {
        isSearching = false;
        page = 1;
        hasNext = true;
        document.getElementById('collection').innerHTML = '';
        loadReleases();
        return;
    }
    
    searchTimeout = setTimeout(() => {
        isSearching = true;
        fetch(`/api/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('collection').innerHTML = '';
                data.releases.forEach(release => {
                    appendRelease(release);
                });
            });
    }, 300);
});

function appendRelease(release) {
    const collection = document.getElementById('collection');
    const div = document.createElement('div');
    div.className = 'release';
    const icons = release.formats.map(f =>
        `<img src="${getFormatIcon(f)}" class="format-icon" title="${f}">`
    ).join('');
    div.innerHTML = `
        <div class="cover-wrapper">
            <img src="${release.cover_image_url}" alt="${release.title}">
            <div class="format-icons">${icons}</div>
        </div>
        <h2>${release.title}</h2>
        <p>${release.artist}${release.release_year ? ' · ' + release.release_year : ''}</p>
    `;
    collection.appendChild(div);
    div.addEventListener('click', () => {
        window.location.href = `/release/${release.id}`;
    });
}

function loadReleases() {
    if (loading || !hasNext) return
    loading = true;
    document.getElementById('loading').style.display = 'block';

    fetch(`/api/releases?page=${page}&sort=${sort}`)
        .then(response => response.json())
        .then(data => {
            const collection = document.getElementById('collection');
            data.releases.forEach(release => appendRelease(release));
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