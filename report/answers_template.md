# CSC458 PA2 Report

Names / UTORids:

## Part 0 - Mininet introduction and the forwarding/control-plane bridge

1. **Mininet components.** In your own words, define a Mininet host, switch, link, and controller. What Linux mechanisms make it possible to emulate many hosts on one VM?
Host: A host is a machine that sends/receives data in the form of IP packets. Every host has a network namespace, interfaces, and IP/MAC address. It can also run threads and processes as well as Linux commands.
Switch: A switch essentially acts as a "transparent" forwarder of packets. It doesn't have its own IP addresses and also doesn't manipulate the source and destination MAC addresses at intermediary hops (unlike routers).
Link: A link is a connection between any 2 nodes (in this case, a "node" can be a host or a switch).
Controller: A controller acts as a control plane that stores all the correct routing tables and information and passes it to the switches (using OpenFlow) for them to abide by (data plane). The controller can be created by Mininet itself or run with its own IP address and port like we did on our VM in 3.7 (e.g. `controller ptcp:6633`). 
We use Mininet to emulate several hosts on one VM using linux namespaces and Open vSwitch (OvS) switches to allow us to communicate with them. 

2. **CLI orientation.** Include the output of `net` and `links` for the original one-host/one-switch topology. Give one command that you ran inside `h1` from the Mininet CLI and explain how it differs from an `mn` launcher command.
```
mininet> net
h1 h1-eth0:s1-eth1
s1 lo:  s1-eth1:h1-eth0
c0
mininet> links
h1-eth0<->s1-eth1 (OK OK) 
```
One command I ran inside `h1` was `h1 ip addr`. This differs from an `mn` launcher command like `sudo mn --custom ./topology.py --topo tutorialTopology --switch ovs` in several ways. The simplest is that commands within the launched mininet can start with the host name (e.g. `h1`) or switch name (e.g. `s1`) for example, and can give us direct information about the node. These commands are executed within the launched mininet, whereas `mn` launcher commands are launched in the VM terminal.

3. **Task 1 - more hosts.** Show that your one-switch/five-host topology has the expected five links and 0% `pingall` loss before link constraints are introduced.
```
mininet> net
h1 h1-eth0:s1-eth1
h2 h2-eth0:s1-eth2
h3 h3-eth0:s1-eth3
h4 h4-eth0:s1-eth4
h5 h5-eth0:s1-eth5
s1 lo:  s1-eth1:h1-eth0 s1-eth2:h2-eth0 s1-eth3:h3-eth0 s1-eth4:h4-eth0 s1-eth5:h5-eth0
c0
mininet> links
h1-eth0<->s1-eth1 (OK OK) 
h2-eth0<->s1-eth2 (OK OK) 
h3-eth0<->s1-eth3 (OK OK) 
h4-eth0<->s1-eth4 (OK OK) 
h5-eth0<->s1-eth5 (OK OK) 
mininet> pingall
*** Ping: testing ping reachability
h1 -> h2 h3 h4 h5 
h2 -> h1 h3 h4 h5 
h3 -> h1 h2 h4 h5 
h4 -> h1 h2 h3 h5 
h5 -> h1 h2 h3 h4 
*** Results: 0% dropped (20/20 received)
```

4. **Task 2 - more switches.** Show the final two-switch/ten-host structure and the inter-switch link. Briefly describe how you refactored the topology Python code to avoid repetition.
```
mininet> net
h1 h1-eth0:s1-eth1
h2 h2-eth0:s1-eth2
h3 h3-eth0:s1-eth3
h4 h4-eth0:s1-eth4
h5 h5-eth0:s1-eth5
h6 h6-eth0:s2-eth1
h7 h7-eth0:s2-eth2
h8 h8-eth0:s2-eth3
h9 h9-eth0:s2-eth4
h10 h10-eth0:s2-eth5
s1 lo:  s1-eth1:h1-eth0 s1-eth2:h2-eth0 s1-eth3:h3-eth0 s1-eth4:h4-eth0 s1-eth5:h5-eth0 s1-eth6:s2-eth6
s2 lo:  s2-eth1:h6-eth0 s2-eth2:h7-eth0 s2-eth3:h8-eth0 s2-eth4:h9-eth0 s2-eth5:h10-eth0 s2-eth6:s1-eth6
c0
mininet> links
h1-eth0<->s1-eth1 (OK OK) 
h2-eth0<->s1-eth2 (OK OK) 
h3-eth0<->s1-eth3 (OK OK) 
h4-eth0<->s1-eth4 (OK OK) 
h5-eth0<->s1-eth5 (OK OK) 
h6-eth0<->s2-eth1 (OK OK) 
h7-eth0<->s2-eth2 (OK OK) 
h8-eth0<->s2-eth3 (OK OK) 
h9-eth0<->s2-eth4 (OK OK) 
h10-eth0<->s2-eth5 (OK OK) 
s1-eth6<->s2-eth6 (OK OK) 
mininet> pingall
*** Ping: testing ping reachability
h1 -> h2 h3 h4 h5 h6 h7 h8 h9 h10 
h2 -> h1 h3 h4 h5 h6 h7 h8 h9 h10 
h3 -> h1 h2 h4 h5 h6 h7 h8 h9 h10 
h4 -> h1 h2 h3 h5 h6 h7 h8 h9 h10 
h5 -> h1 h2 h3 h4 h6 h7 h8 h9 h10 
h6 -> h1 h2 h3 h4 h5 h7 h8 h9 h10 
h7 -> h1 h2 h3 h4 h5 h6 h8 h9 h10 
h8 -> h1 h2 h3 h4 h5 h6 h7 h9 h10 
h9 -> h1 h2 h3 h4 h5 h6 h7 h8 h10 
h10 -> h1 h2 h3 h4 h5 h6 h7 h8 h9 
*** Results: 0% dropped (90/90 received)
```
We refactored the code to loop over the host numbers (i.e. `range(1, 11)` to give us 1, 2, ..., 10), build the `hostname` using an f-string with the host number, register it, and store in a list of hosts. The same was done for the 2 switches. Then, we loop over the hosts in the list, check if its `host_number` (i.e. index in host list + 1) is between 1-5 (inclusive), and if so, create a link from that host to `s1`. We do the same check for `host_number` between 6-10 (inclusive), and if so, create a link from that host to `s2`. Then, we simply create a link between `s1` and `s2` at the end.

