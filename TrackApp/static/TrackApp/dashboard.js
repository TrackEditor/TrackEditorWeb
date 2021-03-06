import * as utils from "../../../static/editor/utils.js";

document.addEventListener('DOMContentLoaded', () => {
    // Load initial page
    let page = 1;
    const number_pages = parseInt(document.querySelector('#pagination').dataset.number_pages);

    if (number_pages > 0) {
        load_tracks(page, number_pages);
        page_management(page, number_pages);
    }

});


function page_management(page, number_pages) {
    // Manage page changes
    document.querySelectorAll('.page-link').forEach(item => {
        item.addEventListener('click', () => {
            let previous_item = document.querySelector(`#page_${page}`);

            if (item.innerHTML != page) {
                if (item.innerHTML === 'Next') {
                    if (page < number_pages) {
                        previous_item.classList.remove('page-link-selected');
                        page++;
                        load_tracks(page, number_pages);
                    }
                } else if (item.innerHTML === 'Previous') {
                    if (page > 1) {
                        previous_item.classList.remove('page-link-selected');
                        page--;
                        load_tracks(page, number_pages);
                    }
                } else {
                    previous_item.classList.remove('page-link-selected');
                    page = parseInt(item.innerHTML);
                    load_tracks(page, number_pages);
                }
            }
        })
    });
}


function load_tracks(page, number_pages) {
    let tbody = document.querySelector('#table_body');
    tbody.innerHTML = '';
    document.querySelector('#div_spinner').style.display = 'inline-block';

    if (number_pages > 1) {
        document.querySelector(`#page_${page}`).classList.add('page-link-selected');
    }

    fetch(`/get_tracks_from_db/${page}`)
        .then(response => response.json())
        .then(tracks => {
            if (tracks.length === 0) {
                let div = document.getElementById('div_warning_msg');
                div.style.display = 'inline-block';
                div.innerHTML = 'You have removed all your tracks!';
                document.querySelector('#div_spinner').style.display = 'none';
            }
            tracks.forEach(track => {
                document.querySelector('#div_spinner').style.display = 'none';

                const tr = document.createElement('tr');
                const td_buttons = document.createElement('td');
                const td_track = document.createElement('td');
                const td_last_edit = document.createElement('td');

                const button_edit = document.createElement('a');
                const button_remove = document.createElement('button');

                button_edit.setAttribute('href', `editor/${track.id}`);
                button_edit.setAttribute('class', 'btn');
                button_edit.setAttribute('title', 'Edit');
                button_edit.innerHTML = '<span class="btn-edit">&#9998</span>';
                td_buttons.appendChild(button_edit);

                button_remove.setAttribute('class', 'btn-close');
                button_remove.setAttribute('aria-label', 'Close');
                button_remove.setAttribute('title', 'Remove');
                button_remove.addEventListener('click', () => remove_session(track.id, page));
                td_buttons.appendChild(button_remove);

                td_track.innerHTML = `<span class="track dashboard-title">${track.title}</span>`;
                td_last_edit.innerHTML = `<span class="track dashboard-last-edit">${track.last_edit}</span>`;

                tr.appendChild(td_buttons);
                tr.appendChild(td_track);
                tr.appendChild(td_last_edit);
                tbody.appendChild(tr);
            })
        });
}

function remove_session(id, page) {
    const btn_yes = document.getElementById('btn_yes');
    const modal = document.getElementById('div_confirmation_modal');
    const span = document.getElementsByClassName("close")[0];  // <span> element that closes the modal
    modal.style.display = 'block';

    // When the user clicks on <span> (x), close the modal
    span.onclick = () => {
      modal.style.display = 'none';
      return;
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = event => {
      if (event.target === modal) {
        modal.style.display = 'none';
        return;
      }
    }

    // When click yes
    btn_yes.onclick = () => {
        const csrftoken = utils.getCookie('csrftoken');
        document.querySelector('#div_spinner_modal').style.display = 'inline-block';
        fetch(`/editor/remove_session/${id}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
        })
        .then(response => {
            modal.style.display = 'none';
            console.log('remove_session', id);
            console.log(response.status);
            if (response.status === 201) {
                load_tracks(page);
            }
            else {
                let div = document.getElementById('div_error_msg');
                div.innerHTML = 'Unable to remove track'
                setTimeout(function(){
                    div.innerHTML = '';
                }, 3000);
            }
        })
    };
    document.querySelector('#div_spinner_modal').style.display = 'none';
}
