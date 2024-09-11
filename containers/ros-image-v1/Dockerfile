FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
        && apt-get -y install --no-install-recommends python3-pip less vim curl unzip mandoc \
        #
        # Clean up
        && apt-get autoremove -y \
        && apt-get clean -y \
        && rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=dialog

RUN python3 -m pip install awsiotsdk \
        && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
        && unzip awscliv2.zip \
        && ./aws/install

RUN mkdir -p /agent
RUN mkdir -p /ros_ws
RUN mkdir -p /config

COPY agent /agent/
COPY ws /ros_ws/
COPY config /config/

ARG THING_NAME
ENV THING_NAME=$THING_NAME

ARG TOPIC
ENV TOPIC=$TOPIC

ARG VERSION
ENV VERSION=$VERSION

ARG HEALTH
ENV HEALTH=$HEALTH

RUN bash -c "source /opt/ros/humble/setup.bash && bash /agent/build.sh"

ENTRYPOINT ["/agent/entrypoint.sh"]