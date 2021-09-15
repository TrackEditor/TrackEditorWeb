document.addEventListener('DOMContentLoaded', () => {
    insert_map();
});

/**
 * GET_COLORS returns a rgb string code to be used with for OpenLayers
 *
 * @param color_index integer index to the color
 * @param alpha string containing a float for RGBA alpha parameter (transparency)
 * @return rgb_string string representing the color to be used in OpenLayers
 */
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


/**
 * CREATE_MAP returns a rgb string code to be used with for OpenLayers
 *
 * @param map_center array of two floats with center point of the map,
 *                   Longitude - Latitude
 * @param map_zoom integer value with the OpenLayers default zoom level
 * @return map OpenLayers map object
 */
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


/**
 * GET_LINK_STYLE returns the style for lines joining two track segments
 *
 * @return link_style OpenLayers style object
 */
function get_link_style() {
    return new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: 'rgb(0, 0, 128, 0.1)',  // navy color
            width: 3,
        })
    });
}


/**
 * GET_POINTS_STYLE returns the style for points in forming a segment
 *
 * @param color_index integer value to get the color from a list
 * @return link_style OpenLayers style object
 */
function get_points_style(color_index) {
    return new ol.style.Style({
        image: new ol.style.Circle({
            fill: new ol.style.Fill({color: get_color(color_index)}),  // inner color
            radius: 3,  // circle radius
        }),
    });
}

/**
 * GET_LINE_STYLE returns the style for line forming a segment
 *
 * @param color_index integer value to get the color from a list
 * @return link_style OpenLayers style object
 */
function get_line_style(color_index) {
    return new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: get_color(color_index),
            width: 5,
        })
    });
}


/**
 * INSERT_MAP creates a map object and insert the track points on it. It
 * generates the resulting map @js-map element
 */
function insert_map() {
    // Read data
    const div_map = document.querySelector('#js-map');
    const lat = div_map.data('lat');
    const lon = div_map.data('lon');
    const map_center = JSON.parse(div_map.dataset.map_center);
    const map_zoom = JSON.parse(div_map.dataset.map_zoom);

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


/**
 * GET_POINTS_SOURCE produces the source vector object from all the latitude
 * and longitude pairs of one segment. It is made of points.
 *
 * @param lat array with all the latitude points of one segment
 * @param lon array with all the longitude points of one segment
 * @return vectorSource OpenLayers source Vector object containing all the
 *                      points of the segment
 */
function get_points_source(lat, lon) {
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


/**
 * GET_LINES_SOURCE produces the source vector object from all the latitude
 * and longitude pairs of one segment. It is made by a line.
 *
 * @param lat array with all the latitude points of one segment
 * @param lon array with all the longitude points of one segment
 * @return vectorSource OpenLayers source Vector object containing a line
 *                      generated by all the pairs lon-lat
 */
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


/**
 * GET_LINKS_SOURCE produces the source vector object to create line from end
 * of one segment to the beggining of the next one.
 *
 * @param lat float with the last latitude value of one segment
 * @param lon float with the last longitude value of one segment
 * @param lat_next float with the first latitude value of one segment
 * @param lon_next float with the first longitude value of one segment
 * @return vectorSource OpenLayers source Vector object containing a line
 *                      from lat-lon to lat_next-lon_next
 */
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
