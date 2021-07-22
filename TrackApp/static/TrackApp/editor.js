document.addEventListener('DOMContentLoaded', function() {
    insert_map();
});


function insert_map() {
    // Create map
    const map = new ol.Map({
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
        target: "js-map"
    });
}
