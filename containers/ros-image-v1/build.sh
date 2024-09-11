#!/bin/sh

REGISTRY="localhost:5555"
THING="device-thing-1-firmware"
VERSIONS=3
for (( i=1; i <= $VERSIONS; ++i ))
do
    echo "Building version $i"
    docker build -t "firmware:$i" --build-arg "VERSION=$i" --build-arg "HEALTH=True" --build-arg "THING_NAME=$THING" --build-arg "TOPIC=clients/$THING/hello/world" .
    docker tag "firmware:$i" "$REGISTRY/firmware:$i"
    docker push "$REGISTRY/firmware:$i"
done
