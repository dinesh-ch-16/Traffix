from perception.sumo_client import SumoClient
from perception.traffic_state import TrafficStateEngine
from prediction.congestion_detector import CongestionDetector
from prediction.traffic_dataset import TrafficDatasetRecorder


CONFIG_FILE = "simulation/sumo/configs/traffix.sumocfg"

OUTPUT_FILE = (
    "data/processed/traffic_states/traffic_states.csv"
)


def main():

    # ---------------------------------------------
    # Initialize modules
    # ---------------------------------------------

    sumo = SumoClient(CONFIG_FILE)

    traffic_engine = TrafficStateEngine()

    congestion_detector = CongestionDetector()

    recorder = TrafficDatasetRecorder(
        OUTPUT_FILE
    )


    # ---------------------------------------------
    # Start SUMO
    # ---------------------------------------------

    sumo.start()

    try:

        for step in range(300):

            sumo.step()


            # Record traffic state every 10 seconds
            if step % 10 == 0:

                current_time = sumo.get_time()

                network_state = (
                    traffic_engine.get_network_state()
                )


                for junction_id, state in network_state.items():

                    # Add congestion classification
                    analyzed_state = (
                        congestion_detector.analyze(state)
                    )


                    # Save to dataset
                    recorder.record(
                        timestamp=current_time,
                        junction=junction_id,
                        traffic_state=analyzed_state
                    )


                print(
                    f"Recorded traffic state at "
                    f"{current_time:.0f}s"
                )


    finally:

        sumo.close()


    print("\n========================================")
    print("TRAFFIX DATASET GENERATION COMPLETE")
    print("========================================")
    print(f"Dataset: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()