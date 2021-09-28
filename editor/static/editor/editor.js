let selected_segments = 0;
let selected_segment_idx;
let track;
let map;
let chart;


document.addEventListener('DOMContentLoaded', async () => {
    track = await load_track();
    map = create_map();
    chart = create_chart();  // elevation chart
    submit_file();
    plot_track();
    segments_manager();
    show_summary();
    save_session();
    update_session_name();
    download_session();
    reverse_segment();
    change_segments_order();
});

function activate_spinner(spinner_selector) {
    document.querySelector(spinner_selector).style.display = 'inline-block';
}

function deactivate_spinner(spinner_selector) {
    document.querySelector(spinner_selector).style.display = 'none';
}


function submit_file() {
    /* Submit the file when it is selected, not when a submit button
    * is clicked. */
    document.querySelector('#select-file').onchange = () => {
        document.querySelector('form').submit();
        activate_spinner('#div_spinner');
    };
}

async function load_track() {
    try {
        const response = await fetch('/editor/get_track');
        return await response.json();
    } catch (error) {
        display_error('error', error);
    }
}

function plot_track() {
    // Plot track
    track['segments'].forEach(seg => plot_segment(seg));
    track['links_coor'].forEach(link => plot_link_coor(link));
    track['links_ele'].forEach(link => plot_link_ele(link));

    if (typeof track.map_zoom !== 'undefined') {
        map.getView().setZoom(track.map_zoom);
    }
    if (typeof track.map_center !== 'undefined') {
        map.getView().setCenter(ol.proj.fromLonLat(track.map_center));
    }
}

function segments_manager() {
    track['segments'].forEach(seg => manage_segment(seg));
}


function manage_segment(segment) {
    let color = get_color(segment.index, '-1');
    const p_name = document.createElement('p');
    const span_name = document.createElement('span');
    const span_marker = document.createElement('span');
    const button_remove = document.createElement('button');

    // Define the circle marker
    span_marker.innerHTML = '&#9899';
    span_marker.style = `font-size: 20px; color: transparent;  text-shadow: 0 0 0 ${color};`;

    // Define paragraph
    p_name.setAttribute('class', 'segment-list-item');
    p_name.setAttribute('id', `segment-list-item-${segment.index}`);

    // Define editable track name
    span_name.innerHTML = segment.name;
    span_name.style = 'font-size: 18px; margin-left: 5px;';
    span_name.setAttribute('contenteditable', 'true');
    span_name.setAttribute('data-index', segment.index);
    span_name.setAttribute('data-original_name', span_name.innerHTML);
    span_name.setAttribute('id', `span_rename_${segment.index}`);
    span_name.setAttribute('class', 'span_rename');
    span_name.setAttribute('data-segment_idx', segment.index);

    // Define remove segment button
    button_remove.style = 'font-size: 18px; vertical-align: -3px; margin-left: 20px;';
    button_remove.setAttribute('class', 'btn-close');
    button_remove.setAttribute('type', 'button');
    button_remove.setAttribute('aria-label', 'Close');
    button_remove.setAttribute('data-index', segment.index);
    button_remove.setAttribute('id', `btn_remove_${segment.index}`);

    // Rename segment listener
    span_name.addEventListener('blur', () => {
        let new_name = span_name.innerHTML;
        fetch(`/editor/rename_segment/${segment.index}/${new_name}`, {
             method: 'POST',
        });
    });

    // Remove segment listener
    button_remove.addEventListener('click', () => {
        remove_segment(segment.index, {'p_name': p_name, 'span_name': span_name})
    });

    // Add new elements to html div
    let div_track_list = document.querySelector('#div_track_list');
    p_name.appendChild(span_marker);
    p_name.appendChild(span_name);
    p_name.appendChild(button_remove);
    div_track_list.appendChild(p_name);
}


