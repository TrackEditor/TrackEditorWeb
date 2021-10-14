import * as utils from "./utils.js";
import * as plot from "./plot.js";
import * as data_ops from "./data_operations.js";
import * as reverse_utils from "./reverse.js";
import * as split_segment_utils from "./split_segment.js";
let selected_segments = 0;
let selected_segment_idx;
let track;
let map;
let chart;


document.addEventListener('DOMContentLoaded', async () => {
    track = await data_ops.load_track();
    map = plot.create_map();
    chart = plot.create_chart();  // elevation chart
    data_ops.submit_file();
    data_ops.save_session();
    data_ops.update_session_name();
    data_ops.download_session();
    plot_track();
    segments_manager();
    show_summary();
    reverse_segment();
    change_segments_order();
    split_segment();
});


function plot_track() {
    // Plot track
    track['segments'].forEach(seg => plot_segment(seg));
    track['links_coor'].forEach(link => plot.plot_coordinates_link(map, link));
    track['links_ele'].forEach(link => plot.plot_elevation_link(chart, link));

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
    let color = plot.get_color(segment.index, '-1');
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
        }).catch(error => display_error('error', error + '(at rename_segment)'));
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
    utils.activate_spinner('#div_spinner');

    // remove from list
    list.p_name.style.display = 'none';
    list.span_name.style.display = 'none';

    plot.remove_elevation(chart, segment_index);

    plot.remove_map_layer(map, segment_index);

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
        utils.deactivate_spinner('#div_spinner');
    }).catch( error => {
        display_error('error', error);
        utils.deactivate_spinner('#div_spinner');
    });
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
        plot.plot_coordinates_link(map, new_link);
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
        backgroundColor: plot.get_color(segment.index, '0.2'),
        borderColor: plot.get_color(segment.index, '0.8'),
        hidden: false,
    });
    chart.update();
}


function plot_segment(segment) {
    plot_elevation(segment);

    // Points to vector layer
    const points_vector_layer = new ol.layer.Vector({
        source: plot.get_points_source(segment.lat, segment.lon),
        style: plot.get_points_style(segment.index),
        name: `layer_points_${segment.index}`,
    });
    map.addLayer(points_vector_layer);

    // Lines to vector layer
    const lines_vector_layer = new ol.layer.Vector({
        source: plot.get_lines_source(segment.lat, segment.lon,
                                 `features_lines_${segment.index}`,
                                 plot.get_lines_style(segment.index)),
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
                        color: plot.get_color(segment.index, '0.9'),
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
        utils.deactivate_spinner('#div_spinner_summary');
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
        utils.activate_spinner('#div_spinner_summary');

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
                utils.deactivate_spinner('#div_spinner_summary');

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


function reverse_segment() {
    let btn_reverse = document.getElementById('btn_reverse');
    btn_reverse.addEventListener('click', () => {
        utils.activate_spinner('#div_spinner');

        if (!check_selected_segment(btn_reverse)){  // verify that one segment is selected
            return;
        }

        fetch(`/editor/reverse_segment/${selected_segment_idx}`, {
            method: 'POST',
        }).then( response => {
            if (response.status === 200) {
                reverse_utils.reverse_elevation(chart, selected_segment_idx);
                reverse_utils.reverse_map_link(map, track, selected_segment_idx);
                reverse_utils.reverse_elevation_link(chart, track, selected_segment_idx);
                utils.deactivate_spinner('#div_spinner');
            }
            else {
                response_error_mng(response.status, 'reverse_segment');
                utils.deactivate_spinner('#div_spinner');
            }
        }).catch(error => response_error_mng(-1, error));

    });
}


function check_selected_segment(btn) {
    btn.addEventListener('click', () => {
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
                let color = plot.get_color(el.dataset.segment_idx, '-1');

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
            utils.deactivate_spinner('#div_spinner_change_order');

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
                plot.remove_map_layer(map, segment.index);
                plot.remove_elevation(chart, segment.index);
                plot.remove_map_links(map, segment.index);
                plot.remove_elevation_links(chart, segment.index);
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
                               plot.haversine_distance([current_segment.lat[0], current_segment.lon[0]],
                                                  [previous_segment.lat[end], previous_segment.lon[end]]);
        distance = distance.map(a => a +  seg2seg_distance);
        track['segments'][i]['distance'] = distance;
    }
}


function split_segment() {
    const btn = document.getElementById('btn_split');
    const btn_ok = document.getElementById('btn_split_done');
    const btn_cancel = document.getElementById('btn_split_cancel');
    const range_control = document.getElementById('split-range');
    let segment_index;
    check_selected_segment(btn);

    // Open the split assistant
    btn.addEventListener('click', () => {
        if (selected_segments !== 0) {
            segment_index = selected_segment_idx;
            split_segment_utils.open_split_assistant(map, chart, track, segment_index);
        }
    });

    // Cancel splitting
    btn_cancel.addEventListener('click', () => {
        split_segment_utils.close_split_assistant(map, chart);
    });

    // Apply splitting
    btn_ok.addEventListener('click', () => {
        utils.activate_spinner('#div_spinner');
        fetch(`/editor/divide_segment/${segment_index}/${range_control.value}`, {
             method: 'POST',
        }).then( () => {
            utils.deactivate_spinner('#div_spinner');
            split_segment_utils.close_split_assistant(map, chart);
        }).catch(error => display_error('error', error + '(at split_segment)'));
    });

    // TODO: manage the track object to split segments
}
