# CSC458 PA2 Part 0 - Mininet Tutorial

This tutorial is a CSC458 adaptation of the Lancaster University Mininet introduction supplied with PA2. **Complete all seven stages.** The original Lancaster tutorial, its `mn` command reference, and its starter topology are preserved in this directory as:

- `Lancaster_original_README.md`
- `MN.md`
- `Lancaster_topology_original.py`

The CSC458 version uses the **course Ubuntu VM**, not Lancaster's VS Code devcontainer. The networking concepts, topology tasks, Mininet CLI practice, link-emulation exercises, and SDN/controller stage are retained.

**Estimated time:** about 1-2 hours for the Lancaster sequence, plus the short CSC458 router bridge at the end.

## 0. Environment: Lancaster devcontainer vs. CSC458 VM

Lancaster's original lab explains devcontainers: containers package code, runtime, libraries, and dependencies into isolated environments and are lighter-weight than full virtual machines. Their VS Code workflow used Docker Desktop (or Podman on Lancaster lab machines) and `devcontainer open` / "Reopen in Container" to standardize the environment.

For **CSC458**, that standardization role is already fulfilled by the course VM. Do **not** install Docker for this assignment. Run Mininet directly in the VM with `sudo`. The conceptual distinction between a container and a VM is still useful: Mininet itself relies on Linux process/network-namespace mechanisms, while our VM provides the controlled Linux kernel and software stack shared by PA2-PA6.

Check the VM:

```bash
sudo python3 tools/check_environment.py
sudo mn --test pingall
```

If a Mininet run crashes, clean stale state before trying again:

```bash
sudo mn -c
```

## Stage 1 - Understanding the topology

The starter `topology.py` creates one Mininet host (`h1`), one switch (`s1`), and one virtual link. Mininet emulates networks primarily using Linux network namespaces, software switches/bridges, and virtual Ethernet interfaces.

Four fundamental components:

1. **Hosts** - act like computers. A host has its own network namespace, interfaces, IP/MAC addresses, processes, and can run ordinary Linux commands.
2. **Switches** - software forwarding elements. Open vSwitch (OvS) can behave as a bridge and is OpenFlow-capable.
3. **Links** - virtual connections between nodes; Mininet creates virtual interfaces as link endpoints.
4. **Controllers** - the control plane for OpenFlow-enabled switches. A controller can be created by Mininet or can run remotely at an IP address and TCP port.

Read `topology.py` and identify the calls that create each node/link and the `topos` dictionary that exposes the topology to `mn --topo`.

## Stage 2 - Running the topology and using `mn`

From this directory:

```bash
sudo mn --custom ./topology.py --topo tutorialTopology --switch ovs
```

`--switch ovs` selects Open vSwitch. Explore launcher options with:

```bash
mn -h
mn --version
```

The Lancaster lab's full `mn` reference is included as `MN.md`. It covers switch/host/controller/link selection, built-in topologies, cleanup (`-c`), custom files, regression tests, xterms, IP bases, deterministic MAC addresses, pre-populated ARP, NAT, verbosity, controller namespaces, and other launcher options.

At the `mininet>` prompt, run:

```text
help
nodes
net
links
h1 echo "Hello World!"
h1 ip addr
s1 ip link
exit
```

A Mininet CLI line prefixed by a node name executes that command in that node's context. This ability is central to later PA2 experiments, where you will run `ip route`, `ping`, `traceroute`, `tcpdump`, and routing daemons in different namespaces.

After exiting, run `sudo mn -c`.

## Stage 3 - Extending the topology

### Task 1 - More hosts

Modify `topology.py` so `s1` has five hosts, `h1` through `h5`.

Verify with:

```text
net
links
pingall
h1 ping -c 5 h4
```

You should see five host-switch links and, without intentional loss, `pingall` should report 0% dropped (20/20 host-to-host probes).

### Task 2 - More switches

Extend the topology to two switches. Attach `h1`-`h5` to `s1`, `h6`-`h10` to `s2`, and connect `s1` to `s2`.

Use `net` and `links` to verify the structure. Port numbering can vary, but there should be ten host-switch links plus one switch-switch link. With unconstrained links, `pingall` should report full reachability (90/90 host-to-host probes).

### Bonus - use Python as Python

Refactor repetitive topology code using normal Python data structures and loops. The topology definition is a Python program; do not treat it as a static configuration language.

After each run, clean up with `sudo mn -c`.

## Stage 4 - Basic testing

Mininet shortcuts such as `pingall`, `net`, and `links` are useful, but host commands expose richer measurements.

### Connectivity and latency with ping

Run:

```text
mininet> h1 ping -c 5 h8
```

Record packet loss and min/avg/max RTT. Lancaster's example had 0% loss, average RTT about 0.229 ms, and a first reply around 0.6 ms while later replies were around 0.1-0.2 ms. **Do not expect those exact numbers in the CSC458 VM.** The important observation is that a first packet can be slower because initial communication may require setup such as ARP resolution (which you implemented in PA1) and switch learning.