5. **Basic testing.** For an unconstrained `h1 -> h8` path, report `ping -c 5` packet loss and average RTT, and report one `iperf3` throughput measurement. Was the first ping slower than later pings? If so, connect this observation to mechanisms such as PA1 ARP resolution and switch learning.
```
mininet> h1 ping -c 10 h8
PING 10.0.0.8 (10.0.0.8) 56(84) bytes of data.
64 bytes from 10.0.0.8: icmp_seq=1 ttl=64 time=2.80 ms
64 bytes from 10.0.0.8: icmp_seq=2 ttl=64 time=2.00 ms
64 bytes from 10.0.0.8: icmp_seq=3 ttl=64 time=2.54 ms
64 bytes from 10.0.0.8: icmp_seq=4 ttl=64 time=0.421 ms
64 bytes from 10.0.0.8: icmp_seq=5 ttl=64 time=0.048 ms
64 bytes from 10.0.0.8: icmp_seq=6 ttl=64 time=0.311 ms
64 bytes from 10.0.0.8: icmp_seq=7 ttl=64 time=0.162 ms
64 bytes from 10.0.0.8: icmp_seq=8 ttl=64 time=0.462 ms
64 bytes from 10.0.0.8: icmp_seq=9 ttl=64 time=0.107 ms
64 bytes from 10.0.0.8: icmp_seq=10 ttl=64 time=0.145 ms

--- 10.0.0.8 ping statistics ---
10 packets transmitted, 10 received, 0% packet loss, time 9154ms
rtt min/avg/max/mdev = 0.048/0.898/2.795/1.034 ms
mininet> h8 iperf3 -s &
-----------------------------------------------------------
Server listening on 5201
-----------------------------------------------------------
mininet> h1 iperf3 -c h8 -p 5201
Connecting to host 10.0.0.8, port 5201
[  5] local 10.0.0.1 port 45540 connected to 10.0.0.8 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  9.83 GBytes  84.4 Gbits/sec    0   1.86 MBytes       
[  5]   1.00-2.00   sec  10.9 GBytes  93.6 Gbits/sec    0   2.05 MBytes       
[  5]   2.00-3.00   sec  10.7 GBytes  92.0 Gbits/sec    1   2.38 MBytes       
[  5]   3.00-4.00   sec  11.2 GBytes  96.5 Gbits/sec    0   2.38 MBytes       
[  5]   4.00-5.00   sec  10.9 GBytes  94.0 Gbits/sec    0   2.38 MBytes       
[  5]   5.00-6.00   sec  10.8 GBytes  92.7 Gbits/sec    1   2.38 MBytes       
[  5]   6.00-7.00   sec  10.6 GBytes  91.3 Gbits/sec    0   2.38 MBytes       
[  5]   7.00-8.00   sec  10.6 GBytes  90.8 Gbits/sec    0   2.38 MBytes       
[  5]   8.00-9.00   sec  10.8 GBytes  93.1 Gbits/sec    0   2.38 MBytes       
[  5]   9.00-10.00  sec  11.1 GBytes  95.2 Gbits/sec    0   2.38 MBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec   108 GBytes  92.4 Gbits/sec    2             sender
[  5]   0.00-10.04  sec   108 GBytes  92.0 Gbits/sec                  receiver

iperf Done.
```
`ping -c 5` packet loss: 0%
`ping -c 5` average RTT: 0.898 ms
`iperf3` throughput measurement: 92.4 Gbits/sec is the final throughput from the sender.

