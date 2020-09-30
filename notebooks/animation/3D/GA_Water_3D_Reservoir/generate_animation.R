
library(rayshader)
library(magrittr)
library(raster)
library(lubridate)
library(dplyr)

smooth_sequence = function(from=0, to=1, cycles=2, n=180) {
  
  #' Produces a smooth sequence of any length between two values
  #'
  #' @param cycles The number of cycles to repeat the 'from'-'to' sequence. The default is 2,
  #'   which cycles from the 'from' value to the 'to' value, then back again. Set to 1 to 
  #'   produce a smoothed sequence from 'from' to 'to' without returning back to 'from'.
  
  cos_scale = cos(seq(0, cycles*pi, length.out = n))
  scales::rescale(cos_scale, to=c(to, from))
  
}

raster_rescale <- function(x, new.min = 0, new.max = 1) {
  
  x.min = cellStats(x, "min")
  x.max = cellStats(x, "max")
  
  if(is.null(x.min)) x.min = min(x)
  if(is.null(x.max)) x.max = max(x)
  new.min + (x - x.min) * ((new.max - new.min) / (x.max - x.min))
}

vector_rescale <- function(x, new.min = 0, new.max = 1) {
  
  x.min = min(x)
  x.max = max(x)
  
  new.min + (x - x.min) * ((new.max - new.min) / (x.max - x.min))
}


# Set working directory
setwd('.')

# Analysis name
name = 'inundation_perc'

output_dir = "output/example/"
###############
# Read in CSV #
###############

reservoir_ts = read.csv(paste0(output_dir, name, "_timeseries.csv"))
timesteps = nrow(reservoir_ts)
reservoir_ts['month'] = month(as.POSIXlt(reservoir_ts$date, format="%Y-%m-%d"), label=TRUE)
reservoir_ts['year'] = year(as.POSIXlt(reservoir_ts$date, format="%Y-%m-%d"))
reservoir_ts %<>% mutate(month_year = paste(month, year))


###################
# Read in rasters #
###################

# Import raster
localtif = raster::raster(paste0(output_dir, name, "_dem.tif"))
localtif = t(localtif)
localtif_clip = localtif 

# Set NANs to zero and convert to matrix
localtif_clip[is.na(localtif_clip)] = 0
elevation_matrix = matrix(raster::extract(localtif_clip,
                                          raster::extent(localtif_clip),
                                          buffer=1000),
                          nrow=ncol(localtif_clip),
                          ncol=nrow(localtif_clip))

# Import RGB and scale between 1 and 0
rgb_tif_clip = raster::stack(paste0(output_dir, name, "_rgb.tif"))
rgb_tif_clip = t(rgb_tif_clip)
rgb_matrix = raster::as.array(rgb_tif_clip)
rgb_matrix = rgb_matrix / 10000.0

# Compute shadows
ray_shade_data = ray_shade(elevation_matrix, remove_edges = FALSE, sunangle = 110, 
                           anglebreaks=seq(20,30,1), 
                           zscale=1)
ambient_shade_data = ambient_shade(elevation_matrix, remove_edges = FALSE)


####################
# Animation params #
####################

scale_factor = 1.0
waterdepth_values = (reservoir_ts$innundation_perc / scale_factor) * 100 + 1.5
wateralpha_values = vector_rescale(reservoir_ts$innundation_perc, 
                                   new.min = 0.55, 
                                   new.max = 0.9)
azimuth_values = rep(45, timesteps)  
rotation_values = seq(0, 360, length.out=timesteps) 
fov_values = rep(25, timesteps)  
watercolor = '#78b0aa'


#################
# Export frames #
#################

for(i in 1:(length(waterdepth_values)-1)) {
  
  print(i) 
  
  rgb_matrix %>% 
    add_shadow(ray_shade_data) %>%
    add_shadow(ambient_shade_data) %>%
    # print(paste0(typeof(elevation_matrix)))
    # print(paste0(typeof(waterdepth_values)))
    plot_3d(elevation_matrix, solid = TRUE, shadow = TRUE, water = TRUE, zscale = scale_factor,
            waterdepth =waterdepth_values[i], wateralpha = wateralpha_values[i], watercolor = watercolor,
            waterlinealpha = 0.5, theta = rotation_values[i], phi = azimuth_values[i], fov=fov_values[i], 
            zoom=0.92, windowsize=c(1000, 1000))
  
  # Add title
  rgl::bgplot3d({plot.new()
                 title(main=paste0(reservoir_ts$month_year[i]), line = -3,
                       cex.main = 2,   font.main= 2, col.main= "black")})
  
  # Save to file and close
  rgl::snapshot3d(paste0("figures/", name, "_", i,".png"))
  rgl::rgl.close() 
  
}


#################################
# Combine frames into animation #
#################################

# ffmpeg -y -start_number 1 -i figures/inundation_perc_%d.png -r 18 -vb 3M -filter_complex "setpts=1.5*PTS,crop=900:900:50:50,colorlevels=romin=0.13:gomin=0.13:bomin=0.13" -pix_fmt yuv420p -vcodec libx264 inundation_perc.mp4