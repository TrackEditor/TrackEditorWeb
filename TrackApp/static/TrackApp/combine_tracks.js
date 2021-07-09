    document.addEventListener('DOMContentLoaded', function() {
    var count = 1;

    btn_select_gpx(count);

});

function btn_select_gpx(count) {
    let element_input = document.querySelector(`#select-file-${count}`);
    let element_label = document.querySelector(`#label-select-file-${count}`);
    let element_div = document.querySelector('#div_form');

    element_input.onchange = function() {
        var new_file = this.files[0];

        if ( check_number_files(count) && check_file_size(new_file) ){
            document.querySelector('#file-list').innerHTML += `<p>${new_file.name}</p>`;
            element_label.style.display = 'none';

            new_element = create_btn_select_gpx(count+1);
            element_div.append(new_element);
            btn_select_gpx(count+1);
        }
    }
}

function check_file_size(file) {
    let element_alert = document.querySelector('#div_alert');

    if (file.size > 1e7){  // TODO move constant to corresponding file
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.innerHTML = `File ${file.name} is ${file.size/1e6}. It must be smaller than 10Mb`;
        return false;
    }
    else {
        element_alert.style.display = 'none';
        return true;
    }
}

function check_number_files(count) {
    let element_alert = document.querySelector('#div_alert');

    if (count > 5){  // TODO move constant to corresponding file
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.innerHTML = 'No more than 5 files are allowed.';
        return false;
    }
    else {
        element_alert.style.display = 'none';
        return true;
    }
}

function create_btn_select_gpx(count){
    let label = document.createElement('label');
    label.className = 'btn btn-lg btn-select-file'
    label.innerHTML = 'Select gpx'
    label.setAttribute('id', `label-select-file-${count}`);

    let input = document.createElement('input');
    input.setAttribute('id', `select-file-${count}`);
    input.setAttribute('type', 'file');
    input.setAttribute('accept', '.gpx');
    input.setAttribute('name', 'document');

    label.appendChild(input);

    return label;
}