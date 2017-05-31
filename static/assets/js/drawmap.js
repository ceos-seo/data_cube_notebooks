/* Author: AHDS
   Creation date: 2016-06-23
   Modified by:
   Last modified date: */

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


/*
 * Begin DrawMap
 */

//ARGS: Cesium div id, lat min, lat max, long min, long max ids. <-- arrays.
//initializes a map with drawing capabilities. Starts the cesium instance,
//sets up the camera, and stores the form fields that should be populated with
//latlong bounds.
//Draws an outline over valid bounds set by window variables, sets up static
//imagery, and begins drawing. Mouse position is marked with lat/lon position.
function DrawMap(container_id, min_lat, max_lat, min_lon, max_lon) {
    //holds the rectangle entity for the query bounds.
    this.query_bounds_entity = undefined;
    this.drawing = false;

    //arrays containing ids that should be updated when the bounding box changes.
    this.min_lat = $.map(min_lat, function(v) {
        return $("#" + v);
    });
    this.max_lat = $.map(max_lat, function(v) {
        return $("#" + v);
    });
    this.min_lon = $.map(min_lon, function(v) {
        return $("#" + v);
    });
    this.max_lon = $.map(max_lon, function(v) {
        return $("#" + v);
    });

    //sets up the defaults view extent.
    var lat_diff = (Math.abs(window._MAX_LAT_DATA_BOUNDS_ - window._MIN_LAT_DATA_BOUNDS_)/2);
    var lon_diff = (Math.abs(window._MAX_LON_DATA_BOUNDS_ - window._MIN_LON_DATA_BOUNDS_)/2);
    var rectangle = Cesium.Rectangle.fromDegrees(window._MIN_LON_DATA_BOUNDS_-lon_diff, window._MIN_LAT_DATA_BOUNDS_-lat_diff, window._MAX_LON_DATA_BOUNDS_+lon_diff, window._MAX_LAT_DATA_BOUNDS_+lat_diff);
    Cesium.Camera.DEFAULT_VIEW_RECTANGLE = rectangle;
    Cesium.Camera.DEFAULT_VIEW_FACTOR = 0;

    //init cesium.
    this.cesium = new Cesium.Viewer(container_id, {
        animation: false,
        baseLayerPicker: false,
        fullscreenButton: false,
        vrButton: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        sceneModePicker: false,
        selectionIndicator: false,
        timeline: false,
        navigationHelpButton: true,
        navigationInstructionsInitiallyVisible: true,
        sceneMode: Cesium.SceneMode.SCENE2D,
        /*imageryProvider : new Cesium.ArcGisMapServerImageryProvider({
            url : 'http://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer'
        }),*/
        /*imageryProvider: new Cesium.SingleTileImageryProvider({
            url: "/static/assets/images/22.22222,-10,57.777777,10.png",
            rectangle: Cesium.Rectangle.fromDegrees(22.22222,-10,57.77777,10)
        }),*/
        //TODO:? add a black box rather than this image?
        imageryProvider: new Cesium.SingleTileImageryProvider({
            url: window._MAIN_IMAGERY_,
            rectangle: Cesium.Rectangle.fromDegrees(-180,-101.25,180,101.25)
        }),
    });

    this.cesium.scene.imageryLayers.addImageryProvider(new Cesium.SingleTileImageryProvider({
        url: window._DETAIL_IMAGERY_,
        rectangle: Cesium.Rectangle.fromDegrees(window._MIN_LON_IMAGERY_BOUNDS_,window._MIN_LAT_IMAGERY_BOUNDS_,window._MAX_LON_IMAGERY_BOUNDS_,window._MAX_LAT_IMAGERY_BOUNDS_)
    }));

    this.camera_setup();

    this.bounding_box = [Cesium.Cartographic.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_), Cesium.Cartographic.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_)]

    //removes the ability to click for a popup so it won't interfere with tile listing info.
    this.cesium.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_CLICK);
    this.cesium.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);

    this.images = [];

    this.create_data_outline();
    this.set_mouse_label();
    this.start_rect_draw();
}

//Only responsible for zoom limits at this time. The imagery we use is finite resolution
//so this stops things from being too grainy.
DrawMap.prototype.camera_setup = function() {
  var zoom_limits = [this.cesium.camera.positionCartographic.height/25, this.cesium.camera.positionCartographic.height];
  //sets the initial view of the camera.
  //var rectangle = Cesium.Rectangle.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_-1, window._MAX_LON_DATA_BOUNDS_, window._MAX_LAT_DATA_BOUNDS_+1);
  //Cesium.Camera.DEFAULT_VIEW_RECTANGLE = rectangle;
  /*this.cesium.camera.setView({
      destination: rectangle
  });*/
  //var rect_center = Cesium.Rectangle.center(rectangle);
  //this.cesium.camera.lookAt(Cesium.Cartesian3.fromRadians(rect_center.longitude, rect_center.latitude), new Cesium.Cartesian3(0, 0, 100000));

  //enforces zoom limits
  this.cesium.scene.screenSpaceCameraController.maximumZoomDistance = zoom_limits[1];
  this.cesium.scene.screenSpaceCameraController.minimumZoomDistance = zoom_limits[0];

}

