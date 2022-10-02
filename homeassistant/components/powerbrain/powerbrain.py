"""cFos Powerbrain http API interface."""

import requests

API_GET_PARAMS = "/cnf?cmd=get_params"
API_GET_DEV_INFO = "/cnf?cmd=get_dev_info"


class Device:
    """Device connected via Powerbrain."""

    def __init__(self, attr):
        """Initialize the device instance."""
        self.name = attr["name"]
        self.dev_id = attr["dev_id"]
        self.attributes = attr

    def update_status(self, attr):
        """Update attributes."""
        self.attributes = attr


class Powerbrain:
    """Powerbrain charging controller class."""

    def __init__(self, host):
        """Initialize the Powerbrain instance."""
        self.host = host
        self.name = ""
        self.devices = {}
        self.attributes = {}

    def get_params(self):
        """Get powerbrain attributes and available devices."""

        dev_info = requests.get(self.host + API_GET_DEV_INFO, timeout=5).json()

        params = dev_info["params"]
        self.name = params["title"]
        self.attributes = params

        for device_attr in dev_info["devices"]:
            if device_attr["device_enabled"]:
                self.devices[device_attr["dev_id"]] = Device(device_attr)

    def update_device_status(self):
        """Update the device status."""
        dev_info = requests.get(self.host + API_GET_DEV_INFO, timeout=5).json()
        for k, device in self.devices.items():
            attr = next((x for x in dev_info["devices"] if x["dev_id"] == k), "")
            device.update_status(attr)