function remove_segment(segment_index, list) {
    activate_spinner('#div_spinner');

    // remove from list
    list.p_name.style.display = 'none';
    list.span_name.style.display = 'none';

    remove_elevation(segment_index);

    remove_map(segment_index);

    remove_segment_from_track(segment_index);

    relink_map(segment_index);

    // Remove segment in back end
    fetch(`/editor/remove_segment/${segment_index}`, {
        method: 'POST',
    }).then( response => {
        if (response.status !== 201) {
            throw new Error(`Server error by ${response.status} when removing segment.`);
        }
    }).then(() =>
        update_distance()
    ).then(() => {
        // Remove elevation plots and links
        chart.data.datasets = [];
        chart.update();
        track.links_ele = [];
    }).then( () => {
        // Update links
        for (let i = 0; i < track.segments.length - 1; i++) {
            let current_segment = track.segments[i];
            let next_segment = track.segments[i + 1];

            track.links_ele.push(
                {'from': current_segment.index,
                    'to': next_segment.index,
                    'from_ele': {'x': current_segment.distance[current_segment.distance.length - 1],
                        'y': current_segment.ele[current_segment.ele.length - 1]},
                    'to_ele': {'x': next_segment.distance[0],
                        'y': next_segment.ele[0]}
                });
        }
    }).then(() => {
        // Plot new elevation
        track['segments'].forEach(seg => plot_elevation(seg));
        track['links_ele'].forEach(link => plot_link_ele(link));
        deactivate_spinner('#div_spinner');
    }).catch( error => {
        display_error('error', error);
        deactivate_spinner('#div_spinner');
    });
}

function remove_map(segment_index) {
    let layersToRemove = [];
    map.getLayers().forEach(layer => {
        let layer_name = layer.get('name');

        if (typeof layer_name !== 'undefined') {
            if ((layer_name === `layer_points_${segment_index}`) ||
                (layer_name === `layer_lines_${segment_index}`) ||
                (RegExp(`^layer_link_\\d+_${segment_index}$`).test(layer_name)) ||
                (RegExp(`^layer_link_${segment_index}_\\d+$`).test(layer_name)) ) {
                layersToRemove.push(layer);
            }
        }
    });

    const len = layersToRemove.length;
    for(let j = 0; j < len; j++) {
        map.removeLayer(layersToRemove[j]);
    }
}

function remove_elevation(segment_index) {
    let chartIndexToRemove = [];
    chart.data.datasets.forEach((dataset, canvas_index) => {
        let label = dataset.label;

        if (typeof label !== 'undefined') {
            if ((label === `elevation_${segment_index}`) ||
                (RegExp(`^link_\\d+_${segment_index}$`).test(label)) ||
                (RegExp(`^link_${segment_index}_\\d+$`).test(label))) {
                chartIndexToRemove.push(canvas_index);
            }
        }
    });

    // reverse is needed since array of size changes in each iteration
    let chartIndexToRemoveReversed = chartIndexToRemove.reverse();
    chartIndexToRemoveReversed.forEach(idx => {
        // reverse is needed since array of size changes in each iteration
        chart.data.datasets.splice(idx, 1);
    });
    chart.update();
}

function remove_map_link(segment_index) {
    let layersToRemove = [];
    map.getLayers().forEach(layer => {
        let layer_name = layer.get('name');

        if (typeof layer_name !== 'undefined') {
            if ((RegExp(`^layer_link_\\d+_${segment_index}$`).test(layer_name)) ||
                (RegExp(`^layer_link_${segment_index}_\\d+$`).test(layer_name)) ) {
                layersToRemove.push(layer);
            }
        }
    });

    const len = layersToRemove.length;
    for(let j = 0; j < len; j++) {
        map.removeLayer(layersToRemove[j]);
    }
}

function remove_ele_link(segment_index) {
    let chartIndexToRemove = [];
    chart.data.datasets.forEach((dataset, canvas_index) => {
        let label = dataset.label;

        if (typeof label !== 'undefined') {
            if ((RegExp(`^link_\\d+_${segment_index}$`).test(label)) ||
                (RegExp(`^link_${segment_index}_\\d+$`).test(label))) {
                chartIndexToRemove.push(canvas_index);
            }
        }
    });

    // reverse is needed since array of size changes in each iteration
    let chartIndexToRemoveReversed = chartIndexToRemove.reverse();
    chartIndexToRemoveReversed.forEach(idx => {
        chart.data.datasets.splice(idx, 1);
    });
    chart.update();
}

function remove_segment_from_track(segment_index) {
    // The segment is removed in the track structure
    let segment_track_index;
    for (let i = 0; i < track['segments'].length; i++) {
        let segment = track['segments'][i];
        if (segment['index'] === segment_index) {
            segment_track_index = i;
            break;
        }
    }
    track['segments'].splice(segment_track_index, 1);
}

