# GA_Water_3D_Reservoir

First run `GA_Water_3DReservoir.ipynb` to create files that `generate_animation.R` will use to generate the animation. Files are written to the `output/example` directory unless specified otherwise.

If R is not already installed, install it. Run these commands to do so on Ubuntu 18.04:

```
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
sudo apt-get install software-properties-common
sudo add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu bionic-cran40/'
sudo apt update
sudo apt install r-base
sudo apt-get -y install libcurl4-gnutls-dev libxml2-dev mesa-common-dev libglu1-mesa-dev freeglut3-dev libmagick++-dev

sudo apt-get install libmagick++-dev
```

Now open the R console (`R` command) and run these commands to install some packages:

```
install.packages('rayshader')
install.packages('lubridate')
install.packages('dplyr')
install.packages('rgdal')
install.packages('magick')
```

Now run `R -f generate_animation.R` to generate images of the water extent animation in a new `figures` directory. These can be combined into an animation called `inundation_perc.mp4` (inundation percent) with the command `ffmpeg -y -start_number 1 -i figures/inundation_perc_%d.png -r 18 -vb 3M -filter_complex "setpts=1.5*PTS,crop=900:900:50:50,colorlevels=romin=0.13:gomin=0.13:bomin=0.13" -pix_fmt yuv420p -vcodec libx264 inundation_perc.mp4`.

If you want to generate a new animation, move the `output/example` directory somewhere else - like `output/<name-of-water-body>`. Also move the `inundation_perc.mp4` file somewhere else to avoid overwriting it.