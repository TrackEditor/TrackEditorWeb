document.addEventListener('DOMContentLoaded', function() {
    let map = create_map();
    submit_file();
    manage_track_names();
    plot_tracks(map);
//    plot_last_segment(map);
});


function submit_file() {
    /*
    SUBMIT_FILE submit the file when it is selected, not when a submit button
    is clicked. A spinner is activated while the uploading.
    */
    document.querySelector('#select-file').onchange = function() {
        document.querySelector('form').submit();
        document.querySelector('#div_spinner').style.display = 'inline-block';
    };
}


function plot_tracks(map) {
    /*
    PLOT_TRACKS plots all available segments in the map
    */
    let div_track_list = document.querySelector('#div_track_list');  // TODO modify with API endpoint
    let track_list = eval(div_track_list.dataset.track_list);

    if (typeof track_list !== 'undefined') {
        for (var i = 1; i < track_list.length+1; i++) {
            console.log('plot_tracks', i);
            plot_segment(map, i);
        }
    }
}


function manage_track_names() {
    /*
    MANAGE_TRACK_NAMES displays the name of the track as soon as the
    corresponding GPX file. 
    It also manage the call to remove a track and renaming.
    */
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
            span_name.setAttribute('data-index', i);
            span_name.setAttribute('data-original_name', span_name.innerHTML);

            span_name.addEventListener('blur', function() {
                console.log('Change track name ',
                             parseInt(span_name.getAttribute('data-index')),
                             span_name.innerHTML);

                fetch('/editor/rename_segment', {
                    method: 'POST',
                    body: JSON.stringify({
                        index:  parseInt(span_name.getAttribute('data-index')),
                        new_name: span_name.innerHTML
                    })
                });
                // TODO use the data-original_name if response is not OK

            });

            button_remove.setAttribute('class', 'btn-close');
            button_remove.setAttribute('type', 'button');
            button_remove.setAttribute('aria-label', 'Close');
            button_remove.style = 'font-size: 18px; vertical-align: -3px; margin-left: 20px;';
            button_remove.setAttribute('data-index', i);

            button_remove.addEventListener('click', function() {
                console.log('Remove track ', i);
                p_name.style.display = 'none';

                fetch('/editor/remove_segment', {
                    method: 'POST',
                    body: JSON.stringify({
                        index:  parseInt(button_remove.getAttribute('data-index')) + 1  // segments start to count in 1, not 0
                    })
                });
                // TODO reverse the display='none' if response is NOK
                // TODO remove segment plot
            });

            p_name.appendChild(span_marker);
            p_name.appendChild(span_name);
            p_name.appendChild(button_remove);
            div_track_list.appendChild(p_name);
        }
    }
}


function get_color(color_index, alpha='0.5') {
    /*
    GET_COLOR returns the rgb string corresponding to a number of predefined
    colors
    */
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


function create_map() {
    /*
    CREATE_MAP produces the basic map object when track layers will be
    displayed
    */
    let map = new ol.Map({
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

    return map;
}

function plot_segment(map, index) {
    /*
    PLOT_LAST_SEGMENT create the source layer
    Fetched data:
        - size: total number of elements in arrays lat/lon/ele
        - lat
        - lon
        - ele
        - map_center
        - map_zoom
        - index
    The API end point /editor/get_segment/<int:index> returns the information
    of each segment by index. When index=0 the last available segment is
    returned.
    */

    // Get data
    fetch(`/editor/get_segment/${index}`)
        .then(response => response.json())
        .then(data => {
            console.log('plot_segment', index);
            if (data.size === 0) {  // do nothing if no data
                console.log('plot_segment: size=0');
                return;
            }

            // Points to vector layer
            const points_vector_layer = new ol.layer.Vector({
                source: get_points_source(data.lat, data.lon),
                style: get_points_style(data.index - 1)
            });
            map.addLayer(points_vector_layer);

            // Lines to vector layer
            const lines_vector_layer = new ol.layer.Vector({
                source: get_lines_source(data.lat, data.lon),
                style: get_lines_style(data.index - 1)
            });
            map.addLayer(lines_vector_layer);

            // Adjust display
            map.getView().setZoom(data.map_zoom);
            map.getView().setCenter(ol.proj.fromLonLat(data.map_center));
        });
}

function get_points_source(lat, lon) {
    /*
    GET_POINTS_SOURCE generates a vector source with points of pairs
    latitude-longitude
    */

    // create points
    const features = [];
    for (i = 0; i < lat.length; i++) {
        features.push(new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.fromLonLat([
                lon[i], lat[i]
            ]))
        }));
    }

    // create the source and layer for features
    const vectorSource = new ol.source.Vector({
        features
    });

    return vectorSource;
}


function get_lines_source(lat, lon) {
    /*
    GET_LINES_SOURCE generates a vector source with a line joining pairs
    of coordinates latitude-longitude
    */

    // create points
    const points = [];
    for (i = 0; i < lat.length; i++) {
        points.push(ol.proj.fromLonLat([lon[i], lat[i]]));
    }

    const featureLine = new ol.Feature({
        geometry: new ol.geom.LineString(points)
    });

    // create the source and layer for features
    var lineSource = new ol.source.Vector({
        features: [featureLine]
    });

    return lineSource;
}


function get_points_style(color_index) {
    /*
    GET_POINTS_STYLE provides a style for points
    */
    const points_style = new ol.style.Style({
            image: new ol.style.Circle({
                fill: new ol.style.Fill({color: get_color(color_index)}),  // inner color
                radius: 3,  // circle radius
            }),
        });
    return points_style;
}


function get_lines_style(color_index) {
    /*
    GET_LINES_STYLE provides a style for lines
    */
    const line_style = new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: get_color(color_index),
                width: 5,
            })
        });
    return line_style;
}
