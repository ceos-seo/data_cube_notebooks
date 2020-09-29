# You can follow the steps below in order to get yourself a local ODC.
# Once running, you can access a Jupyter environment 
# at 'http://localhost' with password 'secretpassword'
docker_compose = docker-compose --project-directory docker -f docker/docker-compose.yml

# 1. Start your Docker environment
up:
	$(docker_compose) up -d --build

up-no-build:
	$(docker_compose) up -d

restart: down up

restart-no-build: down up-no-build

down:
	$(docker_compose) down

ps:
	$(docker_compose) ps

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

# Create the persistent volume for the ODC database.
create-notebooks-odc-db-volume:
	docker volume create notebooks-odc-db-vol

# Delete the persistent volume for the ODC database.
delete-notebooks-odc-db-volume:
	docker volume rm notebooks-odc-db-vol

# 2. Prepare the database
initdb:
	$(docker_compose) exec jupyter datacube -v system init

# 3. Add a product definition for landsat level 1
product:
	$(docker_compose) exec jupyter datacube product add \
		https://raw.githubusercontent.com/opendatacube/datacube-dataset-config/master/products/ls_usgs_level1_scene.yaml

# 3. Index a dataset (just an example, you can change the extents)
index:
	$(docker_compose) exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 ./autoIndex.py \
			--start_date '2019-01-01' \
			--end_date '2020-01-01' \
			--extents '146.30,146.83,-43.54,-43.20'"

# Some extra commands to help in managing things.
# Rebuild the image
build:
	$(docker_compose) build

# Start an interactive shell
jupyter-shell:
	$(docker_compose) exec jupyter bash

postgres-shell:
	$(docker_compose) exec postgres bash

# Delete everything
clear:
	$(docker_compose) stop
	$(docker_compose) rm -fs

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