function relink_map(segment_index) {
    let from = {'coor': undefined, 'segment_index': undefined, 'link_index': undefined};
    let to = {'coor': undefined, 'segment_index': undefined, 'link_index': undefined};

    for (const [i, link] of track['links_coor'].entries()) {
        if (link.from === segment_index) {
            to.coor = link['to_coor'];
            to.segment_index = link['to'];
            to.link_index = i;
        }
        else if (link.to === segment_index) {
            from.coor = link['from_coor'];
            from.segment_index = link['from'];
            from.link_index = i;
        }
    }

    if ((typeof from.coor !== 'undefined') && (typeof to.coor !== 'undefined')){
        // segment is in the middle
        track['links_coor'].splice(from.link_index, 1);
        track['links_coor'].splice(to.link_index, 1);
        const new_link = {'from': from.segment_index,
                          'to': to.segment_index,
                          'from_coor': from.coor,
                          'to_coor': to.coor}
        track['links_coor'].push(new_link);
        plot_link_coor(new_link);
    }
    else if ((typeof from.coor === 'undefined') && (typeof to.coor !== 'undefined')){
        // segment is at the end
        track['links_coor'].splice(from.link_index, 1);
    }
    else if ((typeof from.coor !== 'undefined') && (typeof to.coor === 'undefined')){
        // segment is at the start
        track['links_coor'].splice(to.link_index, 1);
    }

}

