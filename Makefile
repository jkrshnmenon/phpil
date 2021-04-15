PWD ?= pwd_unknown
NS ?= 4rbit3r
IMAGE_NAME ?= $(notdir $(PWD))
TAG ?= latest
CONTAINER_NAME ?= php-debug

.PHONY: build release shell commit debug run exec

help:
	@echo ''
	@echo 'Usage: make [TARGET] [EXTRA_ARGUMENTS]'
	@echo 'Targets:'
	@echo '  build    	build docker image $(NS)/$(IMAGE_NAME):$(TAG)'
	@echo '  release	push docker image $(NS)/$(IMAGE_NAME):$(TAG)'
	@echo '  shell		test container for image $(NS)/$(IMAGE_NAME):$(TAG) as $(CONTAINER_NAME)'
	@echo '  exec		run container for image $(NS)/$(IMAGE_NAME):$(TAG) as $(CONTAINER_NAME)'
	@echo '  debug		run container for image $(NS)/$(IMAGE_NAME):$(TAG) as $(CONTAINER_NAME) with source mapped as volume'
	@echo '  commit	build and push docker image $(NS)/$(IMAGE_NAME):$(TAG)'
	@echo '  run		build and run docker image $(NS)/$(IMAGE_NAME):$(TAG) as $(CONTAINER_NAME)'
	@echo ''
	@echo 'Extra arguments:'
	@echo 'TAG=:		make TAG="<tag>" (defaults to latest)'
	@echo 'IMAGE_NAME=:	make IMAGE_NAME="<image_name>" (defaults to directory name)'
	@echo 'CONTAINER_NAME=:make CONTAINER_NAME="<container_name>" (defaults to "default_instance")'

build:
	docker build -t $(NS)/$(IMAGE_NAME):$(TAG) .

release: 
	docker push $(NS)/$(IMAGE_NAME):$(TAG)

exec:
	docker run --rm -v $(PWD)/workspace:/home/hacker/workspace --name $(CONTAINER_NAME) -it $(NS)/$(IMAGE_NAME):$(TAG)

shell: build
	docker run --rm -v $(PWD)/workspace:/home/hacker/workspace --name $(CONTAINER_NAME) -it $(NS)/$(IMAGE_NAME):$(TAG) bash

debug: build
	docker run --rm -v $(PWD):/home/hacker/phpil --name $(CONTAINER_NAME) -it $(NS)/$(IMAGE_NAME):$(TAG) /bin/bash

commit: build release

run: build exec
	
