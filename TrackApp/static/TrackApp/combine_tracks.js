document.addEventListener('DOMContentLoaded', function() {
    var files = [];
    var count = 1;

    btn_select_gpx(count);

});

function btn_select_gpx(count) {
    let element_input = document.querySelector(`#select-file-${count}`);
    let element_label = document.querySelector(`#label-select-file-${count}`);
    let element_div = document.querySelector('#div_form');

    element_input.onchange = function() {
        var new_file = this.files[0];
        document.querySelector("#file-list").innerHTML += `<p>${new_file.name}</p>`;
        element_label.style.display = "none";

        new_element = create_btn_select_gpx(count+1);
        element_div.append(new_element);
        btn_select_gpx(count+1);
    }
}

function create_btn_select_gpx(count){
    let label = document.createElement('label');
    label.className = "btn btn-lg btn-select-file"
    label.innerHTML = "Select gpx"
    label.setAttribute('id', `label-select-file-${count}`);

    let input = document.createElement('input');
    input.setAttribute('id', `select-file-${count}`);
    input.setAttribute('type', 'file');
    input.setAttribute('accept', '.gpx');
    input.setAttribute('name', 'document');

    label.appendChild(input);

    return label;
}