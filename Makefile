BUILD_VARS=

CONFIG_DIR ?= $(PWD)/config
BUILD_VARS+=CONFIG_DIR=$(CONFIG_DIR)

PROTOS_DIR ?= $(PWD)/protos
BUILD_VARS+=PROTOS_DIR=$(PROTOS_DIR)

BUILD_DIR ?= $(PWD)/build
BUILD_VARS+=BUILD_DIR=$(BUILD_DIR)

PYTHONPATH=$(BUILD_DIR)/python/bifrostv1


NGROK=$(PWD)/.local/bin/ngrok
$(NGROK):
	-mkdir -p $(shell dirname $(NGROK))
	curl -o $(NGROK)  https://s3-eu-west-1.amazonaws.com/sequenceiq/ngrok_linux
	chmod +x $(NGROK)


all:
	$(error You must explicitly use 'make compile')


image:
	docker pull dillonhicks/gotham:latest


compile: image
	@echo === Build Variables ===
	@echo $(BUILD_VARS) | xargs -n1 echo
	@echo =======================
	@echo

	docker run --rm \
		-v $(CONFIG_DIR):/app/config \
	  	-v $(PROTOS_DIR):/app/protos \
	  	-v $(BUILD_DIR):/app/build \
	  	-t dillonhicks/gotham:latest \


export PYTHONPATH
runserver:
	python server.py --with-proxy-server


run-ngrokd: $(NGROK)
	docker run --rm \
		-p 4480:4480 \
		-p 4444:4444 \
		-p 4443:4443 \
		sequenceiq/ngrokd \
			-httpAddr=:4480 \
			-httpsAddr=:4444 \
			-domain=bifrost.valhalla


export PYTHONPATH
ipython:
	ipython


testserver:
	curl http://localhost:9090/v1/echo/Sir/Good%20Day
	@echo
	curl http://localhost:9090/v1/echo/Potato/Die
	@echo
	curl http://localhost:9090/v1/echo/!!!!/dasf
	@echo
	curl http://localhost:9090/v1/echo/World/Hello
	@echo
