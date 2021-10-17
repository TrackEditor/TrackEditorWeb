import * as plot from "./plot.js";
import * as utils from "./utils.js";


export function close_split_assistant(map, chart) {
    const btn = document.getElementById('btn_split');
    const div = document.getElementById('div-split');
    btn.classList.remove('split-mode');
    btn.classList.add('btn-edition');
    div.style.display = 'none';
    enable_all_btn();
    remove_elevation_point(chart);
    remove_map_point(map);
}


export function open_split_assistant(map, chart, track, segment_index) {
    const range_control = document.getElementById('split-range');
    const btn = document.getElementById('btn_split');
    const div = document.getElementById('div-split');

    // Disable buttons except the split assistant
    btn.classList.remove('btn-edition');
    btn.classList.add('split-mode');
    div.style.display = 'inline-block';
    disable_all_btn_except_ids(['btn_split_done', 'btn_split_cancel']);

    // Segment management
    let segment = utils.get_segment(track, segment_index);
    let segment_size = segment['lat'].length;
    range_control.setAttribute('max', `${segment_size - 1}`);

    // Initial point display map
    let point_idx = range_control.value;
    let point_coordinates = {'lat': segment['lat'][point_idx],
                             'lon': segment['lon'][point_idx]};

    const split_point_source_vector = plot.get_points_source([point_coordinates.lat],
                                                             [point_coordinates.lon]);
    const splitting_point_layer = new ol.layer.Vector({
        source: split_point_source_vector,
        style: plot.get_splitting_point_style(),
        name: `layer_points_${segment.index}`,
    });
    map.addLayer(splitting_point_layer);

    // Initial point display elevation
    let point_elevation = {'x': segment['distance'][point_idx], 'y': segment['ele'][point_idx]};
    chart.data.datasets.push({
        label: 'split_point',
        fill: true,
        data: [point_elevation],
        showLine: false,
        pointRadius: 10,
        backgroundColor: 'rgb(255, 0, 0, 0.6)',
        borderColor: 'rgb(255, 0, 0, 0.8)',
        hidden: false,
    });
    chart.update();

    // Move the displayed point in map
    const split_assistant_point_map = () => {
        point_idx = range_control.value;
        point_coordinates = {'lat': segment['lat'][point_idx],
                             'lon': segment['lon'][point_idx]};
        split_point_source_vector.getFeatures()[0].
                                  getGeometry().
                                  setCoordinates(
                                      ol.proj.fromLonLat([point_coordinates.lon, point_coordinates.lat]));
        map.render();
    };

    // Move the displayed point in elevation
    const split_assistant_point_elevation = () => {
        chart.data.datasets.forEach(dataset => {
            if (dataset.label === 'split_point') {
                point_idx = range_control.value;
                point_elevation = {'x': segment['distance'][point_idx],
                                   'y': segment['ele'][point_idx]};
                dataset.data = [point_elevation];
            }
        });
        chart.update();
    };

    range_control.addEventListener('input', split_assistant_point_map);
    range_control.addEventListener('change', split_assistant_point_map);
    range_control.addEventListener('input', split_assistant_point_elevation);
    range_control.addEventListener('change', split_assistant_point_elevation);
}


function disable_all_btn_except_ids(btn_exception_ids) {
    let btn_list = Array.from(document.getElementsByClassName('btn'));

    btn_list.forEach(btn => {
        if (!btn_exception_ids.includes(btn.id)) {
            btn.disabled = true;
        }
    });

    // Add gpx button management
    let btn_select_file = document.getElementById('select-file');
    let label_select_file = document.getElementById('label-select-file');
    btn_select_file.disabled = true;
    label_select_file.disabled = true;
    label_select_file.style.opacity = '0.6';
}


function enable_all_btn() {
    let btn_list = Array.from(document.getElementsByClassName('btn'));

    btn_list.forEach(btn => {
            btn.disabled = false;
    });

    // Add gpx button management
    let btn_select_file = document.getElementById('select-file');
    let label_select_file = document.getElementById('label-select-file');
    btn_select_file.disabled = false;
    label_select_file.disabled = false;
    label_select_file.style.opacity = '1';
}


function remove_elevation_point(chart) {
    let chartIndexToRemove;
    chart.data.datasets.forEach((dataset, index) => {
        let label = dataset.label;

        if (typeof label !== 'undefined') {
            if (label === 'split_point') {
                chartIndexToRemove = index;
            }
        }
    });

    chart.data.datasets.splice(chartIndexToRemove, 1);
    chart.update();
}


function remove_map_point(map) {
    let layerToRemove;
    map.getLayers().forEach(layer => {
        let layer_name = layer.get('name');

        if (typeof layer_name !== 'undefined') {
                layerToRemove = layer;
        }
    });

    map.removeLayer(layerToRemove);
}

export function execute_split(track, segment_index, split_point) {
    console.log(track);
    // Update index of later segments
    track.segments.forEach(seg => {
        if (seg.index > segment_index) {
            seg.index++;
        }
    });

    // Split segment
    let segment = utils.get_segment(track, segment_index);
    track.segments.push({  // new segment
        lat: segment.lat.slice(split_point),
        lon: segment.lon.slice(split_point),
        ele: segment.ele.slice(split_point),
        distance: segment.distance.slice(split_point),
        segment_distance: segment.segment_distance.slice(split_point) - segment.segment_distance[split_point],
        size: segment.size - split_point,
        index: segment_index + 1,
        name: segment.name + '_2part'
    });

    segment.lat = segment.lat.slice(0, split_point);
    segment.lon = segment.lon.slice(0, split_point);
    segment.ele = segment.ele.slice(0, split_point);
    segment.distance = segment.distance.slice(0, split_point);
    segment.segment_distance = segment.segment_distance.slice(0, split_point);
    segment.size = split_point;
    segment.index = segment_index;
    segment.name = segment.name + '_1part';
}


export function update_links(track, segment_index) {
    let segment = utils.get_segment(track, segment_index);
    let new_segment = utils.get_segment(track, segment_index + 1);

    // Update links info
    track.links_coor.forEach(link => {
        if (link.from >= segment_index) {
            link.from++;
            link.to++;
        }
    });

    track.links_ele.forEach(link => {
        if (link.from >= segment_index) {
            link.from++;
            link.to++;
        }
    });

    // Add new link
    track.links_coor.push({
        'from': segment_index,
        'to': new_segment.index,
        'from_coor': {'lat': segment.lat[segment.size - 1],
                     'lon': segment.lon[segment.size - 1]},
        'to_coor': {'lat': new_segment.lat[0],
                   'lon': new_segment.lon[0]}
    });
    track.links_ele.push({
        'from': segment_index,
        'to': new_segment.index,
        'from_ele': {'x': segment.distance[segment.size - 1],
                     'y': segment.ele[segment.size - 1]},
        'to_ele': {'x': new_segment.distance[0],
                   'y': new_segment.ele[0]}
    });

}
