export function activate_spinner(spinner_selector) {
    document.querySelector(spinner_selector).style.display = 'inline-block';
}

export function deactivate_spinner(spinner_selector) {
    document.querySelector(spinner_selector).style.display = 'none';
}

export function response_error_mng(status, fnc_name) {
    if (status !== 200) {
        if (status === 520) {
            display_error('error', 'No track is loaded');
        } else if ((status >= 500) && (status < 600)) {
            display_error('error', `Server error: ${status} (${fnc_name})`);
        } else {
            display_error('error', `Unexpected error: ${status} (${fnc_name})`);
        }
    }
}

export function display_error(severity, msg) {
    let div = document.getElementById('div_alerts_box');
    if (severity === 'error') {
        div.innerHTML = `<div class="alert alert-danger" role="alert">${msg}</div>`;
    }
    else if (severity === 'warning') {
        div.innerHTML = `<div class="alert alert-warning" role="alert">${msg}</div>`;
    }
    else {
        div.innerHTML = `<div class="alert alert-primary" role="alert">${msg}</div>`;
    }
    div.style.display = 'inline-block';

    setTimeout(() => {
        div.style.display = 'none';
        div.innerHTML = '';
    }, 3000);
}


export function get_segment(track, segment_index) {
    for (let segment of track['segments']) {
        if (segment['index'] === segment_index) {
            return segment;
        }
    }
}
