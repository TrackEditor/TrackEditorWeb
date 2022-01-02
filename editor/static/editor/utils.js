export function activate_spinner(spinner_selector) {
    document.querySelector(spinner_selector).style.display = 'inline-block';
}


export function deactivate_spinner(spinner_selector) {
    document.querySelector(spinner_selector).style.display = 'none';
}


export function response_error_mng(status, fnc_name) {

    if ((status !== 200) && (status !== 201)) {
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


export function haversine_distance([lat1, lon1], [lat2, lon2]) {
    /* Compute distance between two coordinates */
    const toRadian = angle => (Math.PI / 180) * angle;
    const distance = (x, y) => (Math.PI / 180) * (x - y);
    const RADIUS_OF_EARTH_IN_KM = 6371;

    const dLat = distance(lat2, lat1);
    const dLon = distance(lon2, lon1);

    lat1 = toRadian(lat1);
    lat2 = toRadian(lat2);

    // Haversine Formula
    const a =
        Math.pow(Math.sin(dLat / 2), 2) +
        Math.pow(Math.sin(dLon / 2), 2) * Math.cos(lat1) * Math.cos(lat2);
    const c = 2 * Math.asin(Math.sqrt(a));

    return RADIUS_OF_EARTH_IN_KM * c;
}


export function getCookie(name) {
    /* Provided in the Django's documentation to get the csrf code
    *  https://docs.djangoproject.com/en/4.0/ref/csrf/ */
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
