import traci


class TrafficStateEngine:

    def __init__(self):

        self.junctions = ["J1", "J2", "J3", "J4"]

        self.junction_edges = {

            "J1": [
                "N1_J1",
                "W1_J1",
                "J1_N1",
                "J1_W1",
                "J1_J2",
                "J1_J3"
            ],

            "J2": [
                "N2_J2",
                "J2_N2",
                "E1_J2",
                "J2_E1",
                "J1_J2",
                "J2_J1",
                "J2_J4",
                "J4_J2"
            ],

            "J3": [
                "S1_J3",
                "J3_S1",
                "W2_J3",
                "J3_W2",
                "J1_J3",
                "J3_J1",
                "J3_J4",
                "J4_J3"
            ],

            "J4": [
                "S2_J4",
                "J4_S2",
                "E2_J4",
                "J4_E2",
                "J2_J4",
                "J4_J2",
                "J3_J4",
                "J4_J3"
            ]
        }


    def get_junction_state(self, junction_id):

        edges = self.junction_edges[junction_id]

        vehicle_ids = set()

        total_speed = 0.0
        total_waiting = 0.0

        for edge_id in edges:

            vehicles = traci.edge.getLastStepVehicleIDs(edge_id)

            for vehicle_id in vehicles:

                vehicle_ids.add(vehicle_id)

                total_speed += traci.vehicle.getSpeed(vehicle_id)

                total_waiting += traci.vehicle.getWaitingTime(vehicle_id)


        vehicle_count = len(vehicle_ids)

        if vehicle_count > 0:

            average_speed = total_speed / vehicle_count

            average_waiting = total_waiting / vehicle_count

        else:

            average_speed = 0.0
            average_waiting = 0.0


        queue_length = 0

        for edge_id in edges:

            queue_length += traci.edge.getLastStepHaltingNumber(edge_id)


        return {

            "junction": junction_id,

            "vehicle_count": vehicle_count,

            "average_speed": round(average_speed, 2),

            "average_waiting": round(average_waiting, 2),

            "queue_length": queue_length

        }


    def get_network_state(self):

        network_state = {}

        for junction in self.junctions:

            network_state[junction] = self.get_junction_state(junction)

        return network_state