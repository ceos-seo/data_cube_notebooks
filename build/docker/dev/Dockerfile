FROM jcrattzama/cube-in-a-box:odc1.8.3
# jcrattzama/datacube-base:odc1.8.3

ARG BUILD_DIR=/tmp/build
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

COPY requirements.txt requirements.txt
RUN chown jovyan requirements.txt
USER jovyan
RUN pip3 install -r requirements.txt
# RUN pip3 install rasterio==1.1.8 && \
#     mkdir -p /etc/pki/tls/certs && \
#     ln -s /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt
RUN pip3 install --no-binary=rasterio rasterio==1.1.8 GDAL==$(gdal-config --version)

USER root

# Setup the ODC configuration.
# ARG ODC_DB_HOSTNAME="odc-db"
# ARG ODC_DB_DATABASE="datacube"
# ARG ODC_DB_USER="dc_user"
# ARG ODC_DB_PASSWORD="localuser1234"
# ARG ODC_DB_PORT="5432"
# ENV ODC_DB_HOSTNAME=${ODC_DB_HOSTNAME} \
#     ODC_DB_DATABASE=${ODC_DB_DATABASE} \
#     ODC_DB_USER=${ODC_DB_USER} \
#     ODC_DB_PASSWORD=${ODC_DB_PASSWORD} \
#     ODC_DB_PORT=${ODC_DB_PORT}
ENV ODC_DB_HOSTNAME \
    ODC_DB_DATABASE \
    ODC_DB_USER \
    ODC_DB_PASSWORD \
    ODC_DB_PORT
# RUN mkdir -p /config && echo "\
# [datacube] \n\
# db_hostname: ${ODC_DB_HOSTNAME} \n\
# db_database: ${ODC_DB_DATABASE} \n\
# db_username: ${ODC_DB_USER} \n\
# db_password: ${ODC_DB_PASSWORD} \n" > /config/datacube.conf
# RUN cp /config/datacube.conf /etc/datacube.conf
# ENV DATACUBE_CONFIG_PATH=/config/datacube.conf
COPY build/native/odc_conf.sh native/odc_conf.sh

ARG NOTEBOOK_ROOT
ENV NOTEBOOK_ROOT=${NOTEBOOK_ROOT}
RUN chown -R jovyan ${NOTEBOOK_ROOT}

# ENTRYPOINT ["/bin/tini", "--"]
COPY build/native/entrypoint.sh native/entrypoint.sh
RUN chmod 555 native/entrypoint.sh
WORKDIR ${NOTEBOOK_ROOT}
USER jovyan
ENTRYPOINT ["${BUILD_DIR}/build/native/entrypoint.sh"]
# ENTRYPOINT ["tail", "-f", "/dev/null"]
# CMD ["tail", "-f", "/dev/null"]
CMD ["jupyter", "notebook", "--allow-root", "--ip='0.0.0.0'" "--NotebookApp.token='secretpassword'"]
