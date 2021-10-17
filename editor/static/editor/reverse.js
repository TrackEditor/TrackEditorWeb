import * as plot from "./plot.js";
import * as utils from "./utils.js";


export function reverse_elevation(chart, segment_index) {
    chart.data.datasets.forEach(dataset => {
        if (dataset.label === `elevation_${segment_index}`) {
            let reversed_data = [];
            let size = dataset.data.length;
            for (let i = 0; i < size; i++){
                reversed_data.push({x: dataset.data[i].x, y: dataset.data[size - i - 1].y});
            }
            dataset.data = reversed_data;
        }
    });
    chart.update();
}


export function reverse_map_link(map, track, segment_index) {
    let segment = utils.get_segment(track, segment_index);

    plot.remove_map_links(map, segment_index);

    for (let link of track['links_coor']) {
        let end = segment['lon'].length - 1;

        if (link['from'] === segment_index) {
            // different reversing criteria to support multiple reverse
            if (segment['lon'][0] !== link['from_coor']['lon']) {
                link['from_coor'] = {
                    'lon': segment['lon'][0],
                    'lat': segment['lat'][0]
                };
            }
            else{
                link['from_coor'] = {
                    'lon': segment['lon'][end],
                    'lat': segment['lat'][end]
                };
            }
            plot.plot_coordinates_link(map, link);
        }

        if (link['to'] === segment_index) {
            if (segment['lon'][end] !== link['to_coor']['lon']) {
                link['to_coor'] = {
                    'lon': segment['lon'][end],
                    'lat': segment['lat'][end]
                };
            }
            else {
                link['to_coor'] = {
                    'lon': segment['lon'][0],
                    'lat': segment['lat'][0]
                };
            }
            plot.plot_coordinates_link(map, link);
        }
    }

}


export function reverse_elevation_link(chart, track, segment_index) {
    let segment = utils.get_segment(track, segment_index);

    plot.remove_elevation_links(chart, segment_index);

    for (let link of track['links_ele']) {
        let end = segment['ele'].length - 1;

         if (link['from'] === segment_index) {
            // different reversing criteria to support multiple reverse
            if (segment['ele'][0] !== link['from_ele']['y']) {
                link['from_ele'] = {'x': segment['distance'][end],
                                    'y': segment['ele'][0]};
            }
            else{
                link['from_ele'] = {'x': segment['distance'][end],
                                    'y': segment['ele'][end]};
            }
            plot.plot_elevation_link(chart, link);
        }

        if (link['to'] === segment_index) {
            if (segment['ele'][end] !== link['to_ele']['y']) {
                link['to_ele'] = {'x': segment['distance'][0],
                                  'y': segment['ele'][end]};
            }
            else {
                link['to_ele'] = {'x': segment['distance'][0],
                                  'y': segment['ele'][0]};
            }
            plot.plot_elevation_link(chart, link);
        }
    }
}
