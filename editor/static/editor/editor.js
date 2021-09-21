var selected_segments = 0;
var selected_segment_idx;
var track;
var map;
var chart;

document.addEventListener('DOMContentLoaded', () => {
    map = create_map();
    chart = create_chart();  // elevation chart
    track = load_track();  // data load includes plotting
    submit_file();

    // manage_track_names();
    // show_summary();
    // save_session();
    // update_session_name();
    // download_session();
    // reverse_segment();
    // change_segments_order();
});

function activate_spinner(spinner_selector) {
    document.querySelector(spinner_selector).style.display = 'inline-block';
}

/**
* SUBMIT_FILE submit the file when it is selected, not when a submit button
* is clicked. A spinner is activated while the uploading.
*/
function submit_file() {
    document.querySelector('#select-file').onchange = function() {
        document.querySelector('form').submit();
        activate_spinner('#div_spinner');
    };
}

function load_track() {
    let track_data;
    fetch('/editor/get_track')
        .then(response => response.json())
        .then(data => {
            track_data = data;
            console.log('track_data', track_data);

            // Plot track
            track_data['segments'].forEach(seg => plot_segment(seg));
            track_data['links_coor'].forEach(link => plot_link_coor(link));
            // track_data['links_ele'].forEach(link => plot_link_ele(link));

            if (typeof track_data.map_zoom !== 'undefined') {
                map.getView().setZoom(track_data.map_zoom);
            }
            if (typeof track_data.map_center !== 'undefined') {
                map.getView().setCenter(ol.proj.fromLonLat(track_data.map_center));
            }

        });

    return track_data;
}


