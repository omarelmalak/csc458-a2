# Packet captures

PA2 does not ship fixed PCAPs. Instead, generate control-plane captures from your own Mininet run:

```bash
sudo python3 tools/run_mininet.py line4.json --protocol DV --capture
```

The run directory will contain one `R*.pcap` file per router. Open them in Wireshark or use `tcpdump -nn -r <file>`. The UDP control port is 4582.
