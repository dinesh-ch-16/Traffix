import csv
import os
import traci


# ============================================================
# TRAFFIX SCENARIOS
# ============================================================

# Keep ONLY normal for the first test.
# After normal works, we will enable all scenarios.

SCENARIOS = [
    "normal",
    "high",
    "j1_surge",
    "j2_surge",
    "j3_surge",
    "j4_surge",
]


# ============================================================
# SETTINGS
# ============================================================

SIMULATION_TIME = 900
RECORD_INTERVAL = 5

OUTPUT_DIR = "data/processed/traffic_states/scenarios"

JUNCTIONS = [
    "J1",
    "J2",
    "J3",
    "J4",
]


# ============================================================
# CONGESTION CLASSIFICATION
# ============================================================

def get_congestion(
    vehicle_count,
    queue_length,
    average_speed
):

    if (
        queue_length >= 10
        or average_speed < 3
        or vehicle_count >= 25
    ):
        return "CRITICAL"

    elif (
        queue_length >= 6
        or average_speed < 5
        or vehicle_count >= 15
    ):
        return "HIGH"

    elif (
        queue_length >= 2
        or average_speed < 9
        or vehicle_count >= 7
    ):
        return "MODERATE"

    else:
        return "LOW"


# ============================================================
# CALCULATE TRAFFIC STATE FOR ONE JUNCTION
# ============================================================

def calculate_junction_state(junction_id):

    # Get incoming edges of the junction.
    #
    # Example:
    # J2
    #   ↓
    # J1_J2
    # E1_J2
    # N2_J2
    # J4_J2

    incoming_edges = (
        traci.junction.getIncomingEdges(
            junction_id
        )
    )


    # Keep unique vehicle IDs.
    vehicles = set()


    queue_count = 0

    total_speed = 0.0
    speed_count = 0

    total_waiting = 0.0


    # ========================================================
    # CHECK EVERY INCOMING EDGE
    # ========================================================

    for edge_id in incoming_edges:

        # Number of lanes on this edge
        lane_count = (
            traci.edge.getLaneNumber(
                edge_id
            )
        )


        # ====================================================
        # CHECK EVERY LANE
        # ====================================================

        for lane_index in range(
            lane_count
        ):

            lane_id = (
                f"{edge_id}_{lane_index}"
            )


            # Vehicles currently on this lane
            vehicle_ids = (
                traci.lane.getLastStepVehicleIDs(
                    lane_id
                )
            )


            # =================================================
            # CHECK EVERY VEHICLE
            # =================================================

            for vehicle_id in vehicle_ids:

                vehicles.add(
                    vehicle_id
                )


                # Current speed
                speed = (
                    traci.vehicle.getSpeed(
                        vehicle_id
                    )
                )


                # Current waiting time
                waiting = (
                    traci.vehicle.getWaitingTime(
                        vehicle_id
                    )
                )


                total_speed += speed

                speed_count += 1

                total_waiting += waiting


                # Vehicle below 3 m/s
                # is considered queued.

                if speed < 3:

                    queue_count += 1


    # ========================================================
    # CALCULATE FINAL VALUES
    # ========================================================

    vehicle_count = len(
        vehicles
    )


    if speed_count > 0:

        average_speed = (
            total_speed /
            speed_count
        )

        average_waiting = (
            total_waiting /
            speed_count
        )

    else:

        average_speed = 0.0

        average_waiting = 0.0


    # ========================================================
    # CONGESTION LEVEL
    # ========================================================

    congestion_level = get_congestion(
        vehicle_count,
        queue_count,
        average_speed
    )


    return {

        "vehicle_count":
            vehicle_count,

        "queue_length":
            queue_count,

        "average_speed":
            round(
                average_speed,
                2
            ),

        "average_waiting":
            round(
                average_waiting,
                2
            ),

        "congestion_level":
            congestion_level
    }


# ============================================================
# RUN ONE SCENARIO
# ============================================================

def run_scenario(scenario):

    print()
    print("=" * 60)

    print(
        f"RUNNING SCENARIO: "
        f"{scenario.upper()}"
    )

    print("=" * 60)


    # ========================================================
    # SUMO CONFIGURATION FILE
    # ========================================================

    config_file = (
        f"simulation/sumo/"
        f"scenarios/{scenario}/"
        f"traffix.sumocfg"
    )


    # Check configuration exists
    if not os.path.exists(
        config_file
    ):

        raise FileNotFoundError(
            f"SUMO configuration not found:\n"
            f"{config_file}"
        )


    # ========================================================
    # OUTPUT FILE
    # ========================================================

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


    output_file = (
        f"{OUTPUT_DIR}/"
        f"traffic_states_{scenario}.csv"
    )


    # ========================================================
    # START SUMO
    # ========================================================

    sumo_command = [

        "sumo",

        "-c",
        config_file,

        "--no-step-log",
        "true",
    ]


    print(
        "Starting SUMO through TraCI..."
    )


    traci.start(
        sumo_command
    )


    print(
        "Connected to SUMO."
    )


    # ========================================================
    # DATA STORAGE
    # ========================================================

    rows = []


    try:

        # ====================================================
        # RUN SIMULATION
        # ====================================================

        for step in range(
            SIMULATION_TIME
        ):

            # Advance SUMO by one second
            traci.simulationStep()


            # =================================================
            # RECORD TRAFFIC STATE
            # =================================================

            if (
                step %
                RECORD_INTERVAL
                == 0
            ):

                timestamp = (
                    traci.simulation.getTime()
                )


                # ---------------------------------------------
                # PROCESS EACH JUNCTION
                # ---------------------------------------------

                for junction in JUNCTIONS:

                    state = (
                        calculate_junction_state(
                            junction
                        )
                    )


                    rows.append({

                        "scenario":
                            scenario,

                        "timestamp":
                            timestamp,

                        "junction":
                            junction,

                        "vehicle_count":
                            state[
                                "vehicle_count"
                            ],

                        "queue_length":
                            state[
                                "queue_length"
                            ],

                        "average_speed":
                            state[
                                "average_speed"
                            ],

                        "average_waiting":
                            state[
                                "average_waiting"
                            ],

                        "congestion_level":
                            state[
                                "congestion_level"
                            ],
                    })


                print(
                    f"{scenario}: "
                    f"{timestamp:.0f}s"
                )


    finally:

        # ====================================================
        # CLOSE SUMO
        # ====================================================

        try:

            traci.close()

        except Exception:

            pass


    # ========================================================
    # SAVE CSV
    # ========================================================

    columns = [

        "scenario",

        "timestamp",

        "junction",

        "vehicle_count",

        "queue_length",

        "average_speed",

        "average_waiting",

        "congestion_level",
    ]


    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


    # ========================================================
    # COMPLETE
    # ========================================================

    print()

    print(
        f"Saved: {output_file}"
    )

    print(
        f"Rows: {len(rows)}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)

    print(
        "TRAFFIX SCENARIO DATA GENERATOR"
    )

    print("=" * 60)


    for scenario in SCENARIOS:

        run_scenario(
            scenario
        )


    print()
    print("=" * 60)

    print(
        "TRAFFIX SCENARIO COMPLETE"
    )

    print("=" * 60)


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    main()