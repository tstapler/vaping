import logging
from icmplib import ping

import confu.schema

import vaping
from vaping.plugins import TimedProbeSchema


class ICMPSchema(TimedProbeSchema):
    """
    Define a schema for ICMP and also define defaults.
    """

    count = confu.schema.Int(default=5, help="Number of pings to send")
    interval = confu.schema.Str(default="1m", help="Time between pings")
    output = confu.schema.List(
        item=confu.schema.Str(), help="Determine what plugin displays output"
    )
    ping_interval = confu.schema.Float(
        default=0.2,
        help="Time in seconds between successive packets to an individual target",
    )


@vaping.plugin.register("icmp")
class ICMP(vaping.plugins.TimedProbe):
    """
    ICMP probe plugin using icmplib

    # Config

    - interval (`str=1m`): time between pings
    - count (`int=5`): number of pings to send
    - ping_interval (`float=0.2`): time in seconds between successive packets
    """

    ConfigSchema = ICMPSchema

    def __init__(self, config, ctx):
        super().__init__(config, ctx)
        self.count = self.config.get("count")
        self.ping_interval = self.config.get("ping_interval")
        self.hosts = []

    def init(self):
        """Initialize the probe with hosts from config"""
        self.hosts = []
        # Handle both legacy dict and new list format for groups
        if isinstance(self.config.get("groups"), dict):
            # Legacy format
            for name, group_config in list(self.config["groups"].items()):
                self.hosts.extend(group_config.get("hosts", []))
        else:
            # New format
            for group_config in self.config.get("groups", []):
                self.hosts.extend(group_config.get("hosts", []))

    def get_host_address(self, host):
        """Extract host address from config item"""
        if isinstance(host, dict):
            return host["host"]
        return host

    def probe(self):
        """
        Probe the configured hosts using icmplib
        """
        msg = self.new_message()
        data = []

        for host in self.hosts:
            try:
                addr = self.get_host_address(host)
                result = ping(
                    addr,
                    count=self.count,
                    interval=self.ping_interval,
                    privileged=False
                )

                if result.packets_received > 0:
                    host_data = {
                        "host": addr,
                        "data": result.rtts,
                        "min": result.min_rtt,
                        "avg": result.avg_rtt,
                        "max": result.max_rtt,
                        "cnt": result.packets_sent,
                        "loss": result.packet_loss,
                        "last": result.rtts[-1] if result.rtts else None,
                        "jitter": result.jitter
                    }
                else:
                    host_data = {
                        "host": addr,
                        "cnt": result.packets_sent,
                        "loss": 1.0
                    }

                data.append(host_data)

            except Exception as e:
                logging.error(f"failed to probe host {host}: {e}")
                data.append({})

        msg["data"] = data
        return msg
