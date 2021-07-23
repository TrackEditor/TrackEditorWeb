document.addEventListener('DOMContentLoaded', function() {
    insert_map();
    submit_file();
    insert_track_name();
});


function submit_file() {
    document.querySelector('#select-file').onchange = function() {
        document.querySelector('form').submit();
        document.querySelector('#div_spinner').style.display = 'inline-block';
    };
}


function insert_track_name() {
    let div_track_list = document.querySelector('#div_track_list');
    let track_list = eval(div_track_list.dataset.track_list);

    if (typeof track_list !== 'undefined') {
        for (var i = 0; i < track_list.length; i++) {
            let color = get_color(i, alpha='-1');

            const p_name = document.createElement('p');
            const span_name = document.createElement('span');
            const span_marker = document.createElement('span');
            const button_remove = document.createElement('button');

            span_marker.innerHTML = '&#9899';
            span_marker.style = `font-size: 20px; color: transparent;  text-shadow: 0 0 0 ${color};`;

            span_name.style = 'font-size: 18px; margin-left: 5px;';
            span_name.setAttribute('contenteditable', 'true');
            span_name.innerHTML = track_list[i];
            span_name.addEventListener('blur', function() {
                console.log('Change track name ', i, span_name.innerHTML);
                // TODO create fetch for change_segment_name endpoint
                // TODO store in track a name for each segment
                // TODO convert track segment to JSON
            });

            button_remove.setAttribute('class', 'btn-close');
            button_remove.setAttribute('type', 'button');
            button_remove.setAttribute('aria-label', 'Close');
            button_remove.style = 'font-size: 18px; vertical-align: -3px; margin-left: 20px;';
            button_remove.addEventListener('click', function() {
                console.log('Remove track ', i);
                p_name.style.display = 'none';
                // TODO remove segment from pandas
                // TODO remove segment plot
                // TODO create fetch for remove_segment endpoint
            });

            p_name.appendChild(span_marker);
            p_name.appendChild(span_name);
            p_name.appendChild(button_remove);
            div_track_list.appendChild(p_name);
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
        target: 'js-map'
    });
}
