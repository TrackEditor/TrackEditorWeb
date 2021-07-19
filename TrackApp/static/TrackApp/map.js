document.addEventListener('DOMContentLoaded', function() {
    points_vector = get_points();
    insert_map(points_vector);
});


function insert_map(points_vector) {
    // Points to vector layer
    const points_vector_layer = new ol.layer.Vector({
        source: points_vector,
        style: new ol.style.Style({
            image: new ol.style.Circle({
                radius: 2,
                fill: new ol.style.Fill({color: 'red'})
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
            points_vector_layer
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

