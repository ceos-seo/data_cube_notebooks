FROM jcrattzama/cube-in-a-box:odc1.8.3
# jcrattzama/datacube-base:odc1.8.3

ARG BUILD_DIR=/build
ENV BUILD_DIR=${BUILD_DIR}
WORKDIR ${BUILD_DIR}

USER root

# Let jovyan run sudo without a password.
RUN echo "jovyan ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ARG UID
ENV UID=${UID}
RUN usermod -u ${UID} jovyan
RUN chown -R jovyan /env
# RUN find /env/* | xargs chown jovyan

# RUN apt-get install git tini -y

# RUN pip3 install --upgrade pip

# Install the graphviz system package for Dask
# (used through the graphviz Python library).
RUN apt-get update && apt-get install graphviz -y && \
    rm -rf /var/lib/apt/lists/*

# COPY requirements.txt requirements.txt
# RUN chown jovyan requirements.txt
# USER jovyan
# RUN pip3 install -r requirements.txt

# RUN chown -R jovyan reqs
USER jovyan
COPY build/reqs/01_reqs_build.txt reqs/01_reqs_build.txt
RUN pip3 install -r reqs/01_reqs_build.txt
COPY build/reqs/02_reqs_platform.txt reqs/02_reqs_platform.txt
RUN pip3 install -r reqs/02_reqs_platform.txt
RUN jupyter-lab build
COPY build/reqs/03_reqs_gis.txt reqs/03_reqs_gis.txt
RUN pip3 install -r reqs/03_reqs_gis.txt
COPY build/reqs/04_reqs_odc.txt reqs/04_reqs_odc.txt
RUN pip3 install -r reqs/04_reqs_odc.txt
COPY build/reqs/05_reqs_scale.txt reqs/05_reqs_scale.txt
RUN pip3 install -r reqs/05_reqs_scale.txt
COPY build/reqs/06_reqs_test.txt reqs/06_reqs_test.txt
RUN pip3 install -r reqs/06_reqs_test.txt
COPY build/reqs/07_reqs_raster.txt reqs/07_reqs_raster.txt
RUN pip3 install -r reqs/07_reqs_raster.txt
COPY build/reqs/08_reqs_geom.txt reqs/08_reqs_geom.txt
RUN pip3 install -r reqs/08_reqs_geom.txt
COPY build/reqs/09_reqs_ml.txt reqs/09_reqs_ml.txt
RUN pip3 install -r reqs/09_reqs_ml.txt
COPY build/reqs/10_reqs_data_load.txt reqs/10_reqs_data_load.txt
RUN pip3 install -r reqs/10_reqs_data_load.txt
COPY build/reqs/11_reqs_analysis.txt reqs/11_reqs_analysis.txt
RUN pip3 install -r reqs/11_reqs_analysis.txt
COPY build/reqs/12_reqs_vis.txt reqs/12_reqs_vis.txt
RUN pip3 install -r reqs/12_reqs_vis.txt
COPY build/reqs/13_reqs_voxel_visualizer.txt reqs/13_reqs_voxel_visualizer.txt
RUN pip3 install -r reqs/13_reqs_voxel_visualizer.txt
COPY build/reqs/14_reqs_misc.txt reqs/14_reqs_misc.txt
RUN pip3 install -r reqs/14_reqs_misc.txt

# RUN pip3 install rasterio==1.1.8 && \
#     mkdir -p /etc/pki/tls/certs && \
#     ln -s /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt
RUN pip3 install --no-binary=rasterio rasterio==1.1.8 GDAL==$(gdal-config --version)

# Set config directory for Matplotlib to avoid warnings.
ENV MPLCONFIGDIR=/var/jovyan/.config/matplotlib

# Install the ODC-GEE package.
COPY odc_gee odc_gee
USER root
RUN cd odc_gee; python3 setup.py build && python3 setup.py install
# Set the recently changed or added packages' ownership to jovyan. 
RUN find /env/lib/python3.6/site-packages -group root -mtime -1 -exec chown -R jovyan:users {} +

# Setup the ODC configuration.
ENV ODC_DB_HOSTNAME \
    ODC_DB_DATABASE \
    ODC_DB_USER \
    ODC_DB_PASSWORD \
    ODC_DB_PORT
COPY build/native/odc_conf.sh native/odc_conf.sh

# Install ODC-GEE.
COPY odc_gee odc_gee
RUN cd odc_gee; python3 setup.py build && python3 setup.py install
# Set the recently changed or added packages' ownership to jovyan. 
RUN find /env/lib/python3.6/site-packages -group root -mtime -1 -exec chown -R jovyan:users {} +

# Create the main directory.
ARG ROOT_DIR
ARG NOTEBOOK_ROOT
ENV ROOT_DIR=${ROOT_DIR} NOTEBOOK_ROOT=${NOTEBOOK_ROOT}
RUN mkdir -p ${ROOT_DIR}; chown -R jovyan ${ROOT_DIR}

COPY build/native/entrypoint.sh native/entrypoint.sh
RUN chown -R jovyan:users ${BUILD_DIR}
RUN chmod 777 -R ${BUILD_DIR}
USER jovyan
WORKDIR ${ROOT_DIR}
ENV NBK_SERVER_PASSWORD=${NBK_SERVER_PASSWORD}
ENV AWS_ACCESS_KEY_ID \
    AWS_SECRET_ACCESS_KEY \
    AWS_DEFAULT_REGION
ENTRYPOINT ["/build/native/entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
