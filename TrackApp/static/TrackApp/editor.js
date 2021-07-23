document.addEventListener('DOMContentLoaded', function() {
    insert_map();
    submit_file();
    insert_track_name();
});


function submit_file() {
    document.querySelector("#select-file").onchange = function() {
        document.querySelector("form").submit();
        document.querySelector('#div_spinner').style.display = 'inline-block';
    };
}


function insert_track_name() {
    let div_track_list = document.querySelector("#div_track_list");
    let track_list = eval(div_track_list.dataset.track_list);

    if (typeof track_list !== "undefined") {
        for (var i = 0; i < track_list.length; i++) {
            let color = get_color(i, alpha='-1');
            console.log(i, color);
            let identifier = `<span style="font-size: 20px; color: transparent;  text-shadow: 0 0 0 ${color};">&#9899;</span>`;
            console.log(identifier);
            div_track_list.innerHTML += `<p>${identifier} <span contenteditable style="font-size: 18px;">${track_list[i]}</span></p>`;
        }
    }
}


function get_color(color_index, alpha='0.5') {
    const colors = ['255, 127, 80',  // coral
                    '30, 144, 255',  // dodgerblue
                    '50, 205, 50', // limegreen
                    '255, 105, 180', // hotpink
                    '250, 128, 114',  // salmon
                    '123, 104, 238', // MediumSlateBlue
                    '34, 139, 34', // forestgreen
                    '255, 0, 0',  // red
                    '95, 158, 160',  // cadetblue
                    '218, 112, 214',  // orchid
                    '189, 183, 107',  // darkkhaki
                    '160, 82, 45',  // sienna
                    '255, 215, 0', // gold
                    '64, 224, 208',  // turquoise
                    '0, 128, 128', // teal
                   ];

    if (alpha === '-1') {
        return `rgb(${colors[color_index]})`;
    }

    return `rgb(${colors[color_index]}, ${alpha})`;
}


function insert_map() {
    // Create map
    const map = new ol.Map({
        view: new ol.View({
            center: ol.proj.fromLonLat([0, 0]),
            zoom: 1,
            maxZoom: 16,
            minZoom: 1
        }),
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            }),
        ],
        target: "js-map"
    });
}
