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

//updates the bounding box from the form data if relevant.
DrawMap.prototype.bounding_box_from_form = function(min_lat, max_lat, min_lon, max_lon) {
    var min_point = [parseFloat(min_lat),parseFloat(min_lon)];
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

//inserts an image onto the map using provided bounds. This currently uses the entity/rect methods, but
//can be easily converted to single tile imagery providers if necessary for performance reasons.
//the image is accompanied by an outline that can be enabled/disabled for a highlight function.
DrawMap.prototype.insert_image_with_bounds = function(id, url, min_lat, max_lat, min_lon, max_lon) {

    var layers = this.cesium.imageryLayers;

    this.images[id] = layers.addImageryProvider(new Cesium.SingleTileImageryProvider({
        url: url,
        rectangle: Cesium.Rectangle.fromDegrees(min_lon, min_lat, max_lon, max_lat)
    }));

    /*this.cesium.entities.add({
      id: id,
      rectangle: {
        coordinates: Cesium.Rectangle.fromDegrees(min_lon, min_lat, max_lon, max_lat),
        material: new Cesium.ImageMaterialProperty({
          image: url
        }),
        outline: false,
        height: 0
      }
    });*/

    polyline_from_bounds = [Cesium.Cartesian3.fromDegrees(min_lon, max_lat), Cesium.Cartesian3.fromDegrees(max_lon, max_lat), Cesium.Cartesian3.fromDegrees(max_lon, min_lat), Cesium.Cartesian3.fromDegrees(min_lon, min_lat), Cesium.Cartesian3.fromDegrees(min_lon, max_lat)];
    this.cesium.entities.add({
        id: id + "_outline",
        polyline: {
            positions: polyline_from_bounds,
            width: 5.0,
            material: Cesium.Color.ALICEBLUE
        },
        show: false
    });

    //clear out the box so it isn't tinted white/blue
    if (!this.drawing)
        this.bounding_box = [Cesium.Cartographic.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_), Cesium.Cartographic.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_)];
}

//zooms and pans to an image by its id.
DrawMap.prototype.zoom_to_image_by_id = function(id) {
    var entity = this.cesium.entities.getById(id + "_outline");
    if (entity) {
        rect = Cesium.Rectangle.fromCartesianArray(entity.polyline.positions.getValue(), Cesium.Ellipsoid.WGS84);
        //dest_cartographic = Cesium.Rectangle.center(rect);
        //enforce max height.
        //if(dest_cartographic.height < 150000)
        //  dest_cartographic.height = 150000;
        //dest = Cesium.Cartesian3.fromRadians(dest_cartographic.longitude, dest_cartographic.latitude, dest_cartographic.height);
        this.cesium.camera.flyTo({
            destination: rect
        });
    }
}

//toggles the visibility of the outline by its id.
DrawMap.prototype.toggle_outline_by_id = function(id, val) {
    var entity = this.cesium.entities.getById(id + "_outline");
    if (entity) {
        if (val !== undefined) {
            entity.show = val;
        } else
            entity.show = !entity.show;
    }
}

//toggles the visibility of the image by its id.
DrawMap.prototype.toggle_visibility_by_id = function(id, val) {
    //var entity = this.cesium.entities.getById(id);
    var entity = this.images[id];
    if (entity) {
        if (val !== undefined) {
            entity.show = val;
        } else
            entity.show = !entity.show;
    }
}

//deletes and image and its outline by their ids.
DrawMap.prototype.remove_image_by_id = function(id) {
    this.cesium.imageryLayers.remove(this.images[id]);
    //this.cesium.entities.removeById(id);
    this.cesium.entities.removeById(id + "_outline");
}

function constrain_bounds(constraint_bounds, bounds) {
    return L.latLngBounds([
        [bounds.getSouth().clamp(constraint_bounds.getSouth(), constraint_bounds.getNorth()), bounds.getWest().clamp(constraint_bounds.getWest(), constraint_bounds.getEast())],
        [bounds.getNorth().clamp(constraint_bounds.getSouth(), constraint_bounds.getNorth()), bounds.getEast().clamp(constraint_bounds.getWest(), constraint_bounds.getEast())]
    ]);
}

//checks if a point is within its boundaries as defined by global bounds.
function is_in_bounds(lon, lat) {
    if (lon > window._MIN_LON_DATA_BOUNDS_ && lon < window._MAX_LON_DATA_BOUNDS_ && lat > window._MIN_LAT_DATA_BOUNDS_ && lat < window._MAX_LAT_DATA_BOUNDS_)
        return true;
    return false;
}

//returns a bounded cartographic.
function clamp_input(lon, lat) {
    return [lon.clamp(window._MIN_LON_DATA_BOUNDS_, window._MAX_LON_DATA_BOUNDS_), lat.clamp(window._MIN_LAT_DATA_BOUNDS_, window._MAX_LAT_DATA_BOUNDS_)];
}
