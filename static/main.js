let page = 1;
let sort = 'az';
let loading = false;
let hasNext = true;
let searchScope = 'albums';

function toggleSort() {
    sort = sort === 'random' ? 'az' : 'random';
    document.getElementById('toggle-sort').textContent =
        sort === 'az' ? 'A-Z View' : 'Random View';
    page = 1;
    hasNext = true;
    document.getElementById('collection').innerHTML = '';
    loadReleases();
}

const toggleBtn = document.getElementById('toggle-sort');

toggleBtn.addEventListener('mouseenter', function() {
    this.textContent = sort === 'az' ? 'Random View' : 'A-Z View';
});

toggleBtn.addEventListener('mouseleave', function() {
    this.textContent = sort === 'az' ? 'A-Z View' : 'Random View';
});

const scopePlaceholders = {
    'albums': 'Search artists and albums...',
    'songs': 'Search song titles...',
    'years': 'Search by year or decade (e.g. 1975, 70s)...'
};

document.querySelectorAll('.scope-pill').forEach(pill => {
    pill.addEventListener('click', function() {
        document.querySelectorAll('.scope-pill').forEach(p => p.classList.remove('active'));
        this.classList.add('active');
        searchScope = this.dataset.scope;
        document.getElementById('search-bar').placeholder = scopePlaceholders[searchScope];

        const query = document.getElementById('search-bar').value.trim();
        if (query) {
            fetch(`/api/search?q=${encodeURIComponent(query)}&scope=${searchScope}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('collection').innerHTML = '';
                    data.releases.forEach(release => appendRelease(release));
                });
        }
    });

    pill.addEventListener('mouseenter', function() {
        document.getElementById('search-bar').placeholder = scopePlaceholders[this.dataset.scope];
    });

    pill.addEventListener('mouseleave', function() {
        document.getElementById('search-bar').placeholder = scopePlaceholders[searchScope];
    });
});

function getFormatIcon(format) {
    if (format === 'CD') return '/static/icons/cd.png';
    if(format === 'Cassette') return '/static/icons/cassette.png';
    return '/static/icons/vinyl.png';
}


let searchTimeout = null;
let isSearching = false;

document.getElementById('search-bar').addEventListener('input', function() {
    console.log('input fired:', this.value);
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
        runSearch(query);
    }, 300);
});   

let activeFormat = 'all';

const formatPill = document.getElementById('format-pill');
const formatDropdown = document.getElementById('format-dropdown');

formatPill.addEventListener('click', function(e) {
    e.stopPropagation();
    formatDropdown.classList.toggle('open');
});

document.addEventListener('click', function() {
    formatDropdown.classList.remove('open');
});

document.querySelectorAll('.format-option').forEach(option => {
    option.addEventListener('click', function() {
        document.querySelectorAll('.format-option').forEach(o => o.classList.remove('active'));
        this.classList.add('active');
        activeFormat = this.dataset.format;
        
        // Update pill label
        if (activeFormat === 'all') {
            formatPill.textContent = 'Format ▾';
            formatPill.classList.remove('active-filter');
        } else {
            formatPill.textContent = activeFormat + ' ▾';
            formatPill.classList.add('active-filter');
        }
        
        // Reload with new filter
        const query = document.getElementById('search-bar').value.trim();
        if (query) {
            runSearch(query);
        } else {
            page = 1;
            hasNext = true;
            document.getElementById('collection').innerHTML = '';
            loadReleases();
        }
    });
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
        <p class="release-artist"><a href="/artist/${release.artist_id}" class="artist-link">${release.artist}</a>${release.release_year ? ' · <span class="release-year">' + release.release_year + '</span>' : ''}</p>
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

    fetch(`/api/releases?page=${page}&sort=${sort}&format=${activeFormat}`)
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

function runSearch(query) {
    isSearching = true;
    fetch(`/api/search?q=${encodeURIComponent(query)}&scope=${searchScope}&format=${activeFormat}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('collection').innerHTML = '';
            data.releases.forEach(release => appendRelease(release));
        });
}

    window.addEventListener('scroll', () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 300) {
            loadReleases();
    }
});

loadReleases();