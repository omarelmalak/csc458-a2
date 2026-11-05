# CSC458 PA2 - Intra-Domain Routing in Mininet

PA2 starts where PA1 ended. PA1 owns CIDR/LPM and static forwarding. PA2 reuses your **completed PA1 `prefix_tools.py`** and focuses on the routing control plane: Distance Vector (DV) and Link State (LS) dynamically compute next hops, and the staff runtime installs the resulting remote-prefix routes into real Linux forwarding tables inside Mininet.

## What you edit

- `mininet_tutorial/topology.py` - Part 0 Mininet tutorial exercises
- `src/csc458_pa2/dv_core.py` - Part I
- `src/csc458_pa2/ls_core.py` - Part II
- `report/answers_template.md` - Part 0 and experiment writeup

You do **not** reimplement CIDR/LPM in PA2.

## 0. Carry your PA1 prefix code forward

Copy your completed PA1 module into PA2:

```bash
python3 tools/import_pa1.py /path/to/your/PA1/repository
python3 tools/pa1_prefix_smoke.py
```

This creates/overwrites `src/csc458_pa2/prefix_tools.py`. The Linux-FIB adapter in PA2 imports this module directly from the PA2 package, so it is part of the forwarding stack rather than dead carry-forward code.

## 1. Unit-test environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD/src"
pytest -q -m "not mininet"
```

or:

```bash
./grade_local.sh
```

The deterministic harness tests DV/LS logic without root. It is not the experiment environment.

## 2. Part 0 - Mininet tutorial

Read and complete:

```text
mininet_tutorial/README.md
```

It adapts the complete Lancaster University Mininet introduction to the CSC458 course VM and retains all seven stages: topology concepts, `mn`/CLI, topology extension, ping/iperf3, multiple topologies, TCLink realism, and remote-controller/SDN orientation. The original Lancaster README, `MN.md` command reference, and original topology starter are bundled alongside it.

Then run the CSC458 router bridge:

```bash
sudo python3 tools/mininet_intro.py
```

If Mininet leaves stale interfaces/namespaces:

```bash
sudo mn -c
```

## 3. Run DV/LS in Mininet

```bash
sudo python3 tools/run_mininet.py line4.json --protocol DV --dv-mode poison_reverse
sudo python3 tools/run_mininet.py line4.json --protocol LS
```

Interactive example:

```bash
sudo python3 tools/run_mininet.py failure_alt.json --protocol DV --interactive
```

Useful commands at the `csc458>` prompt:

```text
routes R1
status R1
converged
link r1 r2 down
link r1 r2 up
cost R1 R2 5
h1 ping -c 2 10.4.0.2
h1 traceroute -n 10.4.0.2
```

## 4. Capture routing-control traffic

```bash
sudo python3 tools/run_mininet.py count_to_infinity.json --protocol DV --dv-mode basic --capture
```

Per-router PCAPs are stored in the run directory. Routing-control messages use UDP port 4582.

## Repository layout

```text
src/csc458_pa2/
  prefix_tools.py       COPY from your completed PA1; no new LPM implementation
  dv_core.py            EDIT
  ls_core.py            EDIT
  core_api.py           provided
  daemon.py             provided UDP runtime
  linux_routes.py       provided FIB adapter; reuses PA1 canonical_prefix()
  mininet_lab.py        provided PA2 Mininet runtime
  routing_cli.py        provided CLI extensions
  core_harness.py       deterministic unit-test harness
  topology.py           PA2 topology/event parser
  addressing.py         addressing scheme
  oracle.py             experiment checker; student cores may NOT import it

mininet_tutorial/
  README.md             CSC458 adaptation of full Lancaster lab
  topology.py           EDIT during Part 0
  MN.md                  Lancaster mn reference
  Lancaster_original_README.md
  Lancaster_topology_original.py

topologies/             DV/LS scenarios
tests/                  public tests
tools/                  import, experiment, diagnostic tools
report/                 report template
```

See `CSC458_PA2_handout.pdf` for the full specification.
