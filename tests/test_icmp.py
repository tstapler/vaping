import pytest
import vaping.daemon
import vaping.plugins.icmp
from vaping import plugin

def test_icmp_probe():
    config = {
        "interval": "5s",
        "count": 2,
        "ping_interval": 0.2,
        "groups": {
            "test_group": {
                "hosts": ["127.0.0.1"]
            }
        }
    }
    
    probe = vaping.plugins.icmp.ICMP(config, None)
    probe.init()
    
    msg = probe.probe()
    assert msg
    assert "data" in msg
    assert len(msg["data"]) == 1
    
    data = msg["data"][0]
    assert data["host"] == "127.0.0.1"
    assert data["cnt"] == 2
    assert isinstance(data["loss"], float)
    assert 0 <= data["loss"] <= 1
    
    if data["loss"] < 1:
        assert "min" in data
        assert "avg" in data
        assert "max" in data
        assert "jitter" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
