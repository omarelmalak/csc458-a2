from pathlib import Path

import pytest

from csc458_pa2.addressing import endpoint_ip, stub_prefix
from csc458_pa2.core_harness import CoreHarness
from csc458_pa2.linux_routes import LinuxRouteManager
from csc458_pa2.model import INFINITY, Route
from csc458_pa2.topology import Topology

ROOT = Path(__file__).resolve().parents[1]
TOPOS = ROOT / "topologies"


def harness(name: str, protocol: str, mode: str = "poison_reverse") -> CoreHarness:
    return CoreHarness(Topology.load(TOPOS / name), protocol, mode)


def test_address_allocator_is_deterministic():
    assert stub_prefix("R4") == "10.4.0.0/24"
    assert endpoint_ip("R1", "R2", "R1") != endpoint_ip("R1", "R2", "R2")


def test_dv_line_converges():
    h = harness("line4.json", "DV")
    h.converge()
    assert h.all_optimal()
    assert h.cores["R1"].get_route(stub_prefix("R4")) == Route(4, "R2")


def test_dv_weighted_mesh_uses_lowest_cost_not_fewest_hops():
    h = harness("weighted_mesh.json", "DV")
    h.converge()
    assert h.cores["R1"].get_route(stub_prefix("R5")) == Route(6, "R2")


def test_dv_failure_uses_alternate_path():
    h = harness("failure_alt.json", "DV")
    h.converge()
    h.link_down("R2", "R4")
    h.converge()
    assert h.cores["R1"].get_route(stub_prefix("R4")) == Route(4, "R3")


def test_dv_link_addition_is_learned():
    h = harness("link_addition.json", "DV")
    h.converge()
    h.link_up("R1", "R4", 1)
    h.converge()
    assert h.cores["R1"].get_route(stub_prefix("R4")) == Route(1, "R4")


def test_dv_poison_reverse_marks_route_infinite_to_its_next_hop():
    h = harness("line4.json", "DV", "poison_reverse")
    h.converge()
    r2 = h.cores["R2"]
    assert r2._advertisement_for("R3")[stub_prefix("R4")] == INFINITY


def test_dv_split_horizon_omits_route_to_its_next_hop():
    h = harness("line4.json", "DV", "split_horizon")
    h.converge()
    r2 = h.cores["R2"]
    assert stub_prefix("R4") not in r2._advertisement_for("R3")


def test_dv_basic_count_to_infinity_is_bounded_by_16():
    h = harness("count_to_infinity.json", "DV", "basic")
    h.converge()
    h.link_down("R1", "R2")
    # Deliver enough asynchronous exchanges to reach the assignment's infinity.
    for _ in range(40):
        h.step()
    for rid in ("R2", "R3"):
        route = h.cores[rid].routes.get(stub_prefix("R1"))
        assert route is None or route.metric <= INFINITY
        assert h.cores[rid].get_route(stub_prefix("R1")) is None


def test_ls_line_converges():
    h = harness("line4.json", "LS")
    h.converge()
    assert h.cores["R1"].get_route(stub_prefix("R4")) == Route(4, "R2")


def test_ls_weighted_mesh_converges():
    h = harness("weighted_mesh.json", "LS")
    h.converge()
    assert h.cores["R1"].get_route(stub_prefix("R5")) == Route(6, "R2")


def test_ls_failure_uses_alternate_path():
    h = harness("failure_alt.json", "LS")
    h.converge()
    h.link_down("R2", "R4")
    h.converge()
    assert h.cores["R1"].get_route(stub_prefix("R4")) == Route(4, "R3")


def test_ls_cost_change_recomputes_shortest_paths():
    h = harness("cost_change.json", "LS")
    h.converge()
    h.cost_change("R2", "R4", 8)
    h.converge()
    assert h.cores["R1"].get_route(stub_prefix("R4")) == Route(4, "R2")


