#!/bin/sh

export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0
export DOCKER_DEFAULT_PLATFORM=linux/amd64

VERSION=0.0.9
echo "BUILD image asia-southeast1-docker.pkg.dev/ghn-platforms/ghn-tools/sonarqube-exporter:$VERSION"
docker buildx build --platform linux/amd64 -t asia-southeast1-docker.pkg.dev/ghn-platforms/ghn-tools/sonarqube-exporter:$VERSION .

echo PUSH image
docker push asia-southeast1-docker.pkg.dev/ghn-platforms/ghn-tools/sonarqube-exporter:$VERSION
