let startPage = 1;
let currentPage = 1;
let wrapped = false;
let sort = 'az';
let loading = false;
let hasNext = true;
let searchScope = 'albums';
let currentLetter = 'null';

async function init() {
    const res = await fetch('/api/releases/count');
    const data = await res.json();
    startPage = Math.floor(Math.random() * data.total_pages) + 1;
    currentPage = startPage;
    loadReleases();
}

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
    if (!isSearching) {
        const sortLetter = release.sort_name[0].toUpperCase();
        if (sortLetter !== currentLetter) {
            currentLetter = sortLetter;
            const divider = document.createElement('div');
            divider.className = 'section-divider letter-divider';
            divider.dataset.letter = sortLetter;
            document.getElementById('collection').appendChild(divider);
        }
    }
    const collection = document.getElementById('collection');
    const div = document.createElement('div');
    div.className = 'release';
    const displayTitle = release.short_title || release.title;
    const icons = release.formats.map(f => {
        const slug = f === '7"' ? '7inch' : f.toLowerCase();
        return `<a href="/release/${release.id}/${slug}" onclick="event.stopPropagation()"><img src="${getFormatIcon(f)}" class="format-icon" title="${f}"></a>`;
    }).join('');
    div.innerHTML = `
        <div class="cover-wrapper">
            <img src="${release.cover_image_url}" alt="${displayTitle}">
            <div class="format-icons">${icons}</div>
        </div>
        <h2>${displayTitle}</h2>
        <p class="release-artist"><a href="/artist/${release.artist_id}" class="artist-link">${release.artist}</a>${release.release_year ? ' · <span class="release-year">' + release.release_year + '</span>' : ''}</p>
    `;
    collection.appendChild(div);
    div.addEventListener('click', () => {
        window.location.href = `/release/${release.id}`;
    });
}

function loadReleases() {
    if (loading || !hasNext) return;
    loading = true;
    document.getElementById('loading').style.display = 'block';

    fetch(`/api/releases?page=${currentPage}&sort=${sort}&format=${activeFormat}`)
        .then(response => response.json())
        .then(data => {
            data.releases.forEach(release => appendRelease(release));
            loading = false;
            document.getElementById('loading').style.display = 'none';

            if (data.has_next && currentPage + 1 !== startPage) {
                currentPage++;
            } else if (!wrapped && startPage > 1) {
                wrapped = true;
                insertWrapDivider();
                currentPage = 1;
                hasNext = true;
            } else {
                hasNext = false;
            }
        });
}

function insertWrapDivider(){
    const divider = document.createElement('div');
    divider.className = 'section-divider wrap-divider';
    document.getElementById('collection').appendChild(divider);
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

init();