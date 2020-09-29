
FROM opendatacube/geobase:wheels-3.0.4  as env_builder

ARG py_env_path=/env

RUN mkdir -p /conf
COPY base_requirements.txt /conf/
RUN env-build-tool new /conf/base_requirements.txt ${py_env_path} /wheels

FROM opendatacube/geobase:runner-3.0.4
ARG py_env_path

COPY --from=env_builder $py_env_path $py_env_path
COPY --from=env_builder /bin/tini /bin/tini

RUN useradd -m -s /bin/bash -N jovyan
# Let jovyan run sudo without a password.
RUN echo "jovyan ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
RUN sudo chown -R jovyan /env

RUN apt-get update -y \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --fix-missing --no-install-recommends \
  # developer convenience
  postgresql-client-10 \
  less \
  vim \
  git \
  && rm -rf /var/lib/apt/lists/*

COPY extra_requirements.txt /conf/

RUN . /env/bin/activate && pip3 install \
    # This Python packages index is Digital Earth Australia's package index.
    # Used for installing the odc-tools package (provides an `odc` module).
    --extra-index-url="https://packages.dea.ga.gov.au" \
    -r /conf/extra_requirements.txt

RUN export GDAL_DATA=$(gdal-config --datadir)
ENV LC_ALL=C.UTF-8 \
    PATH="/env/bin:$PATH"

ARG NOTEBOOK_ROOT
ENV NOTEBOOK_ROOT=${NOTEBOOK_ROOT}
WORKDIR ${NOTEBOOK_ROOT}

ENTRYPOINT ["/bin/tini", "--"]

USER jovyan
CMD ["jupyter", "notebook", "--allow-root", "--ip='0.0.0.0'" "--NotebookApp.token='secretpassword'"]
