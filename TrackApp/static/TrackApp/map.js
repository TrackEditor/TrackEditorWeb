document.addEventListener('DOMContentLoaded', function() {
    insert_map();
});


function insert_map() {
    const points_style = new ol.style.Style({
            image: new ol.style.Circle({
                fill: new ol.style.Fill({color: 'rgba(255,255,0,0.4)'}),  // inner color
                radius: 5,  // edge radius
                stroke: new ol.style.Stroke({  // edge definition
                    color: 'red',  // edge color
                    width: 2,  // edge size
                })
            }),
        });

    // Points to vector layer
    const points_vector_layer = new ol.layer.Vector({
        source: get_points(),
        style: points_style
    });

    // Lines to vector layer
    const lines_vector_layer = new ol.layer.Vector({
        source: get_lines(),
        style: new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'red',
                width: 2,
            })
        })
    });

    // Create map
    const map = new ol.Map({
        view: new ol.View({
            center: [0, 3.5e+6],
            zoom: 1,
            maxZoom: 16,
            minZoom: 1
        }),
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            }),
            points_vector_layer,
            lines_vector_layer
        ],
        target: "js-map"
    })
}

function get_points() {
    const element_div_map = document.querySelector('#js-map');
    var lat = eval(element_div_map.dataset.lat);
    var lon = eval(element_div_map.dataset.lon);

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

function get_lines() {
    const element_div_map = document.querySelector('#js-map');
    var lat = eval(element_div_map.dataset.lat);
    var lon = eval(element_div_map.dataset.lon);

    // create points
    const points = [];
    for (i = 0; i < lat.length; i++) {
        console.log(ol.proj.fromLonLat([lon[i], lat[i]]));
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

