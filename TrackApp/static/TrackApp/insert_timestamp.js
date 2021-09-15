document.addEventListener('DOMContentLoaded', function() {
    btn_select_gpx();
    btn_insert_timestamp();
});


function btn_select_gpx() {
    let element_input = document.querySelector('#select-file');
    let element_alert = document.querySelector('#div_alert');

    element_input.onchange = () => {
        const new_file = this.files[0];
        if ( check_file_size(new_file, element_alert) &&
             check_extension(new_file, element_alert) ) {
            document.querySelector('#file-list').innerHTML = `<p>${new_file.name}</p>`;
        }
    }

    let element_speed = document.querySelector('#input_desired_speed');
    element_speed.onchange = () => {
        check_speed(element_speed, element_alert);
    }

    let element_date = document.querySelector('#input_date');
    element_date.onchange = () => {
        check_date(element_date, element_alert);
    }

    let element_time = document.querySelector('#input_time');
    element_time.onchange = () => {
        check_time(element_time, element_alert);
    }

}


function check_file_size(file, element_alert) {
    let maximum_file_size = element_alert.dataset.maximum_file_size;

    if (file.size > maximum_file_size){
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = `File ${file.name} is ${Math.floor(file.size/1e6)} Mb. It must be smaller than ${maximum_file_size/1e6} Mb`;
        return false;
    }
    else {
        element_alert.style.display = 'none';
        element_alert.innerHTML = '';
        return true;
    }
}


function check_extension(new_file, element_alert) {
    let valid_extensions = element_alert.dataset.valid_extensions;

    let extension = new_file.name.split('.').pop();
    let is_valid = valid_extensions.includes(extension);

    if (!is_valid) {
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = `Extension for ${new_file.name} is not valid ${valid_extensions}.`;
        return false;
    }
    else {
        element_alert.style.display = 'none';
    }
    return true;
}


function check_speed(element_speed, element_alert) {
    let maximum_speed = element_alert.dataset.maximum_speed;

    if (element_speed.value === "") {
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = 'The maximum desired average speed is blank.';
        return false;
    }
    else if (parseFloat(element_speed.value) > parseFloat(maximum_speed)){
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = `The maximum desired average speed cannot exceed ${maximum_speed} km/h.`;
        return false;
    }
    else if (parseFloat(element_speed.value) <= 0){
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = 'The maximum desired average speed must be > 0 km/h.';
        return false;
    }
    else {
        element_alert.style.display = 'none';
        return true;
    }
}


function check_date(element_date, element_alert) {
    const date_reg = /^(\d{4})[-/](\d{2})[-/](\d{2})$/;
    const date = element_date.value;
    const date_array = date.match(date_reg);

    if (!date_reg.test(date)){
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = 'Date has wrong format.';
        return false;
    }
    else {
        if ( (date_array[1] > 2100) || (date_array[1] < 1900) ||
             (date_array[2] > 12) || (date_array[2] < 1) ||
             (date_array[3] > 31) || (date_array[3] < 1) ) {
            element_alert.style.display = 'block';
            element_alert.className = 'alert alert-danger';
            element_alert.setAttribute('role', 'alert');
            element_alert.setAttribute('id', 'div_error_msg_js');
            if ((date_array[1] > 2100) || (date_array[1] < 1900)) {
                element_alert.innerHTML = `Year ${date_array[1]} is not in range 1900 to 2100.`;
            }
            else if ((date_array[2] > 12) ||  (date_array[2] < 1)) {
                element_alert.innerHTML = `Month ${date_array[2]} is not in range 1 to 12.`;
            }
            else if ((date_array[3] > 31) || (date_array[3] < 1)) {
                element_alert.innerHTML = `Day ${date_array[3]} is not in range 1 to 31.`;
            }
            return false;
        }
    }

    element_alert.style.display = 'none';
    return true;
}

function check_time(element_time, element_alert) {
    const time_reg = /^(\d{2})[-/:](\d{2})$/;
    const time = element_time.value;
    const time_array = time.match(time_reg);

    if (!time_reg.test(time)){
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = 'Time has wrong format.';
        return false;
    }
    else {
        if ( (time_array[1] > 23) || (time_array[1] < 0) ||
             (time_array[2] > 59) || (time_array[2] < 0) ) {
            element_alert.style.display = 'block';
            element_alert.className = 'alert alert-danger';
            element_alert.setAttribute('role', 'alert');
            element_alert.setAttribute('id', 'div_error_msg_js');
            if ( (time_array[1] > 23) || (time_array[1] < 0) ) {
                element_alert.innerHTML = `Hour ${time_array[1]} is not in range 00 to 23.`;
            }
            else if ( (time_array[2] < 60) || (time_array[2] < 0) ) {
                element_alert.innerHTML = `Minute ${time_array[2]} is not in range 00 to 59.`;
            }

            return false;
        }
    }

    element_alert.style.display = 'none';
    return true;
}


function check_file(element_file, element_alert) {
    const file = element_file.files[0];

    if (typeof file === "undefined"){
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = 'No file has been selected.';
        return false;
    }
    else {
        element_alert.style.display = 'none';
        return true;
    }
}


function btn_insert_timestamp() {
    let element_insert_btn = document.querySelector('#input_btn_insert_timestamp');
    let element_alert = document.querySelector('#div_alert');
    let element_speed = document.querySelector('#input_desired_speed');
    let element_date = document.querySelector('#input_date');
    let element_time = document.querySelector('#input_time');
    let element_form = document.querySelector('#form');
    let element_file = document.querySelector('#select-file');

    element_insert_btn.onclick = () => {
        if ( check_speed(element_speed, element_alert) &&
             check_date(element_date, element_alert) &&
             check_time(element_time, element_alert) &&
             check_file(element_file, element_alert)) {
            element_form.submit();

            // Activate spinner
            let spinner = document.querySelector('#div_spinner');
            spinner.style.display = 'inline-block';
        }
    }
}