function relink_elevation(segment_index) {
    let from = {'distance': undefined, 'elevation': undefined, 'segment_index': undefined, 'link_index': undefined};
    let to = {'distance': undefined, 'elevation': undefined, 'segment_index': undefined, 'link_index': undefined};

    for (const [i, link] of track['links_ele'].entries()) {
        if (link.from === segment_index) {
            to.distance = link['to_ele']['x'];
            to.elevation = link['to_ele']['y'];
            to.segment_index = link['to'];
            to.link_index = i;
        }
        else if (link.to === segment_index) {
            from.distance = link['from_ele']['x'];
            from.elevation = link['from_ele']['y'];
            from.segment_index = link['from'];
            from.link_index = i;
        }
    }

    if ((typeof from.elevation !== 'undefined') && (typeof to.elevation !== 'undefined')){
        // segment is in the middle
        track['links_ele'].splice(from.link_index, 1);
        track['links_ele'].splice(to.link_index, 1);
        const new_link = {'from': from.segment_index,
                          'to': to.segment_index,
                          'from_ele': {'x': from.distance, 'y': from.elevation},
                          'to_ele': {'x': to.distance, 'y': to.elevation}}
        track['links_ele'].push(new_link);
        plot_link_ele(new_link);
    }
    else if ((typeof from.elevation === 'undefined') && (typeof to.elevation !== 'undefined')){
        // segment is at the end
        track['links_ele'].splice(from.link_index, 1);
    }
    else if ((typeof from.elevation !== 'undefined') && (typeof to.elevation === 'undefined')){
        // segment is at the start
        track['links_ele'].splice(to.link_index, 1);
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

function plot_elevation(segment) {
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
}

function plot_segment(segment) {
    plot_elevation(segment);

    // Points to vector layer
    const points_vector_layer = new ol.layer.Vector({
        source: get_points_source(segment.lat, segment.lon),
        style: get_points_style(segment.index),
        name: `layer_points_${segment.index}`,
    });
    map.addLayer(points_vector_layer);

    // Lines to vector layer
    const lines_vector_layer = new ol.layer.Vector({
        source: get_lines_source(segment.lat, segment.lon,
                                 `features_lines_${segment.index}`,
                                 get_lines_style(segment.index)),
        name: `layer_lines_${segment.index}`,
    });
    map.addLayer(lines_vector_layer);

    // Interaction
    let select_interaction = new ol.interaction.Select({
        layers: [lines_vector_layer]
    });
    map.addInteraction(select_interaction);

    select_interaction.on('select',  e => {
        document.querySelector(`#span_rename_${segment.index}`).style.fontWeight = 'normal';
        if (e.selected.length > 0) {
            if (e.selected[0].getId() === `features_lines_${segment.index}`) {
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


function plot_link_ele(link) {
    let link_data = [link['from_ele'], link['to_ele']];
    chart.data.datasets.push({
        label: `link_${link.from}_${link.to}`,
        fill: true,
        data: link_data,
        showLine: true,
        borderWidth: 3,
        backgroundColor: 'rgb(0, 0, 128, 0.05)',
        borderColor: 'rgb(0, 0, 128, 0.1)',
        hidden: false,
        pointRadius: 0,
    });

    chart.update();
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
    const close_modal = () => {
        modal.style.display = "none";
        deactivate_spinner('#div_spinner_summary');
    }
    // When the user clicks on <span> (x), close the modal
    span.onclick = () => {
        close_modal();
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = (event) => {
        if (event.target === modal) {
            close_modal();
        }
    }

    // When the user clicks on the button, open the modal
    btn.onclick = () => {
        modal.style.display = "block";
        summary_content.innerHTML = '';
        activate_spinner('#div_spinner_summary');

        // Table definition
        const table = document.createElement('table');
        table.setAttribute('class', 'table');
        const tblHead = document.createElement('thead');
        const tblBody = document.createElement('tbody');

        // Fill header
        let hrow = document.createElement("tr");
        ['Track Name', 'Distance', 'Uphill', 'Downhill'].forEach(element => {
            let cell = document.createElement("th");
            cell.innerHTML = element;
            hrow.appendChild(cell);
        });
        tblHead.appendChild(hrow);
        table.appendChild(tblHead);

        // Fill body
        fetch('/editor/get_summary')
            .then(response => response.json())
            .then(data => {
                let summary = data['summary'];
                deactivate_spinner('#div_spinner_summary');

                Object.getOwnPropertyNames(summary).forEach( file => {
                    let brow = document.createElement("tr");
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
                        brow.appendChild(cell);
                    })
                    tblBody.appendChild(brow);
                })
                table.appendChild(tblBody);
                summary_content.appendChild(table);
            }).catch(error => {
            display_error('error', error);
            close_modal();
        });
    }

}

function save_session() {
    /*
    SAVE_SESSION save the current track object in backend when clicking the
    save button
    */
    let btn_save = document.getElementById('btn_save');

    btn_save.addEventListener('click', () => {
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

            setTimeout(() => {
                div.innerHTML = '';
            }, 3000);

        })
    });
}

function update_session_name() {
    let e_title = document.querySelector('#h_session_name');

    e_title.addEventListener('blur', () => {
        let new_name = e_title.innerHTML;
        fetch(`/editor/rename_session/${new_name}`, {
            method: 'POST',
        })
            .then(response => response_error_mng(response.status, 'update_session_name'))
            .catch(error => response_error_mng(-1, error));
    });
}


function download(url, filename) {
    fetch(url).then(t => {
        return t.blob().then((b)=>{
            let a = document.createElement("a");
            a.href = URL.createObjectURL(b);
            a.setAttribute("download", filename);
            a.click();
        })
            .catch(error => response_error_mng(-1, error));
    })
        .then(response => response_error_mng(response.status, 'download'))
        .catch(error => response_error_mng(-1, error));
}

function download_session() {
    let btn_download = document.querySelector('#btn_download');

    btn_download.addEventListener('click', () => {
        activate_spinner('#div_spinner');

        fetch('/editor/download_session', {
            method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                deactivate_spinner('#div_spinner');

                if (data.hasOwnProperty('error')) {
                    display_error('error', data.error);
                }
                else if (data.hasOwnProperty('url')) {
                    download(data.url, data.filename);
                }
            })
            .catch(error => response_error_mng(-1, error));

    });

}

function reverse_segment() {
    let btn_reverse = document.getElementById('btn_reverse');
    btn_reverse.addEventListener('click', () => {
        activate_spinner('#div_spinner');

        if (!check_reverse_button()){  // verify that one segment is selected
            return;
        }

        fetch(`/editor/reverse_segment/${selected_segment_idx}`, {
            method: 'POST',
        }).then( response => {
            if (response.status === 200) {
                reverse_elevation(selected_segment_idx);
                reverse_map_link(selected_segment_idx);
                reverse_ele_link(selected_segment_idx);
                deactivate_spinner('#div_spinner');
            }
            else {
                response_error_mng(response.status, 'reverse_segment');
                deactivate_spinner('#div_spinner');
            }
        }).catch(error => response_error_mng(-1, error));

    });
}

function reverse_elevation(segment_index) {
    chart.data.datasets.forEach(dataset => {
        if (dataset.label === `elevation_${segment_index}`) {
            let reversed_data = [];
            let size = dataset.data.length;
            for (let i = 0; i < size; i++){
                reversed_data.push({x: dataset.data[i].x, y: dataset.data[size - i - 1].y});
            }
            dataset.data = reversed_data;
        }
    });
    chart.update();
}

function get_segment(segment_index) {
    for (let segment of track['segments']) {
        if (segment['index'] === segment_index) {
            return segment;
        }
    }
}


function reverse_map_link(segment_index) {
    let segment = get_segment(segment_index);

    remove_map_link(segment_index);

    for (let link of track['links_coor']) {
        let end = segment['lon'].length - 1;

        if (link['from'] === segment_index) {
            // different reversing criteria to support multiple reverse
            if (segment['lon'][0] !== link['from_coor']['lon']) {
                link['from_coor'] = {
                    'lon': segment['lon'][0],
                    'lat': segment['lat'][0]
                };
            }
            else{
                link['from_coor'] = {
                    'lon': segment['lon'][end],
                    'lat': segment['lat'][end]
                };
            }
            plot_link_coor(link);
        }

        if (link['to'] === segment_index) {
            if (segment['lon'][end] !== link['to_coor']['lon']) {
                link['to_coor'] = {
                    'lon': segment['lon'][end],
                    'lat': segment['lat'][end]
                };
            }
            else {
                link['to_coor'] = {
                    'lon': segment['lon'][0],
                    'lat': segment['lat'][0]
                };
            }
            plot_link_coor(link);
        }
    }

}

function reverse_ele_link(segment_index) {
    let segment = get_segment(segment_index);

    remove_ele_link(segment_index);

    for (let link of track['links_ele']) {
        let end = segment['ele'].length - 1;

         if (link['from'] === segment_index) {
            // different reversing criteria to support multiple reverse
            if (segment['ele'][0] !== link['from_ele']['y']) {
                link['from_ele'] = {'x': segment['distance'][end],
                                    'y': segment['ele'][0]};
            }
            else{
                link['from_ele'] = {'x': segment['distance'][end],
                                    'y': segment['ele'][end]};
            }
            plot_link_ele(link);
        }

        if (link['to'] === segment_index) {
            if (segment['ele'][end] !== link['to_ele']['y']) {
                link['to_ele'] = {'x': segment['distance'][0],
                                  'y': segment['ele'][end]};
            }
            else {
                link['to_ele'] = {'x': segment['distance'][0],
                                  'y': segment['ele'][0]};
            }
            plot_link_ele(link);
        }
    }
}


function check_reverse_button() {
    let btn_reverse = document.getElementById('btn_reverse');
    btn_reverse.addEventListener('click', () => {
        if (selected_segments === 0) {
            display_error('warning', 'No track has been selected');
            return false;
        }
    });

    return true;
}


function display_error(severity, msg) {
    let div = document.getElementById('div_alerts_box');
    if (severity === 'error') {
        div.innerHTML = `<div class="alert alert-danger" role="alert">${msg}</div>`;
    }
    else if (severity === 'warning') {
        div.innerHTML = `<div class="alert alert-warning" role="alert">${msg}</div>`;
    }
    else {
        div.innerHTML = `<div class="alert alert-primary" role="alert">${msg}</div>`;
    }
    div.style.display = 'inline-block';

    setTimeout(() => {
        div.style.display = 'none';
        div.innerHTML = '';
    }, 3000);
}


function response_error_mng(status, fnc_name) {
    if (status !== 200) {
        if (status === 520) {
            display_error('error', 'No track is loaded');
        } else if ((status >= 500) && (status < 600)) {
            display_error('error', `Server error: ${status} (${fnc_name})`);
        } else {
            display_error('error', `Unexpected error: ${status} (${fnc_name})`);
        }
    }
}


function change_segments_order() {
    const modal = document.getElementById("div_change_order_modal");
    const btn = document.getElementById("btn_change_order");
    const btn_cancel = document.getElementById("btn_change_order_cancel");
    const btn_ok = document.getElementById("btn_change_order_ok");
    const span = document.getElementById("close_change_order");
    const change_order_content = document.getElementById("div_change_order");
    const close_modal = () => modal.style.display = "none";

    // When the user clicks on <span> (x), close the modal
    span.onclick = () => {
      close_modal();
    }

    // When the user clicks cancel, close the modal
    btn_cancel.onclick = () => {
      close_modal();
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = (event) => {
      if (event.target === modal) {
        close_modal();
      }
    }

    // When the user clicks on the button, open the modal
    btn.onclick = () => {
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
            display_error('warning', 'No segment is loaded');
            return;
        }
        else if (get_number_segments() === 1){
            display_error('warning', 'One single segment is loaded. At least two are required to modify order.');
            return;
        }
        else {
            modal.style.display = "block";
            change_order_content.innerHTML = '';
        }

        Array.prototype.forEach.call(segments, el => {
            if (el.style.display !== 'none'){
                let color = get_color(el.dataset.segment_idx, '-1');

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
    btn_ok.onclick = () => {
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
            deactivate_spinner('#div_spinner_change_order');

            if (response.status === 200) {
                // 1. Apply changes to track structure
                console.log('new_order', new_order);
                for (let i = 0; i < track.segments.length; i++) {
                    track.segments[i].index = new_order[i];
                }
                track.links_ele = [];
                track.links_coor = [];
                console.log('track after reorder', track);
            } else {
                close_modal();
                throw new Error(`Server error by ${response.status} by change segments order`);
            }
        }).then ( () => {
            // 2. Sort track by index
            track.segments = track.segments.sort((first, second) => {
                return first['index'] - second['index'];
            });
        }).then ( () => {
            // 3. Update distance for all segments
            update_distance();
        }).then( () => {
            // 4. Update links
            for (let i = 0; i < track.segments.length - 1; i++) {
                let current_segment = track.segments[i];
                let next_segment = track.segments[i + 1];

                track.links_coor.push(
                    {'from': current_segment.index,
                     'to': next_segment.index,
                     'from_coor': {'lon': current_segment.lon[current_segment.lon.length - 1],
                                  'lat': current_segment.lat[current_segment.lat.length - 1]},
                     'to_coor': {'lon': next_segment.lon[0],
                                'lat': next_segment.lat[0]}
                    })

                track.links_ele.push(
                    {'from': current_segment.index,
                     'to': next_segment.index,
                     'from_ele': {'x': current_segment.distance[current_segment.distance.length - 1],
                                  'y': current_segment.ele[current_segment.ele.length - 1]},
                     'to_ele': {'x': next_segment.distance[0],
                                'y': next_segment.ele[0]}
                    });
            }
        }).then( () => {
            // 5. Remove all plots (including links)
            chart.data.datasets = [];
            chart.update();

            track.segments.forEach(segment => {
                remove_map(segment.index);
                remove_elevation(segment.index);
                remove_map_link(segment.index);
                remove_ele_link(segment.index);
            });

            let segment_list_items = document.getElementsByClassName('segment-list-item');
            Array.from(segment_list_items).forEach(e => e.remove());

        }).then( () => {
            // 6. Redo all plots (including links)
            plot_track();
            segments_manager();

            close_modal();
        }).catch(error => {
            display_error('error', error);
            close_modal();
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
    chart.data.datasets.forEach(dataset => {
        if (all) {
            dataset.hidden = false;
        }
        else if (typeof index !== 'undefined') {
            dataset.hidden = dataset.label !== `elevation_${index}`;
        }
        else {
            return false;
        }
    });
    chart.update();
    return true;
}

function update_distance() {
    /* The cumulative distance provided from API can be altered when a segment
     * is removed or order is changed. So, it is needed to update it without
     * the need of an API call.
     * */
    track['segments'][0]['distance'] = track['segments'][0]['segment_distance'];

    for (let i = 1; i < track['segments'].length; i++) {
        let previous_segment = track['segments'][i - 1];
        let current_segment = track['segments'][i];
        let end = previous_segment.lat.length - 1;
        let distance = current_segment['segment_distance'];
        let seg2seg_distance = previous_segment['distance'][end] +
                               haversine_distance([current_segment.lat[0], current_segment.lon[0]],
                                                  [previous_segment.lat[end], previous_segment.lon[end]]);
        distance = distance.map(a => a +  seg2seg_distance);
        track['segments'][i]['distance'] = distance;
    }
}

function haversine_distance([lat1, lon1], [lat2, lon2]) {
    /* Compute distance between two coordinates */
    const toRadian = angle => (Math.PI / 180) * angle;
    const distance = (x, y) => (Math.PI / 180) * (x - y);
    const RADIUS_OF_EARTH_IN_KM = 6371;

    const dLat = distance(lat2, lat1);
    const dLon = distance(lon2, lon1);

    lat1 = toRadian(lat1);
    lat2 = toRadian(lat2);

    // Haversine Formula
    const a =
        Math.pow(Math.sin(dLat / 2), 2) +
        Math.pow(Math.sin(dLon / 2), 2) * Math.cos(lat1) * Math.cos(lat2);
    const c = 2 * Math.asin(Math.sqrt(a));

    return RADIUS_OF_EARTH_IN_KM * c;
}
