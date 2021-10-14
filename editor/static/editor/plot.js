export function haversine_distance([lat1, lon1], [lat2, lon2]) {
    /* Compute distance between two coordinates */
    const toRadian = angle => (Math.PI / 180) * angle;
    const distance = (x, y) => (Math.PI / 180) * (x - y);
    const RADIUS_OF_EARTH_IN_KM = 6371;

    const dLat = distance(lat2, lat1);
    const dLon = distance(lon2, lon1);

    lat1 = toRadian(lat1);
    lat2 = toRadian(lat2);

    // Haversine Formula
    const a =
        Math.pow(Math.sin(dLat / 2), 2) +
        Math.pow(Math.sin(dLon / 2), 2) * Math.cos(lat1) * Math.cos(lat2);
    const c = 2 * Math.asin(Math.sqrt(a));

    return RADIUS_OF_EARTH_IN_KM * c;
}

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
            maxZoom: 16,
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
