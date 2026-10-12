from common.receipt import Receipt, burn
from launch_towers.template import LaunchTower

class WaxtabletEngineTower(LaunchTower):
    def __init__(self):
        super().__init__("waxtablet_engine")