The first ping took 2.80 ms, whereas later pings dropped as low as 0.145 by the end. This is because on the first ping, all nodes have no knowledge of mappings from IPs to MAC addresses for any of the hosts (i.e. their ARP caches are completely empty). Therefore, `h1` needs to broadcast an ARP request to find the MAC address of `h8` and set it as the destination in the Ethernet frame header it creates in L2. This takes time because `s1` doesn't know where to send the frame, so it learns the source (i.e. `s1` knows that it can reach `h1` through the port it received the ARP request from) and broadcasts the frame. `s2` does the same (i.e. `s2` now also knows it can reach `h1` through the port it received the ARP request from and the request is broadcasted again). Then, `h8` sends the ARP reply and `s2` learns how to reach `h8`. `s2` knows how it can reach `h1`, so it sends a unicast to `s1`. `s1` also learned how to reach `h1`, so it also sends a unicast (and learns how to reach `h8`). All of this has to happen before the ping can even be sent, which takes some time. Once this happens, the ARP cache entries required to send pings from `h1` to `h8` are built at each respective node mentioned in this process with a TTL. Because of this, the process no longer has to repeat itself for each ping since we can simply send direct unicasts for future pings along `h1` -> `s1` -> `s2` -> `h8` without the need for learning (until the TTL expires), which explains why the pings are delivered faster after the initial.

6. **Multiple topologies.** State the second topology name you added to the `topos` dictionary and show the `mn` command that launches it.
The new topology name is `newTopology` (maps to the `MyNewExampleTopology` class). The `mn` command that launches it is `sudo mn --custom ./topology.py --topo newTopology --switch ovs`. 

7. **TCLink.** Configure the `s1-s2` link for 50 Mbit/s, 30 ms delay, and 10% loss. Report a `ping` observation and an `iperf3` observation and explain how they differ from the unconstrained baseline. Do not expect an exact TCP throughput under loss.
```
mininet> h1 ping -c 5 h8
PING 10.0.0.8 (10.0.0.8) 56(84) bytes of data.
64 bytes from 10.0.0.8: icmp_seq=1 ttl=64 time=129 ms
64 bytes from 10.0.0.8: icmp_seq=2 ttl=64 time=61.9 ms
64 bytes from 10.0.0.8: icmp_seq=3 ttl=64 time=66.3 ms
64 bytes from 10.0.0.8: icmp_seq=4 ttl=64 time=65.9 ms

--- 10.0.0.8 ping statistics ---
5 packets transmitted, 4 received, 20% packet loss, time 4010ms
rtt min/avg/max/mdev = 61.931/80.862/129.326/28.032 ms
mininet> h8 iperf3 -s &
mininet> h1 iperf3 -c h8 -p 5201
Connecting to host 10.0.0.8, port 5201
[  5] local 10.0.0.1 port 47088 connected to 10.0.0.8 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec   298 KBytes  2.44 Mbits/sec   13   5.66 KBytes       
[  5]   1.00-2.00   sec  0.00 Bytes  0.00 bits/sec    5   8.48 KBytes       
[  5]   2.00-3.00   sec  63.6 KBytes   522 Kbits/sec    7   5.66 KBytes       
[  5]   3.00-4.00   sec   127 KBytes  1.04 Mbits/sec    1   11.3 KBytes       
[  5]   4.00-5.00   sec   129 KBytes  1.05 Mbits/sec    5   7.07 KBytes       
[  5]   5.00-6.00   sec   127 KBytes  1.05 Mbits/sec    6   4.24 KBytes       
[  5]   6.00-7.00   sec  0.00 Bytes  0.00 bits/sec    3   2.83 KBytes       
[  5]   7.00-8.00   sec  63.6 KBytes   521 Kbits/sec    8   1.41 KBytes       
[  5]   8.00-9.00   sec  63.6 KBytes   520 Kbits/sec    1   8.48 KBytes       
[  5]   9.00-10.01  sec  63.6 KBytes   521 Kbits/sec    5   7.07 KBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.01  sec   936 KBytes   766 Kbits/sec   54             sender
[  5]   0.00-20.92  sec   936 KBytes   367 Kbits/sec                  receiver
```
`ping -c 5` packet loss: 20% (1/5 packets lost)
`ping -c 5` average RTT: 80.862 ms
`iperf3` throughput measurement: 766 Kbits/sec is the final throughput from the sender.
The `ping -c 5` packet loss increased from 0% (0/5 packets lost) on the unconstrained baseline to 20% (1/5 packets lost). This is because of the 10% loss we added on the link between `s1` and `s2`. The `ping -c 5` average RTT increased from 0.898 ms to 80.862 ms. This is because of the 30 ms delay we added on the link between `s1` and `s2` (i.e. the RTT increases by about `2 x 30 ms = 60 ms` for each ping). The `iperf3` throughput measurement decreased from 92.4 Gbits/sec to 766 Kbits/sec also because of the 50 Mbit/s bandwidth constraint between `s1` and `s2` and also potentially the 10% packet loss as well because if `h1` is using a congestion control algorithm like AIMD, it could cut its flow rate by a large amount for each packet lost, which could do a ton of damage to the final throughput.