function manage_track_names() {
    /*
    MANAGE_TRACK_NAMES displays the name of the track as soon as the
    corresponding GPX file.
    It also manage the call to remove a track and renaming.
    */
    let div_track_list = document.querySelector('#div_track_list');
    let track_list = JSON.parse(div_track_list.dataset.track_list.replace(/'/g, '"'));
    let segment_list = JSON.parse(div_track_list.dataset.segment_list.replace(/'/g, '"'));
    div_track_list.innerHTML = '';

    if (typeof track_list !== 'undefined') {
        for (let i = 0; i < track_list.length; i++) {
            let segment_idx = segment_list[i];
            let color = get_color(segment_idx, '-1');

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
            span_name.setAttribute('id', `span_rename_${segment_idx}`);
            span_name.setAttribute('class', 'span_rename');
            span_name.setAttribute('data-segment_idx', segment_idx);
            console.log('track id:', `span_rename_${segment_idx}`);

            span_name.addEventListener('blur', function() {
                console.log('Change track name',
                             `segment id: ${1 + parseInt(span_name.getAttribute('data-index'))}\n`,
                             `old_name: ${span_name.getAttribute('data-original_name')}\n`,
                             `new_name: ${span_name.innerHTML}`);
                let new_name = span_name.innerHTML;
                let index = parseInt(span_name.getAttribute('data-index'));
                fetch(`/editor/rename_segment/${index}/${new_name}`, {
                    method: 'POST',
                });
                // TODO use the data-original_name if response is not OK
            });

            button_remove.setAttribute('class', 'btn-close');
            button_remove.setAttribute('type', 'button');
            button_remove.setAttribute('aria-label', 'Close');
            button_remove.style = 'font-size: 18px; vertical-align: -3px; margin-left: 20px;';
            button_remove.setAttribute('data-index', segment_idx);
            button_remove.setAttribute('id', `btn_remove_${segment_idx}`);

            button_remove.addEventListener('click', function() {
                // Remove track name from list
                p_name.style.display = 'none';
                span_name.style.display = 'none';

                // Remove layer
                console.log(`Remove track with index: ${segment_idx}`);
                const layersToRemove = [];
                map.getLayers().forEach(layer => {
                    if ((layer.get('name') === `layer_points_${segment_idx}`) ||
                        (layer.get('name') === `layer_lines_${segment_idx}`) ||
                        (layer.get('name') === 'layer_link')) {
                            layersToRemove.push(layer);
                        }
                });

                const len = layersToRemove.length;
                for(let j = 0; j < len; j++) {
                    let layer_name = layersToRemove[j].get('name');
                    console.log(`Removing layer ${layer_name}`);
                    map.removeLayer(layersToRemove[j]);
                }

                // Remove elevation
                let remove_elevation_index;
                canvas.data.datasets.forEach((dataset, canvas_index) => {
                    if (dataset.label === `elevation_${segment_idx}`) {
                        remove_elevation_index = canvas_index;
                    }
                });

                if (remove_elevation_index) {
                    canvas.data.datasets.splice(remove_elevation_index, 1);
                }
                else if (canvas.data.datasets.length === 1){
                    canvas.data.datasets = [];
                }
                canvas.update();

                // Remove segment in back end
                fetch(`/editor/remove_segment/${segment_idx}`, {
                    method: 'POST',
                })
                .then( _ => {
                    fetch('/editor/get_segments_links')
                    .then(response => response.json())
                    .then(data => {
                        let links = JSON.parse(data.links);
                        links.forEach(link => plot_link(map, link));
                    });
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
    if (color_index < 0) {
        color_index = 0;
    }
    else {
        color_index = color_index - 1;  // indexing from 1
    }

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
    return new ol.Map({
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

function plot_segment(segment) {
    // Plot elevation
    let elevation_data = [];
    segment.distance.forEach((distance, index) => {
        let elevation = segment.ele[index];
        elevation_data.push({x: distance, y: elevation});
    });

    chart.data.datasets.push({
        label: `elevation_${segment.index}`,
        fill: true,
        lineTension: 0.4,
        data: elevation_data,
        showLine: true,
        borderWidth: 3,
        backgroundColor: get_color(segment.index, '0.2'),
        borderColor: get_color(segment.index, '0.8'),
        hidden: false,
    });
    chart.update();

    // Points to vector layer
    const points_vector_layer = new ol.layer.Vector({
        source: get_points_source(segment.lat, segment.lon),
        style: get_points_style(segment.index),
        name: `layer_points_${segment.index}`,
    });
    map.addLayer(points_vector_layer);
    console.log(`New layer: ${points_vector_layer.get('name')}`);

    // Lines to vector layer
    const lines_vector_layer = new ol.layer.Vector({
        source: get_lines_source(segment.lat, segment.lon,
                                 `features_lines_${segment.index}`,
                                 get_lines_style(segment.index)),
        name: `layer_lines_${segment.index}`,
    });
    map.addLayer(lines_vector_layer);
    console.log(`New layer: ${lines_vector_layer.get('name')}`);

    // Interaction
    let select_interaction = new ol.interaction.Select({
        layers: [lines_vector_layer]
    });
    map.addInteraction(select_interaction);

    select_interaction.on('select', function (e) {
        console.log('(de)select');
        document.querySelector(`#span_rename_${segment.index}`).style.fontWeight = 'normal';
        if (e.selected.length > 0) {
            if (e.selected[0].getId() === `features_lines_${segment.index}`) {
                console.log('selected line:', e.selected[0].getId());
                console.log('data index:', segment.index);
                e.selected[0].setStyle(new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: get_color(segment.index, '0.9'),
                        width: 7,
                    })
                }));
                // Bold track name
                document.querySelector(`#span_rename_${segment.index}`).style.fontWeight = 'bolder';

            }
            elevation_show_segment(segment.index);
            selected_segment_idx = segment.index;
            selected_segments++;
        }
        else {
            console.log('deselect');
            elevation_show_segment(undefined, true);
            selected_segment_idx = undefined;
            selected_segments--;
        }

    });

}


function get_points_source(lat, lon) {
    /*
    GET_POINTS_SOURCE generates a vector source with points of pairs
    latitude-longitude
    */

    // create points
    const features = [];
    for (let i = 0; i < lat.length; i++) {
        features.push(new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.fromLonLat([
                lon[i], lat[i]
            ]))
        }));
    }

    // create the source and layer for features
    return new ol.source.Vector({
        features
    });
}


function get_lines_source(lat, lon, id, style) {
    /*
    GET_LINES_SOURCE generates a vector source with a line joining pairs
    of coordinates latitude-longitude
    */

    // create points
    const points = [];
    for (let i = 0; i < lat.length; i++) {
        points.push(ol.proj.fromLonLat([lon[i], lat[i]]));
    }

    const featureLine = new ol.Feature({
        geometry: new ol.geom.LineString(points)
    });
    featureLine.setId(id);
    featureLine.setStyle(style);

    // create the source and layer for features
    return new ol.source.Vector({
        features: [featureLine]
    });
}


function get_points_style(color_index) {
    /*
    GET_POINTS_STYLE provides a style for points
    */
    return new ol.style.Style({
        image: new ol.style.Circle({
            fill: new ol.style.Fill({color: get_color(color_index)}),  // inner color
            radius: 3,  // circle radius
        }),
    });
}


function get_lines_style(color_index, alpha) {
    /*
    GET_LINES_STYLE provides a style for lines
    */
    return new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: get_color(color_index, alpha),
            width: 5,
        })
    });
}

function plot_link_coor(link) {
    const link_vector_layer = new ol.layer.Vector({
        source: get_links_source(link['from_coor'], link['to_coor']),
        style: get_link_style(),
        name: `layer_link_${link['from']}_${link['to']}`,
    });
    map.addLayer(link_vector_layer);
}


function get_links_source(from, to) {
    // create points
    const points = [];
    points.push(ol.proj.fromLonLat([from['lon'], from['lat']]));
    points.push(ol.proj.fromLonLat([to['lon'], to['lat']]));

    const featureLink = new ol.Feature({
        geometry: new ol.geom.LineString(points)
    });

    // create the source and layer for features
    return new ol.source.Vector({
        features: [featureLink]
    });
}


function get_link_style() {
    return new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: 'rgb(0, 0, 128, 0.1)',  // navy color
            width: 3,
        })
    });
}


