from perception.sumo_client import SumoClient
from perception.traffic_state import TrafficStateEngine


CONFIG_FILE = "simulation/sumo/configs/traffix.sumocfg"


def main():

    sumo = SumoClient(CONFIG_FILE)

    traffic_engine = TrafficStateEngine()

    sumo.start()

    try:

        for step in range(300):

            sumo.step()

            if step % 10 == 0:

                print("\n" + "=" * 60)

                print(
                    f"TRAFFIX TRAFFIC STATE | "
                    f"TIME: {sumo.get_time():.0f}s"
                )

                print("=" * 60)


                network_state = traffic_engine.get_network_state()


                for junction_id, state in network_state.items():

                    print(f"\n{junction_id}")

                    print(
                        f"  Vehicles       : "
                        f"{state['vehicle_count']}"
                    )

                    print(
                        f"  Queue          : "
                        f"{state['queue_length']}"
                    )

                    print(
                        f"  Avg Speed      : "
                        f"{state['average_speed']} m/s"
                    )

                    print(
                        f"  Avg Waiting    : "
                        f"{state['average_waiting']} sec"
                    )

    finally:

        sumo.close()


if __name__ == "__main__":
    main()