8. **Remote controller / SDN.** Describe what happened when you used the remote reference controller and what happened after the controller was stopped or unavailable. Distinguish the switch data plane from the controller control plane. If the final course VM does not expose the `controller` command, record that fact and explain the experiment you would perform; no mark is lost for that VM-specific absence.
When we used the remote reference controller, everything was working the same way as it was when the controller was initiated by Mininet by default. However, when we stopped the remote reference controller, there was zero reachability (e.g. a `pingall` yielded 100% packet loss). This is because there was no controller control plane available to program the switches with the information they need to be able to forward packets through the links, so the data plane (acted on by the switches) has no knowledge of any frame forwarding rules to work with. 

9. **Bridge to PA2 routing.** In `tools/mininet_intro.py`, why does `h1` initially fail to reach `h3` even though the physical links are up? Paste the final `ip route` output from R1/R2/R3 after you install correct static routes. After `link r2 r3 down`, which entries remain and why does reachability fail? Relate this to why a dynamic routing protocol is needed.
`h1` initially fails to reach `h3` because the routing tables of `r1`, `r2`, and `r3` are incomplete. Specifically, `h1` with IP address 10.1.0.2/24 is trying to reach `h3` with IP address 10.3.0.2/24. It sets the destination to 10.3.0.2/24 in the IP packet header and sends it out to its immediate router `r1`. However, `r1` has no information in its routing table of which next hop to send the packet with destination 10.3.0.2/24, so it drops the packet immediately. Therefore, we have to act as the "control plane" and manually add the next-hops such that each host can reach each of the other hosts through `r1`, `r2`, and `r3`. The result of this as follows:
```
mininet> r1 ip route
10.1.0.0/24 dev r1-stub proto kernel scope link src 10.1.0.1 
10.2.0.0/24 via 10.254.0.6 dev r1-r2 
10.3.0.0/24 via 10.254.0.6 dev r1-r2 
10.254.0.4/30 dev r1-r2 proto kernel scope link src 10.254.0.5 
mininet> r2 ip route
10.1.0.0/24 via 10.254.0.5 dev r2-r1 
10.2.0.0/24 dev r2-stub proto kernel scope link src 10.2.0.1 
10.3.0.0/24 via 10.254.1.154 dev r2-r3 
10.254.0.4/30 dev r2-r1 proto kernel scope link src 10.254.0.6 
10.254.1.152/30 dev r2-r3 proto kernel scope link src 10.254.1.153 
mininet> r3 ip route
10.1.0.0/24 via 10.254.1.153 dev r3-r2 
10.2.0.0/24 via 10.254.1.153 dev r3-r2 
10.3.0.0/24 dev r3-stub proto kernel scope link src 10.3.0.1 
10.254.1.152/30 dev r3-r2 proto kernel scope link src 10.254.1.154
```
When executing `link r2 r3 down`, there's a problem because the entry `10.3.0.0/24 via 10.254.0.6 dev r1-r2` still exists in the routing table of `r1`. In other words, `r1` still believes it can reach the subnet 10.3.0.0/24 via `r2`, but that's no longer true because the link from `r2` to `r3` is down and there is no other way for `r2` to reach that subnet. Therefore, reachability from `h1` to `h3` will fail because after `r1` decides to still send the packet destined for 10.3.0.0/24 to `r2`, but `r2` can't route the packet to `r3` so it gets dropped. Therefore, a dynamic routing protocol is needed to be able to inform `r1` that `r2` can no longer route a packet to any IP in subnet 10.3.0.0/24. 

10. **PA1 reuse.** Explain the separation among: (a) PA1 longest-prefix forwarding lookup, (b) a PA2 DV/LS route computation for a destination prefix, and (c) the Linux FIB entry installed by the staff runtime.
Longest-prefix lookup we did in PA1 occurs in the data plane when the router decides where to route a packet by finding the longest prefix match in its routing table for an IP packet's destination and sending the packet to the mapped next-hop. This routing table has to be built in the first place (which was assumed in PA1), which is where PA2's DV/LS route computation comes in. This route computation is responsible for building the routing table for each of the routers at the control plane level. Once the route computations are complete, the staff runtime allows the control plane to connect to the data plane operated by the routers during packet routing by adding the routes as Linux FIB entries.

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