function show_summary() {
    /*
    SHOW_SUMMARY display on a modal box overall information of each segment
    and the full track.
    */

    // Get elements
    const modal = document.getElementById("div_summary_modal");
    const btn = document.getElementById("btn_summary");
    const span = document.getElementById("close_summary");
    const summary_content = document.getElementById("div_summary_content");

    // When the user clicks on <span> (x), close the modal
    span.onclick = function() {
      modal.style.display = "none";
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
      if (event.target == modal) {
        modal.style.display = "none";
      }
    }

    // When the user clicks on the button, open the modal
    btn.onclick = function() {
      modal.style.display = "block";
      summary_content.innerHTML = '';

        // Table definition
        const table = document.createElement('table');
        table.setAttribute('class', 'table');
        const tblHead = document.createElement('thead');
        const tblBody = document.createElement('tbody');

        // Fill header
        let row = document.createElement("tr");
        ['Track Name', 'Distance', 'Uphill', 'Downhill'].forEach(element => {
            let cell = document.createElement("th");
            cell.innerHTML = element;
            row.appendChild(cell);
        });
        tblHead.appendChild(row);
        table.appendChild(tblHead);

        // Fill body
        fetch('/editor/get_summary')
            .then(response => response.json())
            .then(data => {
                let summary = data['summary'];

                Object.getOwnPropertyNames(summary).forEach( file => {
                    let row = document.createElement("tr");
                    ['file', 'distance', 'uphill', 'downhill'].forEach(element => {
                        let cell = document.createElement("td");
                        if (element === 'file'){
                            if (file === 'total') {
                                cell.innerHTML = '<b>TOTAL</b>';
                            }
                            else {
                                cell.innerHTML = file;
                            }
                        }
                        else {
                            cell.innerHTML = summary[file][element];
                        }
                        row.appendChild(cell);
                    })
                    tblBody.appendChild(row);
                })
                table.appendChild(tblBody);
                summary_content.appendChild(table);
            })
        // TODO manage errors

    }

}

function save_session() {
    /*
    SAVE_SESSION save the current track object in backend when clicking the
    save button
    */
    let btn_save = document.getElementById('btn_save');

    btn_save.addEventListener('click', function() {
        document.querySelector('#div_spinner').style.display = 'inline-block';
        fetch('/editor/save_session', {
            method: 'POST',
        })
        .then(response => {
            document.querySelector('#div_spinner').style.display = 'none';

            let div = document.getElementById('div_alerts_box');
            if (response.status === 201){
                div.innerHTML = '<div class="alert alert-success" role="alert">Session has been saved</div>';
            }
            else if (response.status === 491){
                div.innerHTML = '<div class="alert alert-warning" role="alert">No track is loaded</div>';
            }
            else if (response.status === 492){
                div.innerHTML = '<div class="alert alert-danger" role="alert">Unexpected error. Code: 492</div>';
            }
            else {
                div.innerHTML = '<div class="alert alert-danger" role="alert">Unexpected error. Unable to save</div>';
            }

            setTimeout(function(){
                div.innerHTML = '';
            }, 3000);

        })
    });
}

function update_session_name() {
    let e_title = document.querySelector('#h_session_name');

    e_title.addEventListener('blur', function() {
        let new_name = e_title.innerHTML;
        fetch(`/editor/rename_session/${new_name}`, {
            method: 'POST',
        })
        .then(response => console.log(response));
    });
    // TODO manage error
}


function download(url, filename) {
    fetch(url).then(function(t) {
        return t.blob().then((b)=>{
            var a = document.createElement("a");
            a.href = URL.createObjectURL(b);
            a.setAttribute("download", filename);
            a.click();
        }
        );
    });
}

