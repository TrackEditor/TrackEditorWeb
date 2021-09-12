document.addEventListener('DOMContentLoaded', () => {
    insert_map();
});


function get_color(color_index, alpha='0.5') {
    /*
    
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

    return `rgb(${colors[color_index]}, ${alpha})`;
}


function create_map(map_center, map_zoom) {
    // Create map
    return new ol.Map({
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
}


function get_link_style() {
    return new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: 'rgb(0, 0, 128, 0.1)',  // navy color
            width: 3,
        })
    });
}


function get_points_style(color_index) {
    return new ol.style.Style({
        image: new ol.style.Circle({
            fill: new ol.style.Fill({color: get_color(color_index)}),  // inner color
            radius: 3,  // circle radius
        }),
    });
}

function get_line_style(color_index) {
    return new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: get_color(color_index),
            width: 5,
        })
    });
}


function insert_map() {
    // Read data
    const element_div_map = document.querySelector('#js-map');
    const lat = eval(element_div_map.dataset.lat);
    const lon = eval(element_div_map.dataset.lon);
    const map_center = eval(element_div_map.dataset.map_center);
    const map_zoom = element_div_map.dataset.map_zoom;

    // Map generation
    const map = create_map(map_center, map_zoom);

    for (let i = 0; i < lon.length; i++) {
        // Points to vector layer
        const points_vector_layer = new ol.layer.Vector({
            source: get_points_source(lat[i], lon[i]),
            style: get_points_style(i)
        });
        map.addLayer(points_vector_layer);

        // Lines to vector layer
        const lines_vector_layer = new ol.layer.Vector({
            source: get_lines_source(lat[i], lon[i]),
            style: get_line_style(i)
        });
        map.addLayer(lines_vector_layer);

        // Lines to vector layer
        if (i < lon.length-1){
            const link_vector_layer = new ol.layer.Vector({
                source: get_links_source(lat[i], lon[i], lat[i+1], lon[i+1]),
                style: get_link_style()
            });
            map.addLayer(link_vector_layer);
        }
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
    return new ol.source.Vector({
        features
    });
}


function get_lines_source(lat, lon) {
    // create points
    const points = [];
    for (let i = 0; i < lat.length; i++) {
        points.push(ol.proj.fromLonLat([lon[i], lat[i]]));
    }

    const featureLine = new ol.Feature({
        geometry: new ol.geom.LineString(points)
    });

    // create the source and layer for features
    return new ol.source.Vector({
        features: [featureLine]
    });
}


function get_links_source(lat, lon, lat_next, lon_next) {
    // create points
    const points = [];
    points.push(ol.proj.fromLonLat([lon[lon.length-1], lat[lat.length-1]]));
    points.push(ol.proj.fromLonLat([lon_next[0], lat_next[0]]));

    const featureLink = new ol.Feature({
        geometry: new ol.geom.LineString(points)
    });

    // create the source and layer for features
    return new ol.source.Vector({
        features: [featureLink]
    });
}
