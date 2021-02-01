FROM jcrattzama/cube-in-a-box:odc1.8.3

USER root

# Let jovyan run sudo without a password.
# RUN echo "jovyan ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
# RUN chown -R jovyan /env

RUN pip3 install --upgrade pip

# Setup the Open Data Cube configuration.
ARG ODC_DB_HOSTNAME="odc-db"
ARG ODC_DB_DATABASE="datacube"
ARG ODC_DB_USER="dc_user"
ARG ODC_DB_PASSWORD="localuser1234"
ARG ODC_DB_PORT="5432"
ENV ODC_DB_HOSTNAME=${ODC_DB_HOSTNAME} \
    ODC_DB_DATABASE=${ODC_DB_DATABASE} \
    ODC_DB_USER=${ODC_DB_USER} \
    ODC_DB_PASSWORD=${ODC_DB_PASSWORD} \
    ODC_DB_PORT=${ODC_DB_PORT}
RUN mkdir -p /config && echo "\
[datacube] \n\
db_hostname: ${ODC_DB_HOSTNAME} \n\
db_database: ${ODC_DB_DATABASE} \n\
db_username: ${ODC_DB_USER} \n\
db_password: ${ODC_DB_PASSWORD} \n" > /config/datacube.conf
RUN cp /config/datacube.conf /etc/datacube.conf
ENV DATACUBE_CONFIG_PATH=/config/datacube.conf

ARG NOTEBOOK_ROOT
ENV NOTEBOOK_ROOT=${NOTEBOOK_ROOT}
WORKDIR ${NOTEBOOK_ROOT}

USER jovyan
ENTRYPOINT ["/bin/tini", "--"]
CMD ["jupyter", "notebook", "--allow-root", "--ip='0.0.0.0'" "--NotebookApp.token='secretpassword'"]
