export function create_chart() {
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


export function create_map() {
    return new ol.Map({
        view: new ol.View({
            center: ol.proj.fromLonLat([0, 0]),
            zoom: 1,
            maxZoom: 20,
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


export function get_color(color_index, alpha='0.5') {
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


export function get_links_source(from, to) {
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


export function get_link_style() {
    return new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: 'rgb(0, 0, 128, 0.1)',  // navy color
            width: 3,
        })
    });
}


export function get_points_source(lat, lon) {
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


export function get_lines_source(lat, lon, id, style) {
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


export function get_points_style(color_index) {
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


export function get_splitting_point_style() {
    return new ol.style.Style({
        image: new ol.style.Circle({
            fill: new ol.style.Fill({color: 'rgb(255, 0, 0, 0.7)'}),  // inner color
            radius: 8,  // circle radius
        }),
    });
}


export function get_lines_style(color_index, alpha) {
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


export function plot_elevation(chart, segment) {
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


export function plot_segment(map, chart, segment, selected_segment) {
    plot_elevation(chart, segment);

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
            elevation_show_segment(chart, segment.index);
            selected_segment.idx = segment.index;
            selected_segment.status = true;
        }
        else {
            elevation_show_segment(chart, undefined, true);
            selected_segment.idx = undefined;
            selected_segment.status = false;
        }

    });

}


export function plot_coordinates_link(map, link) {
    const link_vector_layer = new ol.layer.Vector({
        source: get_links_source(link['from_coor'], link['to_coor']),
        style: get_link_style(),
        name: `layer_link_${link['from']}_${link['to']}`,
    });
    map.addLayer(link_vector_layer);
}


export function plot_elevation_link(chart, link) {
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


export function remove_elevation_links(chart, segment_index) {
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
    let chartIndexToRemoveReversed = chartIndexToRemove.slice();
    chartIndexToRemoveReversed.reverse();

    chartIndexToRemoveReversed.forEach(idx => {
        chart.data.datasets.splice(idx, 1);
    });
    chart.update();
}


export function remove_map_links(map, segment_index) {
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


export function remove_map_layer(map, segment_index) {
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


export function remove_elevation(chart, segment_index) {
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
    let chartIndexToRemoveReversed = chartIndexToRemove.slice();
    chartIndexToRemoveReversed.reverse();

    chartIndexToRemoveReversed.forEach(idx => {
        // reverse is needed since array of size changes in each iteration
        chart.data.datasets.splice(idx, 1);
    });
    chart.update();
}


export function elevation_show_segment(chart, index=undefined, all=false) {
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


export function clean_elevation(chart, track) {
    chart.data.datasets = [];
    chart.update();

    track.segments.forEach(segment => {
        remove_elevation(chart, segment.index);
        remove_elevation_links(chart, segment.index);
    });
}

export function clean_map(map, track) {
    track.segments.forEach(segment => {
        remove_map_layer(map, segment.index);
        remove_map_links(map, segment.index);
    });
}
