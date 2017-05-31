"use strict";

/**
 * Returns a number whose value is limited to the given range.
 *
 * Example: limit the output of this computation to between 0 and 255
 * (x * 255).clamp(0, 255)
 *
 * @param {Number} min The lower boundary of the output range
 * @param {Number} max The upper boundary of the output range
 * @returns A number in the range [min, max]
 * @type Number
 */
Number.prototype.clamp = function(min, max) {
    return Math.min(Math.max(this, min), max);
};


/**
 * Initialize a map instance using a container id and options.
 * Options:
 *    min/max lat/lon: Floating point numbers
 *    lat_lon_indicator: id for a div to put the lat lon positions in
 */
function DrawMap(container_id, options) {
    this.lat_lon_indicator = options.lat_lon_indicator == undefined ? "lat_lon_container" : options.lat_lon_indicator;

    this.map = new L.Map(container_id, {
        zoomSnap: 0.25
    });

    var osm = new L.TileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors'
    });

    this.map.addLayer(osm);

    if ('min_lat' in options) {
        var bb_points = [
            [options.min_lat, options.min_lon],
            [options.max_lat, options.min_lon],
            [options.max_lat, options.max_lon],
            [options.min_lat, options.max_lon],
            [options.min_lat, options.min_lon]
        ];

        var polyline = this.create_outline(bb_points);
        this.map.fitBounds(polyline.getBounds(), {
            padding: [100, 100]
        });
        this.bounding_box = polyline.getBounds();
    } else {
        this.map.setView([0, 0], 3);
        this.map.setMaxBounds([
            [-60, -200],
            [85, 200]
        ]);
    }

    this.set_mouse_label(this.lat_lon_indicator);

    this.images = {};
}

/**
 * Configure leaflet for rectangle drawing - adds a new control and starts the handlers.
 */
DrawMap.prototype.set_rectangle_draw = function() {
    var draw_options = {
        draw: {
            polyline: false,
            polygon: false,
            circle: false,
            rectangle: {
                shapeOptions: {
                    clickable: false
                }
            },
            marker: false
        },
        edit: false
    };

    var drawControl = new L.Control.Draw(draw_options);
    this.map.addControl(drawControl);
    this.set_rect_draw_handlers();
}

/**
 * Set all the handlers for rectangle drawing - start on click, creation w/ bounding box, removal on new draw.
 */
DrawMap.prototype.set_rect_draw_handlers = function() {
    var self = this;
    this.map.on(L.Draw.Event.CREATED, function(e) {
        var type = e.layerType,
            layer = e.layer;
        var bounds = layer.getBounds();
        self.bb_rectangle = L.rectangle(constrain_bounds(self.bounding_box, bounds));
        self.map.addLayer(self.bb_rectangle)
    });

    this.map.on(L.Draw.Event.DRAWSTART, function(e) {
        if (self.bb_rectangle != undefined) {
            self.map.removeLayer(self.bb_rectangle);
        }
    });

    this.map.on('click', function(e) {
        new L.Draw.Rectangle(self.map, {
            shapeOptions: {
                clickable: false
            }
        }).enable();
    });
}

/*
 * Set ondraw listeners to update the min/max lat/lon inputs by id.
 */
DrawMap.prototype.set_bb_listeners = function(options) {
    var self = this;

    function set_input_bounds(bounds) {
        jQuery("#" + options.max_lat).val(bounds.getNorth().toFixed(4));
        jQuery("#" + options.min_lat).val(bounds.getSouth().toFixed(4));
        jQuery("#" + options.min_lon).val(bounds.getWest().toFixed(4));
        jQuery("#" + options.max_lon).val(bounds.getEast().toFixed(4));
    }

    this.map.on("draw:created", function(e) {
        var bounds = e.layer.getBounds();
        set_input_bounds(constrain_bounds(self.bounding_box, bounds));
    })
}

/**
 * Add a mousemove event that writes the lat/lng coords to the div id specified by lat_lon_container
 */
DrawMap.prototype.set_mouse_label = function(lat_lon_container) {
    var instance = this;
    var label = $("#" + lat_lon_container);
    this.map.on('mousemove', function(e) {
        label.text("Lat: " + e.latlng.lat.toFixed(4) + ", Lon: " + e.latlng.lng.toFixed(4));
    });
}

/**
 * Create an outline on the map from a list of latlng points
 *     Args:
 *          points: list of Leaflet LatLng points
 *     Returns:
 *          polyline that has been added to the map.
 */
