document.addEventListener('DOMContentLoaded', function() {
    insert_map();
});


function insert_map() {
    // Read data
    const element_div_map = document.querySelector('#js-map');
    var lat = eval(element_div_map.dataset.lat);
    var lon = eval(element_div_map.dataset.lon);
    var map_center = eval(element_div_map.dataset.map_center);
    var map_zoom = element_div_map.dataset.map_zoom;

    // Styles
    const points_style = new ol.style.Style({
            image: new ol.style.Circle({
                fill: new ol.style.Fill({color: 'rgba(255,255,0,0.4)'}),  // inner color
                radius: 1,  // edge radius
//                stroke: new ol.style.Stroke({  // edge definition
//                    color:  new ol.style.Fill({color: 'rgba(255,255,0,0.4)'}),  // edge color
//                    width: 2,  // edge size
//                })
            }),
        });

    const line_style = new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'rgba(255,255,0,0.4)',
                width: 5,
            })
        })

    // Points to vector layer
    const points_vector_layer = new ol.layer.Vector({
        source: get_points(lat, lon),
        style: points_style
    });

    // Lines to vector layer
    const lines_vector_layer = new ol.layer.Vector({
        source: get_lines(lat, lon),
        style: line_style
    });

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
            lines_vector_layer,
            points_vector_layer
        ],
        target: "js-map"
    })
}

function get_points(lat, lon) {
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

function get_lines(lat, lon) {
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

