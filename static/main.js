let sort = 'az';
let loading = false;
let page = 1;
let searchScope = 'albums';
let currentLetter = 'null';
let allGrouped = {};
let letterOrder = [];
let currentLetterIndex = 0;
let substantialLetters = [];
let hasNext = true;

async function init() {
    const res = await fetch('/api/releases/by-letter')
    const data = await res.json();
    allGrouped = data.grouped;
    substantialLetters = data.substantial;

    //Build letter order: # first, then A-Z
    letterOrder = Object.keys(allGrouped).sort((a, b) => {
        if (a === '#') return -1;
        if (b === '#') return 1;
        return a.localeCompare(b);
    });

    //Pick random substantial letter
    const startLetter = substantialLetters[Math.floor(Math.random() * substantialLetters.length)];
    currentLetterIndex = letterOrder.indexOf(startLetter);

    buildLetterNav();
    showLetter(currentLetterIndex);
}

function buildLetterNav() {
    const nav = document.getElementById('letter-nav');
    if (!nav) return;
    nav.innerHTML = '';
    letterOrder.forEach((letter, index) => {
        const tab = document.createElement('button');
        tab.className = 'letter-tab';
        tab.textContent = letter;
        tab.dataset.index = index;
        if (index === currentLetterIndex) tab.classList.add('active');
        tab.addEventListener('click', () => navigateToLetter(index));
        nav.appendChild(tab);
    });
}

function showLetter(index) {
    currentLetterIndex = index;
    const letter = letterOrder[index];
    const collection = document.getElementById('collection');
    collection.innerHTML = '';
    const releases = allGrouped[letter] || [];
    releases.forEach(release => appendRelease(release));
    
    // Update active tab
    document.querySelectorAll('.letter-tab').forEach(tab => {
        tab.classList.toggle('active', parseInt(tab.dataset.index) === index);
    });
    updateEdgeTabs();
}

function updateEdgeTabs() {
    const prevTab = document.getElementById('prev-letter-tab');
    const nextTab = document.getElementById('next-letter-tab');
    
    if (!isLetterNavActive()) {
        prevTab.style.display = 'none';
        nextTab.style.display = 'none';
        return;
    }
    
    const prevLetter = letterOrder[currentLetterIndex - 1];
    const nextLetter = letterOrder[currentLetterIndex + 1];
    
    prevTab.style.display = prevLetter ? 'flex' : 'none';
    nextTab.style.display = nextLetter ? 'flex' : 'none';
    
    prevTab.textContent = prevLetter || '';
    nextTab.textContent = nextLetter || '';
}

function navigateToLetter(index) {
    showLetter(index);
}

function toggleSort() {
    sort = sort === 'random' ? 'az' : 'random';
    document.getElementById('toggle-sort').textContent =
        sort === 'az' ? 'A-Z View' : 'Random View';
    
    const letterNav = document.getElementById('letter-nav');
    const collection = document.getElementById('collection');
    collection.innerHTML = '';
    
    if (sort === 'random' || !isLetterNavActive()) {
        letterNav.style.display = 'none';
        hasNext = true;
        page = 1;
        loading = false;
        loadReleases();
        updateEdgeTabs();
    } else {
        letterNav.style.display = 'flex';
        showLetter(currentLetterIndex);
        updateEdgeTabs();
    }
}

function isLetterNavActive() {
    return sort === 'az' && (activeFormat === 'all' || activeFormat === 'Vinyl');
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
    if (format === 'CD') return '/static/icons/CD.png';
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
        document.getElementById('collection').innerHTML = '';
        const letterNav = document.getElementById('letter-nav');
        
        if (isLetterNavActive()) {
            letterNav.style.display = 'flex';
            buildLetterNav();
            showLetter(currentLetterIndex);
        } else {
            letterNav.style.display = 'none';
            hasNext = true;
            loading = false;
            loadReleases();
        }
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
            const collection = document.getElementById('collection');
            const letterNav = document.getElementById('letter-nav');
            collection.innerHTML = '';
            
            if (isLetterNavActive()) {
                letterNav.style.display = 'flex';
                fetch(`/api/releases/by-letter?format=${activeFormat}`)
                    .then(res => res.json())
                    .then(data => {
                        allGrouped = data.grouped;
                        substantialLetters = data.substantial;
                        letterOrder = Object.keys(allGrouped).sort((a, b) => {
                            if (a === '#') return -1;
                            if (b === '#') return 1;
                            return a.localeCompare(b);
                        });
                        const startLetter = substantialLetters.includes(letterOrder[currentLetterIndex])
                            ? letterOrder[currentLetterIndex]
                            : substantialLetters[0];
                        currentLetterIndex = letterOrder.indexOf(startLetter);
                        buildLetterNav();
                        showLetter(currentLetterIndex);
                        updateEdgeTabs();
                    });
            } else {
                letterNav.style.display = 'none';
                document.getElementById('collection').innerHTML = '';
                page = 1;
                hasNext = true;
                loading = false;
                loadReleases();
                updateEdgeTabs();
            }
        }
    });
});

function appendRelease(release) {
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

    fetch(`/api/releases?page=${page}&sort=${sort}&format=${activeFormat}`)
        .then(response => response.json())
        .then(data => {
            data.releases.forEach(release => appendRelease(release));
            loading = false;
            document.getElementById('loading').style.display = 'none';
            hasNext = data.has_next;
            page++;
        });
}

function insertWrapDivider(){
    const divider = document.createElement('div');
    divider.className = 'section-divider wrap-divider';
    document.getElementById('collection').appendChild(divider);
}

function runSearch(query) {
    isSearching = true;
    document.getElementById('letter-nav').style.display = 'none';
    fetch(`/api/search?q=${encodeURIComponent(query)}&scope=${searchScope}&format=${activeFormat}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('collection').innerHTML = '';
            data.releases.forEach(release => appendRelease(release));
        });
}

window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 300) {
        if (!isLetterNavActive() && !isSearching) {
            loadReleases();
        }
    }
});

init();