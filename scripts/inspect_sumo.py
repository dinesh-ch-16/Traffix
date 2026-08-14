import traci

from perception.sumo_client import SumoClient


CONFIG_FILE = "simulation/sumo/configs/traffix.sumocfg"


def main():

    sumo = SumoClient(CONFIG_FILE)
    sumo.start()

    try:

        sumo.step()

        print("\n" + "=" * 50)
        print("TRAFFIX - SUMO NETWORK INSPECTION")
        print("=" * 50)

        print("\nJUNCTIONS")
        print("-" * 30)

        for junction_id in traci.junction.getIDList():
            print(junction_id)

        print("\nTRAFFIC LIGHTS")
        print("-" * 30)

        for tls_id in traci.trafficlight.getIDList():
            print(tls_id)

        print("\nEDGES")
        print("-" * 30)

        for edge_id in traci.edge.getIDList():

            if not edge_id.startswith(":"):
                print(edge_id)

        print("\nACTIVE VEHICLES")
        print("-" * 30)

        vehicles = traci.vehicle.getIDList()

        print("Count:", len(vehicles))

        for vehicle_id in vehicles[:10]:
            print(vehicle_id)

        print("\n" + "=" * 50)

    finally:

        sumo.close()


if __name__ == "__main__":
    main()