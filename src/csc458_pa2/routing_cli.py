from __future__ import annotations

from .addressing import node_name


def make_routing_cli(lab):
    from mininet.cli import CLI

    class RoutingCLI(CLI):
        prompt = "csc458> "

        def do_link(self, line):
            "link r1 r2 down|up: change link state and keep the PA2 oracle in sync."
            parts = line.split()
            if len(parts) != 3 or parts[2] not in {"up", "down"}:
                print("usage: link r1 r2 up|down")
                return
            try:
                lab.set_link(parts[0], parts[1], parts[2] == "up")
            except Exception as e:
                print(f"error: {e}")

        def do_cost(self, line):
            "cost R1 R2 5: change the routing metric of an existing link."
            parts = line.split()
            if len(parts) != 3:
                print("usage: cost R1 R2 <1..15>")
                return
            try:
                lab.set_cost(parts[0], parts[1], int(parts[2]))
            except Exception as e:
                print(f"error: {e}")

        def do_routes(self, line):
            "routes R1: show the Linux forwarding table on a router."
            rid = line.strip().upper()
            if rid not in lab.topology.routers:
                print("usage: routes R1")
                return
            print(lab.net[node_name(rid)].cmd("ip route"), end="")

        def do_status(self, line):
            "status R1: show protocol status emitted by the routing daemon."
            rid = line.strip().upper()
            print(lab.status(rid))

        def do_converged(self, line):
            "Show whether all protocol routes currently match shortest paths."
            print(lab.routes_match_oracle())

    return RoutingCLI
