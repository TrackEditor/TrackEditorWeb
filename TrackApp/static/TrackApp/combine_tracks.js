document.addEventListener('DOMContentLoaded', function() {
    var files = []

    document.querySelector("#select-file").onchange = function(){
        var new_file = this.files[0].name;
        document.querySelector("#file-list").innerHTML += `<p>${new_file}</p>`;
        files.push(new_file);
        console.log(files);
    }

    document.querySelector("#input_btn_combine").onclick = function(){
        event.preventDefault();
        var n_files = files.length;
        alert(`There are ${n_files} files`);

        fetch("/combine_tracks/api", {
            method: "POST",
            body: JSON.stringify({
                file_list: files
            })
        }).then(response => console.log(response));
    }
});