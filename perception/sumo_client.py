import os
import sys
import traci


SUMO_HOME = os.environ.get("SUMO_HOME")

if not SUMO_HOME:
    raise EnvironmentError(
        "SUMO_HOME is not set. Please set the SUMO_HOME environment variable."
    )


SUMO_BINARY = os.path.join(SUMO_HOME, "bin", "sumo.exe")


class SumoClient:

    def __init__(self, config_file):
        self.config_file = config_file

    def start(self):
        traci.start([
            SUMO_BINARY,
            "-c",
            self.config_file,
            "--start",
            "--quit-on-end"
        ])

        print("Connected to SUMO")

    def step(self):
        traci.simulationStep()

    def get_time(self):
        return traci.simulation.getTime()

    def get_vehicle_ids(self):
        return traci.vehicle.getIDList()

    def get_vehicle_count(self):
        return traci.vehicle.getIDCount()

    def close(self):
        traci.close()
        print("SUMO connection closed")