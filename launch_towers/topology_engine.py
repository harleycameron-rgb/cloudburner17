from common.receipt import Receipt, burn
from launch_towers.template import LaunchTower

class TopologyEngineTower(LaunchTower):
    def __init__(self):
        super().__init__("topology_engine")