function download_session() {
    let btn_download = document.querySelector('#btn_download');

    btn_download.addEventListener('click', function() {
        document.querySelector('#div_spinner').style.display = 'inline-block';

        fetch('/editor/download_session', {
            method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                document.querySelector('#div_spinner').style.display = 'none';

                if (data.hasOwnProperty('error')) {  // manage error
                    let div_error = document.querySelector('#div_error_msg');
                    div_error.innerHTML = data.error;
                    div_error.style.display = 'inline-block';

                    setTimeout(function() {
                        div_error.innerHTML = '';
                        div_error.style.display = 'none';
                    }, 3000);

                }
                else if (data.hasOwnProperty('url')) {
                    download(data.url, data.filename);
                }
            });
    });

}


function reverse_segment() {
    let btn_reverse = document.getElementById('btn_reverse');
    btn_reverse.addEventListener('click', () => {
        document.querySelector('#div_spinner').style.display = 'inline-block';
        let segment_idx;
        if (check_reverse_button()) {
            segment_idx = selected_segment_idx;
        }
        else {
            return false;
        }
        console.log('reverse', segment_idx);

        // Remove segment in back end
        fetch(`/editor/reverse_segment/${segment_idx}`, {
            method: 'POST',
        })
        .then( response => {
            document.querySelector('#div_spinner').style.display = 'inline-block';

            // Reverse elevation
            canvas.data.datasets.forEach((dataset, canvas_index) => {
                if (dataset.label === `elevation_${segment_idx}`) {
                    console.log('reverse-elevation', `elevation_${segment_idx}`, dataset.label);
                    let reversed_data = [];
                    let size = dataset.data.length;
                    for (let i = 0; i < size; i++){
                        reversed_data.push({x: dataset.data[i].x, y: dataset.data[size - i - 1].y});
                    }
                    console.log('reverse-elevation DONE');
                    dataset.data = reversed_data;
                }
            });
            canvas.update();

            // Remove existing links
            let layersToRemove = [];
            map.getLayers().forEach(layer => {
                if (layer.get('name') === 'layer_link') {
                        layersToRemove.push(layer);
                    }
            });

            let len = layersToRemove.length;
            for(let j = 0; j < len; j++) {
                let layer_name = layersToRemove[j].get('name');
                console.log(`Removing layer ${layer_name}`);
                map.removeLayer(layersToRemove[j]);
            }

            if (response.status === 200){  // redo links
                fetch('/editor/get_segments_links')
                .then(response => response.json())
                .then(data => {
                    // Re-do links
                    let links = JSON.parse(data.links);
                    links.forEach(link => plot_link(map, link));
                });
            }
            else {
                let div = document.getElementById('div_alerts_box');
                if (response.status === 501){
                    div.innerHTML = '<div class="alert alert-warning" role="alert">Unable to reverse this segment.</div>';
                }
                else if (response.status === 500){
                    div.innerHTML = '<div class="alert alert-danger" role="alert">No available track</div>';
                }
                else {
                    div.innerHTML = '<div class="alert alert-danger" role="alert">Unexpected error. Unable to save</div>';
                }

                document.querySelector('#div_spinner').style.display = 'none';
                setTimeout(function(){
                    div.innerHTML = '';
                }, 3000);
            }
        })
        .then( _ => {
            document.querySelector('#div_spinner').style.display = 'none';
        });
    });
}


function check_reverse_button() {
    let btn_reverse = document.getElementById('btn_reverse');
    btn_reverse.addEventListener('click', () => {
        if (selected_segments === 0) {
                let div = document.getElementById('div_alerts_box');
                div.innerHTML = '<div class="alert alert-warning" role="alert">No track has been selected</div>';
                div.style.display = 'inline-block';

                setTimeout(function(){
                    div.style.display = 'none';
                    div.innerHTML = '';
                }, 3000);

                return false;  // TODO: is this returned after 3s?
        }
    });

    return true;
}


