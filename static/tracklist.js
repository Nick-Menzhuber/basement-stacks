function getOrdinal(n) {
    const ordinals = ['One', 'Two', 'Three', 'Four', 'Five', 'Six'];
    return ordinals[n - 1] || n;
}

function isVinylSideFormat(tracks) {
    return tracks.some(t => t.position && /^[A-F]\d+$/.test(t.position));
}

function isDiscFormat(tracks) {
    return tracks.some(t => t.position && /^\d+-\d+$/.test(t.position));
}

function hasVinylOrCassette(formats) {
    return formats.some(f => f === 'Vinyl' || f === 'Cassette');
}

function is7Inch(formats) {
    return formats.includes('7"');
}

function buildTracklistHTML(tracks, formats) {
    if (!tracks || tracks.length === 0) {
        return '<p class="no-tracklist">No tracklist available.</p>';
    }

    if (is7Inch(formats)) {
        return build7InchTracklist(tracks);
    }

    if (hasVinylOrCassette(formats) && isVinylSideFormat(tracks)) {
        return buildSidedTracklist(tracks);
    }

    if (isDiscFormat(tracks)) {
        return buildDiscTracklist(tracks);
    }

    return buildSimpleTracklist(tracks);
}

function build7InchTracklist(tracks) {
    const realTracks = tracks.filter(t => t.type_ !== 'heading' && t.position);
    let html = '<div class="tracklist-45">';
    for (const track of realTracks) {
        const side = track.position.match(/^([AB])/)?.[1];
        const sideLabel = side ? `Side ${side}` : '';
        html += `
            <div class="track-45">
                <span class="side-label-45">${sideLabel}</span>
                <span class="track-title">${track.title}</span>
                <span class="track-duration">${track.duration || ''}</span>
            </div>`;
    }
    html += '</div>';
    return html;
}

function buildSidedTracklist(tracks) {
    const sides = {};
    for (const track of tracks) {
        if (track.type_ === 'heading' || !track.position) continue;
        const match = track.position.match(/^([A-F])(\d+)$/);
        if (match) {
            const letter = match[1];
            const number = match[2];
            if (!sides[letter]) sides[letter] = [];
            sides[letter].push({ ...track, shortPosition: number });
        }
    }

    const sideLetters = Object.keys(sides).sort();
    return buildPairedLayout(sideLetters, (letter) => {
        const sideNumber = letter.charCodeAt(0) - 64;
        return {
            heading: `Side ${getOrdinal(sideNumber)}`,
            tracks: sides[letter],
            positionKey: 'shortPosition'
        };
    });
}

function buildDiscTracklist(tracks) {
    const discs = {};
    for (const track of tracks) {
        if (track.type_ === 'heading' || !track.position) continue;
        const match = track.position.match(/^(\d+)-(\d+)$/);
        if (match) {
            const disc = match[1];
            const number = match[2];
            if (!discs[disc]) discs[disc] = [];
            discs[disc].push({ ...track, shortPosition: number });
        }
    }

    const discNumbers = Object.keys(discs).sort((a, b) => a - b);
    return buildPairedLayout(discNumbers, (disc) => {
        return {
            heading: `Disc ${getOrdinal(parseInt(disc))}`,
            tracks: discs[disc],
            positionKey: 'shortPosition'
        };
    });
}

function buildPairedLayout(keys, getSection) {
    const pairs = [];
    for (let i = 0; i < keys.length; i += 2) {
        pairs.push(keys.slice(i, i + 2));
    }

    let html = '<div class="sides-container">';
    for (const pair of pairs) {
        html += '<div class="sides-row">';
        for (const key of pair) {
            const section = getSection(key);
            html += `<div class="side">`;
            html += `<h4 class="side-heading">${section.heading}</h4>`;
            html += '<table class="tracklist-table">';
            for (const track of section.tracks) {
                html += `
                    <tr class="tracklist-track">
                        <td class="track-position">${track[section.positionKey]}</td>
                        <td class="track-title">${track.title}</td>
                        <td class="track-duration">${track.duration || ''}</td>
                    </tr>`;
            }
            html += '</table></div>';
        }
        html += '</div>';
    }
    html += '</div>';
    return html;
}

function buildSimpleTracklist(tracks) {
    let counter = 0;
    let html = '<table class="tracklist-table">';
    for (const track of tracks) {
        if (track.type_ === 'heading') {
            html += `<tr><td colspan="3" class="tracklist-heading">${track.title}</td></tr>`;
            continue;
        }
        counter++;
        html += `
            <tr class="tracklist-track">
                <td class="track-position">${counter}</td>
                <td class="track-title">${track.title}</td>
                <td class="track-duration">${track.duration || ''}</td>
            </tr>`;
    }
    html += '</table>';
    return html;
}