IMAGE_REGISTRY := europe-west1-docker.pkg.dev/friendly-path-465518-r6/archestra-public
IMAGE_NAME := ai_sre_demo
IMAGE_TAG := latest
IMAGE := $(IMAGE_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: build push build-push clean help

## build: Build Docker image for linux/amd64 (required for GKE)
build:
	cd app && docker buildx build --platform linux/amd64 -t $(IMAGE) .

## push: Push Docker image to registry
push:
	docker push $(IMAGE)

## build-push: Build and push in one step
build-push:
	cd app && docker buildx build --platform linux/amd64 -t $(IMAGE) --push .

## clean: Remove local Docker image
clean:
	docker rmi $(IMAGE) || true

## help: Show this help message
help:
	@echo "AI SRE Demo - Available targets:"
	@echo ""
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'
	@echo ""
	@echo "Image: $(IMAGE)"
