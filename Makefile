# You can follow the steps below in order to get yourself a local ODC.
# Once running, you can access a Jupyter environment 
# at 'http://localhost' with password 'secretpassword'
SHELL:=/bin/bash
docker_compose_dev = docker-compose --project-directory docker/dev -f docker/dev/docker-compose.yml

## Common ##

dev-build:
	$(docker_compose_dev) build

# Start the notebooks environment
dev-up:
	$(docker_compose_dev) up -d --build

# Start without rebuilding the Docker image
# (use when dependencies have not changed for faster starts).
dev-up-no-build:
	$(docker_compose_dev) up -d

# Stop the notebooks environment
dev-down:
	$(docker_compose_dev) down

dev-down-remove-orphans:
	$(docker_compose_dev) down --remove-orphans

dev-restart: dev-down dev-up

dev-restart-no-build: dev-down dev-up-no-build

# List the running containers.
dev-ps:
	$(docker_compose_dev) ps

# Start an interactive shell
dev-ssh:
	$(docker_compose_dev) exec jupyter bash

# Delete everything
dev-clear:
	$(docker_compose_dev) stop
	$(docker_compose_dev) rm -fs

odc-db-ssh:
	docker exec -it odc-db bash

dev-odc-db-init:
	$(docker_compose_dev) exec jupyter datacube system init

## End Common ##

## ODC Docker Network ##

# Create the `odc` network on which everything runs.
create-odc-network:
	docker network create odc

delete-odc-network:
	docker network rm odc

## End ODC Docker Network ##

## ODC DB ##

# Create the persistent volume for the ODC database.
create-odc-db-volume:
	docker volume create odc-db-vol

# Delete the persistent volume for the ODC database.
delete-odc-db-volume:
	docker volume rm odc-db-vol

# Create the ODC database Docker container.
create-odc-db:
	docker run -d \
	-e POSTGRES_DB=datacube \
	-e POSTGRES_USER=dc_user \
	-e POSTGRES_PASSWORD=localuser1234 \
	--name=odc-db \
	--network="odc" \
	-v odc-db-vol:/var/lib/postgresql/data \
	postgres:10-alpine

start-odc-db:
	docker start odc-db

stop-odc-db:
	docker stop odc-db

restart-odc-db: stop-odc-db start-odc-db

delete-odc-db:
	docker rm odc-db

## End ODC DB ##

## Adding Data ##

# Add a product definition for landsat level 1
dev-add-product-def:
	$(docker_compose_dev) exec jupyter datacube product add \
		https://raw.githubusercontent.com/opendatacube/datacube-dataset-config/master/products/ls_usgs_level1_scene.yaml

# Index a dataset (just an example, you can change the extents)
dev-index:
	$(docker_compose_dev) exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 ./autoIndex.py \
			--start_date '2019-01-01' \
			--end_date '2020-01-01' \
			--extents '146.30,146.83,-43.54,-43.20'"

## End Adding Data ##

sudo-ubuntu-install-docker:
	sudo apt-get update
	sudo apt install -y docker.io docker-compose
	sudo systemctl start docker
	sudo systemctl enable docker
	# The following steps are for enabling use 
	# of the `docker` command for the current user
	# without using `sudo`
	getent group docker || sudo groupadd docker
	sudo usermod -aG docker ${USER}

# Update S3 template (this is owned by Digital Earth Australia)
upload-s3:
	aws s3 cp cube-in-a-box-cloudformation.yml s3://opendatacube-cube-in-a-box/ --acl public-read

# This section can be used to deploy onto CloudFormation instead of the 'magic link'
create-infra:
	aws cloudformation create-stack \
		--region ap-southeast-2 \
		--stack-name odc-test \
		--template-body file://opendatacube-test.yml \
		--parameter file://parameters.json \
		--tags Key=Name,Value=OpenDataCube \
		--capabilities CAPABILITY_NAMED_IAM

update-infra:
	aws cloudformation update-stack \
		--stack-name odc-test \
		--template-body file://opendatacube-test.yml \
		--parameter file://parameters.json \
		--tags Key=Name,Value=OpenDataCube \
		--capabilities CAPABILITY_NAMED_IAM