def test_ls_link_addition_synchronizes_database():
    h = harness("link_addition.json", "LS")
    h.converge()
    h.link_up("R1", "R4", 1)
    h.converge()
    assert h.cores["R1"].get_route(stub_prefix("R4")) == Route(1, "R4")
    assert set(h.cores["R4"].lsdb) >= {"R1", "R2", "R3", "R4"}


def test_equal_cost_tie_break_is_deterministic():
    for protocol in ("DV", "LS"):
        h = harness("tie_break.json", protocol)
        h.converge()
        assert h.cores["R1"].get_route(stub_prefix("R4")) == Route(2, "R2")


def test_linux_route_manager_installs_and_removes_only_managed_routes():
    calls = []
    mgr = LinuxRouteManager({"R2": {"peer_ip": "10.254.0.2", "ifname": "r1-r2"}}, run=calls.append)
    mgr.sync({"10.4.0.99/24": Route(3, "R2")})
    assert calls[-1][:4] == ["ip", "route", "replace", "10.4.0.0/24"]
    mgr.sync({})
    assert calls[-1] == ["ip", "route", "del", "10.4.0.0/24"]


# =============================================================================
# Additional PUBLIC tests (TA review)
#
# Everything above this line is an unmodified copy of the original file.
# The tests below were added in the Fall 2026 TA review. Each one drives a
# single router core through a Recorder that logs every message it sends,
# so the harness's periodic refresh cannot mask a missing behaviour.
# =============================================================================
from csc458_pa2.dv_core import DVCore
from csc458_pa2.ls_core import LSCore
from csc458_pa2.model import ControlMessage


class Recorder:
    def __init__(self):
        self.sent: list[tuple[str, ControlMessage]] = []

    def send_control(self, neighbor, message):
        self.sent.append((neighbor, message))

    def clear(self):
        self.sent.clear()

    def to(self, neighbor):
        return [m for n, m in self.sent if n == neighbor]


def lsa(origin, seq, prefix, links):
    return ControlMessage("LS", {"type": "lsa", "origin": origin, "seq": seq, "prefix": prefix, "links": links})


def dv(vector):
    return ControlMessage("DV", {"type": "dv", "vector": vector})


def _ls_r1_with_neighbors(*neighbors):
    api = Recorder()
    r1 = LSCore("R1", "10.1.0.0/24", api)
    for n in neighbors:
        r1.on_link_change(n, 1)
    api.clear()
    return r1, api


def test_dv_triggered_update_after_received_vector_changes_table():
    api = Recorder()
    r2 = DVCore("R2", "10.2.0.0/24", api, "poison_reverse")
    r2.on_link_change("R1", 1)
    r2.on_link_change("R3", 1)
    api.clear()
    r2.on_control("R1", dv({"10.1.0.0/24": 0, "10.9.0.0/24": 2}))
    assert r2.get_route("10.9.0.0/24") == Route(3, "R1")
    # The table changed, so R2 must advertise immediately (no on_periodic call).
    assert any("10.9.0.0/24" in m.payload["vector"] for m in api.to("R3"))


def test_ls_recomputes_immediately_on_new_lsa():
    r1, _ = _ls_r1_with_neighbors("R2")
    r1.on_control("R2", lsa("R2", 5, "10.2.0.0/24", {"R1": 1, "R3": 1}))
    r1.on_control("R2", lsa("R3", 5, "10.3.0.0/24", {"R2": 1}))
    assert r1.get_route("10.3.0.0/24") == Route(2, "R2")


def test_ls_does_not_flood_back_to_sender():
    r1, api = _ls_r1_with_neighbors("R2", "R3")
    r1.on_control("R2", lsa("R4", 7, "10.4.0.0/24", {"R2": 1}))
    assert [m.payload["origin"] for m in api.to("R3")] == ["R4"]
    assert api.to("R2") == []


def test_ls_flooded_lsa_is_unchanged():
    r1, api = _ls_r1_with_neighbors("R2", "R3")
    original = lsa("R4", 7, "10.4.0.0/24", {"R2": 1, "R5": 3})
    r1.on_control("R2", original)
    (forwarded,) = api.to("R3")
    assert forwarded.payload == original.payload
