# This is used to correct a hopefully transient
# issue in the opendatacube/cube-in-a-box image.
FROM opendatacube/cube-in-a-box

USER root

RUN chown root:root /usr/bin/sudo
RUN chown root:root /etc/sudoers
RUN chown root:root /usr/lib/sudo/sudoers.so
RUN chown -R 0:0 /etc/sudoers.d
