document.addEventListener('DOMContentLoaded', function() {
    var count = 1;
    var files = [];
    btn_select_gpx(count, files);
    activate_spinner();
});


function btn_select_gpx(count, files) {
    let element_input = document.querySelector(`#select-file-${count}`);
    let element_label = document.querySelector(`#label-select-file-${count}`);
    let element_div = document.querySelector('#div_form');

    element_input.onchange = function() {
        var new_file = this.files[0];

        if ( check_number_files(count) &&
             check_file_size(new_file) &&
             check_repeated_element(files, new_file) &&
             check_extension(new_file) ) {
            files.push(`${new_file.name}-${new_file.size}-${new_file.lastModified}`);
            console.log(files);
            document.querySelector('#file-list').innerHTML += `<p>${new_file.name}</p>`;
            element_label.style.display = 'none';

            new_element = create_btn_select_gpx(count+1);
            element_div.append(new_element);
            btn_select_gpx(count+1, files);
        }
    }
}


function check_file_size(file) {
    let element_alert = document.querySelector('#div_alert');
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
        return true;
    }
}


function check_number_files(count) {
    let element_alert = document.querySelector('#div_alert');
    let maximum_files = element_alert.dataset.maximum_files;

    if (count > maximum_files){
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = `No more than ${maximum_files} files are allowed.`;
        return false;
    }
    else {
        element_alert.style.display = 'none';
        return true;
    }
}


function check_repeated_element(files, new_file){
    let element_alert = document.querySelector('#div_alert');
    let repeated = files.includes(`${new_file.name}-${new_file.size}-${new_file.lastModified}`);

    if (repeated) {
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = `Repeated file is selected: ${new_file.name}`;
        return false;
    }
    else {
        element_alert.style.display = 'none';
        return true;
    }
}


function check_extension(new_file){
    let element_alert = document.querySelector('#div_alert');
    let valid_extensions = element_alert.dataset.valid_extensions;

    let extension = new_file.name.split('.').pop();
    let is_valid = valid_extensions.includes(extension);

    if (!is_valid) {
        element_alert.style.display = 'block';
        element_alert.className = 'alert alert-danger';
        element_alert.setAttribute('role', 'alert');
        element_alert.setAttribute('id', 'div_error_msg_js');
        element_alert.innerHTML = `Extension for ${new_file.name} is not valid ${valid_extensions}`;
        return false;
    }
    else {
        element_alert.style.display = 'none';
    }

    return true;
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


function activate_spinner(){
    let element_combine_btn = document.querySelector('#input_btn_combine');
    element_combine_btn.onclick = function() {
        let spinner = document.querySelector('#div_spinner');
        spinner.style.display = 'inline-block';
    }
}