//starts the rectangle drawing process that updates the form fields/display.
//constantly updates form fields with values when drawing.
//clicking outside of the valid area will hide the indicator, while
//a single click in the bounds will start a draw.
DrawMap.prototype.start_rect_draw = function() {
    var instance = this;
    instance.query_bounds_entity = instance.cesium.entities.add({
        name: 'Query_bounding_box',
        rectangle: {
            coordinates: new Cesium.CallbackProperty(function() {
                rect = Cesium.Rectangle.fromCartographicArray(instance.bounding_box);
                return rect;
            }, false),
            material: Cesium.Color.ALICEBLUE.withAlpha(0.5),
            extrudedHeight: 0.0,
            height: 0.0
        }
    });

    var handler = new Cesium.ScreenSpaceEventHandler(instance.cesium.scene.canvas);
    //Handles clicks.
    var firstClick = true;
    handler.setInputAction(function(position) {
        var cartesian = instance.cesium.camera.pickEllipsoid(position.position, instance.cesium.scene.globe.ellipsoid);
        if (cartesian) {
            var cartographic = Cesium.Cartographic.fromCartesian(cartesian);
            var longitude = Cesium.Math.toDegrees(cartographic.longitude);
            var latitude = Cesium.Math.toDegrees(cartographic.latitude);
            if (!firstClick) {
                //convert to the more convenient uppre left/lower right format.
                var rectangle = Cesium.Rectangle.fromCartographicArray(instance.bounding_box);
                instance.drawing = false;
                instance.bounding_box = [Cesium.Rectangle.northwest(rectangle), Cesium.Rectangle.southeast(rectangle)];
                firstClick = true;
            } else if (is_in_bounds(longitude, latitude)) {
                if (firstClick) {
                    instance.bounding_box = [cartographic.clone(), cartographic.clone()]
                    instance.drawing = true;
                    firstClick = false;
                }
            //single click outside of the bounding box makes the box go away.
            } else {
                firstClick = true;
                instance.bounding_box = [Cesium.Cartographic.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_), Cesium.Cartographic.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_)]
            }
        }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    //Handles movement.
    handler.setInputAction(function(movement) {
        var cartesian = instance.cesium.camera.pickEllipsoid(movement.endPosition, instance.cesium.scene.globe.ellipsoid);
        if (cartesian) {
            if (firstClick) {
                //donothing?
            } else {
                var cartographic = Cesium.Cartographic.fromCartesian(cartesian);
                var longitude = Cesium.Math.toDegrees(cartographic.longitude);
                var latitude = Cesium.Math.toDegrees(cartographic.latitude);
                var bounded_input = clamp_input(longitude, latitude);
                instance.bounding_box[1] = Cesium.Cartographic.fromDegrees(bounded_input[0], bounded_input[1]);
                instance.update_form_fields();
            }
        }
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

}

//creates and updates a mouse label that lists the current geographic point.
DrawMap.prototype.set_mouse_label = function() {
    var instance = this;
    /*var entity = instance.cesium.entities.add({
        label: {
            show: false,
            pixelOffset: new Cesium.Cartesian2(135, 25),
            //fillColor: Cesium.Color.BLACK
        }
    });*/
    // Mouse over the globe to see the cartographic position
    var label = $("#lat_lon_container");
    handler = new Cesium.ScreenSpaceEventHandler(instance.cesium.scene.canvas);
    handler.setInputAction(function(movement) {
        var cartesian = instance.cesium.camera.pickEllipsoid(movement.endPosition, instance.cesium.scene.globe.ellipsoid);
        if (cartesian) {
            var cartographic = Cesium.Cartographic.fromCartesian(cartesian);
            var longitudeString = Cesium.Math.toDegrees(cartographic.longitude).toFixed(4);
            var latitudeString = Cesium.Math.toDegrees(cartographic.latitude).toFixed(4);
            //entity.position = cartesian;
            //entity.label.show = true;
            //entity.label.text = '(' + longitudeString + ', ' + latitudeString + ')';
            label.text('(' + longitudeString + ', ' + latitudeString + ')')
        } else {
            //entity.label.show = false;
        }
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
}

//Uses the globally defined country boundaries to create a border defining acceptable data ranges.
DrawMap.prototype.create_data_outline = function() {
    polyline_from_bounds = [Cesium.Cartesian3.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MAX_LAT_DATA_BOUNDS_), Cesium.Cartesian3.fromDegrees(window._MAX_LON_DATA_BOUNDS_, window._MAX_LAT_DATA_BOUNDS_), Cesium.Cartesian3.fromDegrees(window._MAX_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_), Cesium.Cartesian3.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_), Cesium.Cartesian3.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MAX_LAT_DATA_BOUNDS_)];
    this.cesium.entities.add({
        polyline: {
            positions: polyline_from_bounds,
            width: 5.0,
            material: Cesium.Color.ALICEBLUE
        }
    });
}

//Updates the form fields based on the current bounding box.
DrawMap.prototype.update_form_fields = function() {
    var rectangle = Cesium.Rectangle.fromCartographicArray(this.bounding_box);
    var upper_left = Cesium.Rectangle.northwest(rectangle);
    var lower_right = Cesium.Rectangle.southeast(rectangle);

    //for each elem. since min/max pairs go together, there will always be the same number of them.
    for (var index = 0; index < this.min_lat.length; index++) {
        this.min_lat[index].val(Cesium.Math.toDegrees(lower_right.latitude).toFixed(4));
        this.max_lat[index].val(Cesium.Math.toDegrees(upper_left.latitude).toFixed(4));
        this.max_lon[index].val(Cesium.Math.toDegrees(lower_right.longitude).toFixed(4));
        this.min_lon[index].val(Cesium.Math.toDegrees(upper_left.longitude).toFixed(4));
    }
}

//updates the bounding box from the form data if relevant.
DrawMap.prototype.bounding_box_from_form = function(min_lat, max_lat, min_lon, max_lon) {
    var min_point = [parseFloat(min_lon), parseFloat(min_lat)];
    var max_point = [parseFloat(max_lon), parseFloat(max_lat)];
    if (isNaN(min_point[1]) || isNaN(max_point[1]) || isNaN(min_point[0]) || isNaN(max_point[0]))
        return;
    if (min_point[1] > max_point[1] || min_point[0] > max_point[0])
        return;
    min_point = clamp_input(min_point[0], min_point[1]);
    max_point = clamp_input(max_point[0], max_point[1]);
    this.bounding_box = [Cesium.Cartographic.fromDegrees(min_point[0], min_point[1]), Cesium.Cartographic.fromDegrees(max_point[0], max_point[1])];
    //this.bounding_box = [Cesium.Cartographic.fromDegrees(min_lon, min_lat), Cesium.Cartographic.fromDegrees(max_lon, max_lat)];
}

//inserts an image onto the map using provided bounds. This currently uses the entity/rect methods, but
//can be easily converted to single tile imagery providers if necessary for performance reasons.
//the image is accompanied by an outline that can be enabled/disabled for a highlight function.
DrawMap.prototype.insert_image_with_bounds = function(id, url, min_lat, max_lat, min_lon, max_lon) {

    var layers = this.cesium.imageryLayers;

    this.images[id] = layers.addImageryProvider(new Cesium.SingleTileImageryProvider({
        url : url,
        rectangle : Cesium.Rectangle.fromDegrees(min_lon, min_lat, max_lon, max_lat)
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
        id: id+"_outline",
        polyline: {
            positions: polyline_from_bounds,
            width: 5.0,
            material: Cesium.Color.ALICEBLUE
        },
        show: false
    });

    //clear out the box so it isn't tinted white/blue
    if(!this.drawing)
      this.bounding_box = [Cesium.Cartographic.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_), Cesium.Cartographic.fromDegrees(window._MIN_LON_DATA_BOUNDS_, window._MIN_LAT_DATA_BOUNDS_)];
}

//zooms and pans to an image by its id.
DrawMap.prototype.zoom_to_image_by_id = function(id) {
  var entity = this.cesium.entities.getById(id+"_outline");
  if(entity) {
    rect = Cesium.Rectangle.fromCartesianArray(entity.polyline.positions.getValue(), Cesium.Ellipsoid.WGS84);
    //dest_cartographic = Cesium.Rectangle.center(rect);
    //enforce max height.
    //if(dest_cartographic.height < 150000)
    //  dest_cartographic.height = 150000;
    //dest = Cesium.Cartesian3.fromRadians(dest_cartographic.longitude, dest_cartographic.latitude, dest_cartographic.height);
    this.cesium.camera.flyTo({destination: rect});
  }
}

//toggles the visibility of the outline by its id.
DrawMap.prototype.toggle_outline_by_id = function(id, val) {
  var entity = this.cesium.entities.getById(id+"_outline");
  if(entity) {
    if(val !== undefined) {
      entity.show = val;
    } else
       entity.show = !entity.show;
  }
}

//toggles the visibility of the image by its id.
DrawMap.prototype.toggle_visibility_by_id = function(id, val) {
   //var entity = this.cesium.entities.getById(id);
   var entity = this.images[id];
   if(entity) {
     if(val !== undefined) {
       entity.show = val;
     } else
        entity.show = !entity.show;
   }
}

//deletes and image and its outline by their ids.
DrawMap.prototype.remove_image_by_id = function(id) {
    this.cesium.imageryLayers.remove(this.images[id]);
    //this.cesium.entities.removeById(id);
    this.cesium.entities.removeById(id+"_outline");
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
