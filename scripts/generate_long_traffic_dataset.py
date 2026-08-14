from perception.sumo_client import SumoClient
from perception.traffic_state import TrafficStateEngine
from prediction.congestion_detector import CongestionDetector
from prediction.traffic_dataset import TrafficDatasetRecorder


CONFIG_FILE = "simulation/sumo/configs/traffix.sumocfg"

OUTPUT_FILE = (
    "data/processed/traffic_states/traffic_states_15min.csv"
)

SIMULATION_STEPS = 900
RECORD_INTERVAL = 5


def main():

    sumo = SumoClient(CONFIG_FILE)

    traffic_engine = TrafficStateEngine()
    congestion_detector = CongestionDetector()

    recorder = TrafficDatasetRecorder(
        OUTPUT_FILE
    )

    sumo.start()

    try:

        for step in range(SIMULATION_STEPS):

            sumo.step()

            current_time = sumo.get_time()

            if step % RECORD_INTERVAL == 0:

                network_state = (
                    traffic_engine.get_network_state()
                )

                for junction_id, state in network_state.items():

                    analyzed_state = (
                        congestion_detector.analyze(state)
                    )

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
    print("TRAFFIX 15-MIN DATASET GENERATION")
    print("========================================")
    print(f"Dataset : {OUTPUT_FILE}")
    print(
        f"Duration: {SIMULATION_STEPS}s"
    )
    print(
        f"Interval: {RECORD_INTERVAL}s"
    )


if __name__ == "__main__":
    main()