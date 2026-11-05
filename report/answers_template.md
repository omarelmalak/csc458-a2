# CSC458 PA2 Report

Names / UTORids:

## Part 0 - Mininet introduction and the forwarding/control-plane bridge

1. **Mininet components.** In your own words, define a Mininet host, switch, link, and controller. What Linux mechanisms make it possible to emulate many hosts on one VM?

2. **CLI orientation.** Include the output of `net` and `links` for the original one-host/one-switch topology. Give one command that you ran inside `h1` from the Mininet CLI and explain how it differs from an `mn` launcher command.

3. **Task 1 - more hosts.** Show that your one-switch/five-host topology has the expected five links and 0% `pingall` loss before link constraints are introduced.

4. **Task 2 - more switches.** Show the final two-switch/ten-host structure and the inter-switch link. Briefly describe how you refactored the topology Python code to avoid repetition.

5. **Basic testing.** For an unconstrained `h1 -> h8` path, report `ping -c 5` packet loss and average RTT, and report one `iperf3` throughput measurement. Was the first ping slower than later pings? If so, connect this observation to mechanisms such as PA1 ARP resolution and switch learning.

6. **Multiple topologies.** State the second topology name you added to the `topos` dictionary and show the `mn` command that launches it.

7. **TCLink.** Configure the `s1-s2` link for 50 Mbit/s, 30 ms delay, and 10% loss. Report a `ping` observation and an `iperf3` observation and explain how they differ from the unconstrained baseline. Do not expect an exact TCP throughput under loss.

8. **Remote controller / SDN.** Describe what happened when you used the remote reference controller and what happened after the controller was stopped or unavailable. Distinguish the switch data plane from the controller control plane. If the final course VM does not expose the `controller` command, record that fact and explain the experiment you would perform; no mark is lost for that VM-specific absence.

9. **Bridge to PA2 routing.** In `tools/mininet_intro.py`, why does `h1` initially fail to reach `h3` even though the physical links are up? Paste the final `ip route` output from R1/R2/R3 after you install correct static routes. After `link r2 r3 down`, which entries remain and why does reachability fail? Relate this to why a dynamic routing protocol is needed.

10. **PA1 reuse.** Explain the separation among: (a) PA1 longest-prefix forwarding lookup, (b) a PA2 DV/LS route computation for a destination prefix, and (c) the Linux FIB entry installed by the staff runtime.

## Part III - DV/LS experiments

### A. Correctness and forwarding

Provide one DV and one LS example showing that the protocol state, Linux `ip route`, `ping`, and `traceroute` agree with the expected shortest path.

### B. Failure convergence

Fill in the table for `failure_alt.json`.

| Protocol | DV mode | Initial convergence (s) | Reconvergence (s) | Control messages during event | Control bytes during event |
|---|---|---:|---:|---:|---:|
| DV | basic | | | | |
| DV | poison reverse | | | | |
| LS | - | | | | |

Explain the path before and after the R2-R4 failure.

### C. Count to infinity

Run `count_to_infinity.json` with DV basic and poison reverse. From the generated control-plane capture/status, give at least three successive metrics that illustrate count-to-infinity in basic DV. Explain why poison reverse changes this behavior.

### D. Cost change

Run `cost_change.json` with DV and LS. State the R1 -> 10.4.0.0/24 route before and after the cost change, and compare how the two protocols disseminate the new information.

### E. DV versus LS

In 200-300 words, compare what each router knows, what is carried in control messages, control overhead, convergence behavior, and the failure modes you observed. Refer to your own measurements.
