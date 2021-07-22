document.addEventListener('DOMContentLoaded', function() {
    insert_map();
});


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

    return `rgb(${colors[color_index]}, ${alpha})`;
}


function create_map(map_center, map_zoom) {
    // Create map
    const map = new ol.Map({
        view: new ol.View({
            center: ol.proj.fromLonLat(map_center),
            zoom: map_zoom,
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

    return map;
}


function get_line_style(color_index) {
    const line_style = new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: get_color(color_index),
                width: 5,
            })
        });
    return line_style;
}


function get_points_style(color_index) {
    const points_style = new ol.style.Style({
            image: new ol.style.Circle({
                fill: new ol.style.Fill({color: get_color(color_index)}),  // inner color
                radius: 2,  // edge radius
//                stroke: new ol.style.Stroke({  // edge definition
//                    color:  new ol.style.Fill({color: get_color(color_index, '0.8')}),  // edge color
//                    width: 1,  // edge size
//                })
            }),
        });
    return points_style;
}


function insert_map() {
    // Read data
    const element_div_map = document.querySelector('#js-map');
    var lat = eval(element_div_map.dataset.lat);
    var lon = eval(element_div_map.dataset.lon);
    var map_center = eval(element_div_map.dataset.map_center);
    var map_zoom = element_div_map.dataset.map_zoom;

    var map = create_map(map_center, map_zoom);
    console.log('insert_map()');
    console.log('length', lon.length);
    console.log('lat', lat);
    console.log('lon', lon);

    for (var i = 0; i < lon.length; i++) {
        // Points to vector layer
        const points_vector_layer = new ol.layer.Vector({
            source: get_points_source(lat[i], lon[i]),
            style: get_points_style(i)
        });

        // Lines to vector layer
        const lines_vector_layer = new ol.layer.Vector({
            source: get_lines_source(lat[i], lon[i]),
            style: get_line_style(i)
        });

        map.addLayer(points_vector_layer);
        map.addLayer(lines_vector_layer);
    }

}

function get_points_source(lat, lon) {
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

