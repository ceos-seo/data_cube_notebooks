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
ENV ODC_DB_HOSTNAME \
    ODC_DB_DATABASE \
    ODC_DB_USER \
    ODC_DB_PASSWORD \
    ODC_DB_PORT
COPY build/native/odc_conf.sh native/odc_conf.sh

ARG NOTEBOOK_ROOT
ENV NOTEBOOK_ROOT=${NOTEBOOK_ROOT}
RUN chown -R jovyan ${NOTEBOOK_ROOT}

COPY build/native/entrypoint.sh native/entrypoint.sh
RUN chown -R jovyan:users ${BUILD_DIR}
RUN chmod 777 -R ${BUILD_DIR}
USER jovyan
WORKDIR ${NOTEBOOK_ROOT}
ENV NBK_SERVER_PASSWORD=${NBK_SERVER_PASSWORD}
ENV AWS_ACCESS_KEY_ID \
    AWS_SECRET_ACCESS_KEY \
    AWS_DEFAULT_REGION
ENTRYPOINT ["/build/native/entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
