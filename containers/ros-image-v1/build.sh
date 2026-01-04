#!/bin/sh

REGISTRY="localhost:5555"
THING="device-thing-1-firmware"
VERSIONS=3
i=1
while [ $i -le $VERSIONS ]
do
    echo "Building version $i"
    docker build -t "firmware:$i" --build-arg "VERSION=$i" --build-arg "HEALTH=True" --build-arg "THING_NAME=$THING" --build-arg "TOPIC=clients/$THING/hello/world" .
    docker tag "firmware:$i" "$REGISTRY/firmware:$i"
    docker push "$REGISTRY/firmware:$i"
    i=$((i + 1))
done