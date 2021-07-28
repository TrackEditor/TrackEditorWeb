
document.addEventListener('DOMContentLoaded', function() {
    // Load initial page
    var page = 1;
    var number_pages = parseInt(document.querySelector('#pagination').dataset.number_pages);
    load_tracks(page);

    // Manage page changes
    document.querySelectorAll('.page-link').forEach(item => {
        item.addEventListener('click', event => {
                let previous_item = document.querySelector(`#page_${page}`);

                if (item.innerHTML !== page){
                    if (item.innerHTML === 'Next') {
                        if (page < number_pages) {
                            previous_item.classList.remove('page-link-selected');
                            page++;
                            load_tracks(page);
                        }
                    }
                    else if (item.innerHTML === 'Previous') {
                        if (page > 1) {
                            previous_item.classList.remove('page-link-selected');
                            page--;
                            load_tracks(page);
                        }
                    }
                    else {
                        previous_item.classList.remove('page-link-selected');
                        page = parseInt(item.innerHTML);
                        load_tracks(page);
                    }
                }
            })
    });

});


function load_tracks(page) {
    let tbody = document.querySelector('#table_body');
    tbody.innerHTML = '';
    document.querySelector('#div_spinner').style.display = 'inline-block';
    document.querySelector(`#page_${page}`).classList.add('page-link-selected');

    fetch(`/get_tracks_from_db/${page}`)
        .then(response => response.json())
        .then(tracks => {
            tracks.forEach(track => {
                document.querySelector('#div_spinner').style.display = 'none';

                const tr = document.createElement('tr');
                const td_buttons = document.createElement('td');
                const td_track = document.createElement('td');
                const td_last_edit = document.createElement('td');

                td_buttons.innerHTML =
                        `<button class="btn" type="button" title="Edit" id="btn_edit_${track.id}">
                            <span class="btn-edit">&#9998</span>
                        </button>
                        <button type="button" class="btn-close" aria-label="Close" title="Remove" id="btn_remove_${track.id}"></button>`;

                td_track.innerHTML = `<span class="track">track_${track.id}</span>`;
                td_last_edit.innerHTML = `<span class="track">${track.last_edit}</span>`;

                tr.appendChild(td_buttons);
                tr.appendChild(td_track);
                tr.appendChild(td_last_edit);
                tbody.appendChild(tr);
            })
        });
}