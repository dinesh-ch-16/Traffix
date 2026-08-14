from perception.sumo_client import SumoClient
from perception.traffic_state import TrafficStateEngine
from prediction.congestion_detector import CongestionDetector


CONFIG_FILE = "simulation/sumo/configs/traffix.sumocfg"


def main():

    sumo = SumoClient(CONFIG_FILE)

    traffic_engine = TrafficStateEngine()
    congestion_detector = CongestionDetector()

    sumo.start()

    try:

        for step in range(300):

            sumo.step()

            # Analyze every 10 seconds
            if step % 10 == 0:

                print("\n" + "=" * 70)

                print(
                    f"TRAFFIX CONGESTION MONITOR | "
                    f"TIME: {sumo.get_time():.0f}s"
                )

                print("=" * 70)


                network_state = traffic_engine.get_network_state()


                for junction_id, state in network_state.items():

                    result = congestion_detector.analyze(state)


                    print(
                        f"\n{junction_id}"
                    )

                    print(
                        f"  Vehicles       : "
                        f"{result['vehicle_count']}"
                    )

                    print(
                        f"  Queue          : "
                        f"{result['queue_length']}"
                    )

                    print(
                        f"  Avg Speed      : "
                        f"{result['average_speed']} m/s"
                    )

                    print(
                        f"  Avg Waiting    : "
                        f"{result['average_waiting']} sec"
                    )

                    print(
                        f"  Congestion     : "
                        f"{result['congestion_level']}"
                    )


    finally:

        sumo.close()


if __name__ == "__main__":
    main()