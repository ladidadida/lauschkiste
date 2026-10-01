# MQTT Integration

The MQTT integration allows you to control your Lauschkiste via the MQTT protocol. This feature enables not only MQTT
control but also integration with home automation systems like Home Assistant.

## Configuration

Set the corresponding setting in `shared\settings\lauschkiste.yaml` to activate this feature.

``` yaml
modules:
    named:
        ...
        mqtt: mqtt
...
mqtt:
    enable: true
    # The prefix for the mqtt topic. /{base_topic}/{topic}
    base_topic: lauschkiste-dev
    # Enable support for legacy commands. Only needed for compatiblity to previous lauschkiste mqtt integration.
    enable_legacy: false
    # The client id used in communication with the MQTT broker and identification of the lauschkiste
    client_id: lauschkiste_dev
    # The username to authenticate against the broker
    username: lauschkiste-dev
    # The password to authenticate against the broker
    password: lauschkiste-dev
    # The host name or IP address of your mqtt broker
    host: 127.0.0.1
    # The port number of the mqtt broker. The default is 1883
    port: 1883
```

## Usage in Home Assistant

Home Assistant does not have a native MQTT Media Player integration. To integrate Lauschkiste into Home Assistant, you
can use the Universal Media Player configuration in combination with the Home Assistant MQTT service.

There is also an HACS addon adding Phoniebox as Media Player [Hass Phoniebox](https://github.com/c0un7-z3r0/hass-phoniebox).