DrawMap.prototype.create_outline = function(points) {
    var polyline = L.polyline(points, {
        color: "#ff7800",
        weight: 3
    }).addTo(this.map);
    return polyline
}

/**
 * Update the BB using form elements registered from the main page
 */
DrawMap.prototype.bounding_box_from_form = function(min_lat, max_lat, min_lon, max_lon) {
    var min_point = [parseFloat(min_lat), parseFloat(min_lon)];
    var max_point = [parseFloat(max_lat), parseFloat(max_lon)];
    if (isNaN(min_point[1]) || isNaN(max_point[1]) || isNaN(min_point[0]) || isNaN(max_point[0]))
        return;

    var bounds = L.latLngBounds([min_point, max_point]);

    if (this.bb_rectangle != undefined) {
        this.map.removeLayer(this.bb_rectangle);
    }
    this.bb_rectangle = L.rectangle(constrain_bounds(this.bounding_box, bounds));
    this.map.addLayer(this.bb_rectangle)
}

/**
 * Insert a rectangular image onto the map using a BB and url. The image is associated with an id for easy removal/mgmt
 */
DrawMap.prototype.insert_image_with_bounds = function(id, url, min_lat, max_lat, min_lon, max_lon) {
    var min_point = [parseFloat(min_lat), parseFloat(min_lon)];
    var max_point = [parseFloat(max_lat), parseFloat(max_lon)];
    if (isNaN(min_point[1]) || isNaN(max_point[1]) || isNaN(min_point[0]) || isNaN(max_point[0]))
        return;

    var bounds = L.latLngBounds([min_point, max_point]);

    var bb_points = [
        [min_lat, min_lon],
        [max_lat, min_lon],
        [max_lat, max_lon],
        [min_lat, max_lon],
        [min_lat, min_lon]
    ];

    this.images[id] = {
        image: L.imageOverlay(url, bounds),
        outline: L.polyline(bb_points, {
            color: "#00FFFF",
            weight: 4
        })
    };

    //this.map.addLayer(this.images[id].outline);
    this.map.addLayer(this.images[id].image);

    if (this.bb_rectangle != undefined) {
        this.map.removeLayer(this.bb_rectangle);
    }
}

/**
 * Set the view based on the BB of an image.
 */
DrawMap.prototype.zoom_to_image_by_id = function(id) {
    this.map.fitBounds(this.images[id].image.getBounds(), {
        padding: [50, 50]
    });
}

/**
 * Toggle an image outline by its id - if val is undefined, then it will be toggled.
 */
DrawMap.prototype.toggle_outline_by_id = function(id, val) {
    var outline = this.images[id].outline;
    var outline_exists = this.map.hasLayer(outline)
    if (val !== undefined) {
        if (!val && outline_exists) {
            this.map.removeLayer(outline);
        } else if (val && !outline_exists) {
            this.map.addLayer(outline);
        }
    } else {
        if (outline_exists) {
            this.map.removeLayer(outline);
        } else {
            this.map.addLayer(outline);
        }
    }
}

/**
 * Add or remove an image with an id
 */
DrawMap.prototype.toggle_visibility_by_id = function(id, val) {
    var image = this.images[id].image;
    var image_exists = this.map.hasLayer(image)
    if (val !== undefined) {
        if (!val && image_exists) {
            this.map.removeLayer(image);
        } else if (val && !image_exists) {
            this.map.addLayer(image);
        }
    } else {
        if (image_exists) {
            this.map.removeLayer(image);
        } else {
            this.map.addLayer(image);
        }
    }
}

/**
 * Remove an image and its outline by id.
 */
DrawMap.prototype.remove_image_by_id = function(id) {
    this.map.removeLayer(this.images[id].outline);
    this.map.removeLayer(this.images[id].image);
}

function constrain_bounds(constraint_bounds, bounds) {
    return L.latLngBounds([
        [bounds.getSouth().clamp(constraint_bounds.getSouth(), constraint_bounds.getNorth()), bounds.getWest().clamp(constraint_bounds.getWest(), constraint_bounds.getEast())],
        [bounds.getNorth().clamp(constraint_bounds.getSouth(), constraint_bounds.getNorth()), bounds.getEast().clamp(constraint_bounds.getWest(), constraint_bounds.getEast())]
    ]);
}

//returns a bounded cartographic.
function clamp_input(lon, lat) {
    return [lon.clamp(window._MIN_LON_DATA_BOUNDS_, window._MAX_LON_DATA_BOUNDS_), lat.clamp(window._MIN_LAT_DATA_BOUNDS_, window._MAX_LAT_DATA_BOUNDS_)];
}
