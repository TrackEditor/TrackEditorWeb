document.addEventListener('DOMContentLoaded', function() {

    document.querySelector("#select-file").onchange = function(){
      document.querySelector("#file-name").textContent = this.files[0].name;
    }
});