function change_segments_order() {
    const modal = document.getElementById("div_change_order_modal");
    const btn = document.getElementById("btn_change_order");
    const btn_cancel = document.getElementById("btn_change_order_cancel");
    const btn_ok = document.getElementById("btn_change_order_ok");
    const span = document.getElementById("close_change_order");
    const change_order_content = document.getElementById("div_change_order");

    // When the user clicks on <span> (x), close the modal
    span.onclick = function() {
      modal.style.display = "none";
    }

    // When the user clicks cancel, close the modal
    btn_cancel.onclick = function() {
      modal.style.display = "none";
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = (event) => {
      if (event.target == modal) {
        modal.style.display = "none";
      }
    }

    // When the user clicks on the button, open the modal
    btn.onclick = function() {
        let segments = document.getElementsByClassName('span_rename');
        const get_number_segments = () => {
            let number_segments = 0;
            Array.prototype.forEach.call(segments, el => {
                if (el.style.display !== 'none'){
                    number_segments++;
                }
            });
            return number_segments;
        };

        if (get_number_segments() === 0){
            let div = document.getElementById('div_alerts_box');
            div.innerHTML = '<div class="alert alert-warning" role="alert">No segment is loaded </div>';
            setTimeout(function(){
                div.innerHTML = '';
            }, 3000);
            return;
        }
        else if (get_number_segments() === 1){
            let div = document.getElementById('div_alerts_box');
            div.innerHTML = '<div class="alert alert-warning" role="alert">One single segment is loaded. At least two are required to modify order.</div>';
            setTimeout(function(){
                div.innerHTML = '';
            }, 3000);
            return;
        }
        else {
            modal.style.display = "block";
            change_order_content.innerHTML = '';
        }

        Array.prototype.forEach.call(segments, el => {
            if (el.style.display !== 'none'){
                let color = get_color(el.dataset.segment_idx, '-1');

                console.log(el.innerHTML, el.dataset.segment_idx, el.style.display);

                const div_segment = document.createElement('div');
                const span_name = document.createElement('span');
                const span_marker = document.createElement('span');
                const span_hover = document.createElement('span');
                const i = document.createElement('i');

                div_segment.setAttribute('class', 'item draggable-item draggable-segment');
                div_segment.setAttribute('data-segment_idx', el.dataset.segment_idx);

                span_marker.innerHTML = '&#9899';
                span_marker.style = `font-size: 20px; color: transparent;  text-shadow: 0 0 0 ${color};`;

                span_name.style = 'font-size: 18px; margin-left: 5px;';
                span_name.innerHTML = el.innerHTML;

                span_hover.innerHTML = '&#8286&#8286 ';
                span_hover.style = 'font-size: 20px; margin-left:15px;';

                i.setAttribute('class', 'fas fa-bars');

                div_segment.appendChild(span_hover);
                div_segment.appendChild(span_marker);
                div_segment.appendChild(span_name);
                div_segment.appendChild(i);
                change_order_content.appendChild(div_segment);
            }
        });
    }

    // Accept the new order
    btn_ok.onclick = function() {
        let segments = document.getElementsByClassName('draggable-segment');
        let new_order = [];
        document.querySelector('#div_spinner_change_order').style.display = 'inline-block';

        Array.prototype.forEach.call(segments, el => {
            new_order.push(parseInt(el.dataset.segment_idx));
        });

        fetch('/editor/change_segments_order', {
            method: 'POST',
            body: JSON.stringify({
                new_order:  new_order,
            })
        })
        .then(response => {
            document.querySelector('#div_spinner_change_order').style.display = 'none';

            let div = document.getElementById('div_alerts_box');
            if (response.status === 520){
                div.innerHTML = '<div class="alert alert-danger" role="alert">No track is loaded</div>';
                setTimeout(function(){
                    div.innerHTML = '';
                }, 3000);
                modal.style.display = "none";
                return;
            }
            else if (response.status === 532){
                div.innerHTML = '<div class="alert alert-danger" role="alert">Unexpected error. Code: 532</div>';
                setTimeout(function(){
                    div.innerHTML = '';
                }, 3000);
                modal.style.display = "none";
                return;
            }
            else if (response.status === 200){
                document.getElementById('a_refresh_editor').click();
            }

        });

    }

}


function create_chart() {
    return new Chart("js-elevation", {
       type: "scatter",
       data: {},
       options: {
           responsive: true,
           maintainAspectRatio: false,
           plugins: {
               legend: {
                   display: false
               },
               tooltips: {
                   enabled: false
               },
           },
           scales: {
               x: {
                   ticks: {
                       callback: (value) => {
                           return value + ' km';
                       }
                   }
               },
               y: {
                   ticks: {
                       callback: (value) => {
                           return value + ' m';
                       }
                   }
               },
           }
       }
   });
}


function elevation_show_segment(index=undefined, all=false) {
    console.log('all', all);
    canvas.data.datasets.forEach((dataset, canvas_index) => {
        console.log('all-forEach', all);
        if (all) {
            dataset.hidden = false;
        }
        else if (typeof index !== 'undefined') {
            dataset.hidden = true;
            if (dataset.label === `elevation_${index}`) {
                dataset.hidden = false;
            }
        }
        else {
            return false;
        }
    });
    canvas.update();
    return true;
}