### Bandwidth with iperf3

`iperf3` needs a server and client. For example:

```text
mininet> h8 iperf3 -s &
mininet> h1 iperf3 -c h8 -p 5201
```

The unconstrained Lancaster example measured roughly 69 Gbit/s because the path was only software inside one machine. Your VM's value will differ. Treat this as an emulation baseline, not as a physical-link capacity.

## Stage 5 - Multiple topologies in one file

A single custom Python file can expose multiple `Topo` subclasses through the `topos` dictionary. Add another class and register it, for example:

```python
topos = {
    'tutorialTopology': (lambda: TutorialTopology()),
    'newTopology': (lambda: MyNewExampleTopology()),
}
```

Then select it with:

```bash
sudo mn --custom ./topology.py --topo newTopology --switch ovs
```

Demonstrate that both topology names can be launched.

## Stage 6 - Adding realism with TCLink

Real networks have finite bandwidth, delay, and loss. Mininet's `TCLink` applies Linux traffic-control constraints to virtual links.

Add:

```python
from mininet.link import TCLink
```

Examples from the Lancaster lab:

```python
self.addLink(h1, s1, cls=TCLink, bw=100)       # 100 Mbit/s
self.addLink(h2, s1, cls=TCLink, delay='75ms') # 75 ms delay
self.addLink(h3, s1, cls=TCLink, loss=5)        # 5% loss
```

Use `iperf3` for bandwidth and `ping` for delay/loss.

### Task 3 - constrain the inter-switch link

On the topology from Task 2, configure the `s1`-`s2` link with:

- bandwidth: **50 Mbit/s**
- latency: **30 ms**
- loss: **10%**

Then repeat `h1 ping -c ... h8` and the `iperf3` experiment. Explain how the observations differ from Stage 4. Do not grade yourself against one exact TCP throughput number: packet loss interacts strongly with TCP congestion control.

## Stage 7 - Welcome to SDN

With `--switch ovs`, Mininet uses Open vSwitch, an OpenFlow-capable software switch. OpenFlow separates a programmable controller (control plane) from switch forwarding behavior (data plane).

A remote controller is selected with `--controller remote` and may be given an IP/port. The Lancaster example used:

```bash
sudo mn --custom ./topology.py --topo tutorialTopology \
    --switch ovs --controller remote,ip=10.50.50.33,port=6633
```

For a local reference controller, open a **second VM terminal** and try:

```bash
controller ptcp:6633
```

Then launch:

```bash
sudo mn --custom ./topology.py --topo tutorialTopology \
    --switch ovs --controller remote,ip=127.0.0.1,port=6633
```

Test connectivity. Then stop the controller and repeat the experiment. Record what changes. The course environment checker reports whether the `controller` command is present. If the final course VM uses a different staff-announced reference-controller command, use that command; the Mininet `--controller remote,...` side is unchanged.

The backslash (`\\`) in a shell command simply continues the same command on the next line.

This stage is an introduction to SDN only. **PA2's DV/LS routers do not use an OpenFlow controller.** Later assignments use Mininet for different kinds of forwarding elements, so understanding this distinction is useful.

## Stage 8 - Bridge from the Mininet tutorial to PA2 routing

The Lancaster stages use Ethernet hosts and OvS switches. PA2's routing experiments instead create Linux router namespaces with IP forwarding enabled. Run:

```bash
sudo python3 tools/mininet_intro.py
```

At the Mininet prompt inspect:

```text
nodes
net
h1 ip addr
r1 ip addr
r1 ip route
r2 ip route
r3 ip route
```

The topology is `R1-R2-R3`, with one stub host behind each router. Initially the routers know only directly connected prefixes, so `h1 ping -c 1 10.3.0.2` fails.

Use the static-routing knowledge from PA1 to install the missing routes with Linux `ip route add`. For example:

```text
r1 ip route add 10.3.0.0/24 via 10.254.0.6 dev r1-r2
```

Determine the remaining routes, verify all-pairs connectivity, and run:

```text
h1 traceroute -n 10.3.0.2
```

Then fail the `r2-r3` link:

```text
link r2 r3 down
```

Observe that manually installed routes remain in the FIB even though their next-hop path is unusable. Restore the link with `link r2 r3 up`.

This is the transition to the rest of PA2: **DV and LS will dynamically compute the remote-prefix next hops and the supplied runtime will install them into these Linux forwarding tables.**

## Source and further reading

This Part 0 is adapted from Lancaster University's supplied Mininet tutorial. The original tutorial and `mn` reference are included locally so every stage and reference item remains available. The original tutorial also links to the Mininet source, official Mininet walkthrough, network-testing guides, and an OSKen/remote-controller tutorial.
