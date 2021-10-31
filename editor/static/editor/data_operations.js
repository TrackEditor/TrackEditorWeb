import * as utils from "./utils.js";

export function submit_file() {
    /* Submit the file when it is selected, not when a submit button
    * is clicked. */
    document.querySelector('#select-file').onchange = () => {
        document.querySelector('form').submit();
        utils.activate_spinner('#div_spinner');
    };
}

export async function load_track() {
    try {
        const response = await fetch('/editor/get_track');
        utils.response_error_mng(response.status, 'load_track');

        return await response.json();
    } catch (error) {
        utils.display_error('error', error);
    }
}


export function save_session() {
    /*
    Save the current track object in backend when clicking the
    save button
    */
    let btn_save = document.getElementById('btn_save');

    btn_save.addEventListener('click', () => {
        document.querySelector('#div_spinner').style.display = 'inline-block';
        fetch('/editor/save_session', {
            method: 'POST',
        })
        .then(response => {
            document.querySelector('#div_spinner').style.display = 'none';

            let div = document.getElementById('div_alerts_box');
            if (response.status === 201){
                div.innerHTML = '<div class="alert alert-success" role="alert">Session has been saved</div>';
            }
            else if (response.status === 491){
                div.innerHTML = '<div class="alert alert-warning" role="alert">No track is loaded</div>';
            }
            else if (response.status === 492){
                div.innerHTML = '<div class="alert alert-danger" role="alert">Unexpected error. Code: 492</div>';
            }
            else {
                div.innerHTML = '<div class="alert alert-danger" role="alert">Unexpected error. Unable to save</div>';
            }

            setTimeout(() => {
                div.innerHTML = '';
            }, 3000);

        })
    });
}

function download(url, filename) {
    fetch(url).then(t => {
        return t.blob().then((b)=>{
            let a = document.createElement("a");
            a.href = URL.createObjectURL(b);
            a.setAttribute("download", filename);
            a.click();
        })
            .catch(error => utils.response_error_mng(-1, error));
    })
        .then(response => utils.response_error_mng(response.status, 'download'))
        .catch(error => utils.response_error_mng(-1, error));
}


export function download_session() {
    let btn_download = document.querySelector('#btn_download');

    btn_download.addEventListener('click', () => {
        utils.activate_spinner('#div_spinner');

        fetch('/editor/download_session', {
            method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                utils.deactivate_spinner('#div_spinner');

                if (data.hasOwnProperty('error')) {
                    utils.display_error('error', data.error);
                }
                else if (data.hasOwnProperty('url')) {
                    download(data.url, data.filename);
                }
            })
            .catch(error => utils.response_error_mng(-1, error));

    });

}

export function update_session_name() {
    let e_title = document.querySelector('#h_session_name');
    let old_name = e_title.innerHTML;

    const rename_session = () => {
        let new_name = e_title.innerHTML.trim();

        if (new_name.length === 0) {
            e_title.innerHTML = old_name;
            utils.display_error('error', 'Session title cannot be blank');
            return;
        }
        else {
            old_name = new_name;
        }
        fetch(`/editor/rename_session/${new_name}`, {
            method: 'POST',
        })
            .then(response => utils.response_error_mng(response.status, 'update_session_name'))
            .catch(error => utils.response_error_mng(-1, error));
    };

    e_title.addEventListener('blur', () => {
        rename_session();
    });

    e_title.addEventListener('keydown', event => {
        if (event.code === 'Enter') {  // when pressing enter
            event.preventDefault();  // prevent inserting line break
            rename_session();
            e_title.blur();  // remove focus
        }
    });
}
