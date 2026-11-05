from mininet.topo import Topo
from mininet.link import TCLink

class TutorialTopology( Topo ):

  def build( self ):
    # add a host to the network
    # h1 = self.addHost( 'h1' )
    hosts = []
    for i in range(1, 11):
      hostname = f'h{i}'
      host = self.addHost(hostname)
      hosts.append(host)

    # add a switch to the network
    # s1 = self.addSwitch( 's1' )
    switches = []
    for i in range(1, 3):
      switchname = f's{i}'
      switch = self.addSwitch(switchname)
      switches.append(switch)

    # add a link between the host `h1` and the `s1` switch
    # self.addLink( h1, s1 )
    for i in range(len(hosts)):
      host = hosts[i]
      host_number = i + 1
      if host_number >= 1 and host_number <= 5:
        self.addLink(host, switches[0])
      elif host_number >= 6 and host_number <= 10:
        self.addLink(host, switches[1])
      
    self.addLink(switches[0], switches[1], cls=TCLink, bw=50, delay='30ms', loss=10)

class MyNewExampleTopology( Topo ):
  def build(self):
    pass

# the topologies accessible to the mn tool's `--topo` flag
# note: if using the Dockerfile, this must be the same as in the Dockerfile
topos = {
    'tutorialTopology': (lambda: TutorialTopology()),
    'newTopology': (lambda: MyNewExampleTopology()),
  }