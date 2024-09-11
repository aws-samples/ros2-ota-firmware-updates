# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from awscrt import io
from awsiot.greengrass_discovery import DiscoveryClient
from awsiot import mqtt_connection_builder


def get_mqtt_connection(thing_name, key, cert, region):
    tls_options = io.TlsContextOptions.create_client_with_mtls_from_path(cert, key)
    tls_context = io.ClientTlsContext(tls_options)

    socket_options = io.SocketOptions()

    proxy_options = None

    print("Performing greengrass discovery...")
    discovery_client = DiscoveryClient(
        io.ClientBootstrap.get_or_create_static_default(),
        socket_options,
        tls_context,
        region,
        None,
        proxy_options,
    )
    resp_future = discovery_client.discover(thing_name)
    discover_response = resp_future.result()

    def on_connection_interupted(connection, error, **kwargs):
        print("connection interrupted with error {}".format(error))

    def on_connection_resumed(connection, return_code, session_present, **kwargs):
        print(
            "connection resumed with return code {}, session present {}".format(
                return_code, session_present
            )
        )

    for gg_group in discover_response.gg_groups:
        for gg_core in gg_group.cores:
            for connectivity_info in gg_core.connectivity:
                try:
                    print(
                        f"Trying core {gg_core.thing_arn} at host {connectivity_info.host_address} port {connectivity_info.port}"
                    )
                    mqtt_connection = mqtt_connection_builder.mtls_from_path(
                        endpoint=connectivity_info.host_address,
                        port=connectivity_info.port,
                        cert_filepath=cert,
                        pri_key_filepath=key,
                        ca_bytes=gg_group.certificate_authorities[0].encode("utf-8"),
                        on_connection_interrupted=on_connection_interupted,
                        on_connection_resumed=on_connection_resumed,
                        client_id=thing_name,
                        clean_session=False,
                        keep_alive_secs=30,
                    )

                    connect_future = mqtt_connection.connect()
                    connect_future.result()
                    print("Connected!")
                    return mqtt_connection

                except Exception as e:
                    print("Connection failed with exception {}".format(e))
                    continue

    raise RuntimeError("All connection attempts failed")
