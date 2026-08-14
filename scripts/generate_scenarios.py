import os
import xml.etree.ElementTree as ET
from copy import deepcopy


SOURCE_FILE = (
    "simulation/sumo/routes/traffix.rou.xml"
)

OUTPUT_ROOT = (
    "simulation/sumo/scenarios"
)


SCENARIOS = {

    "normal": {
        "multiplier": 1.0,
        "target": None
    },

    "high": {
        "multiplier": 1.5,
        "target": None
    },

    "j1_surge": {
        "multiplier": 1.0,
        "target": [
            "north_south_1",
            "south_north_1",
            "west_east_1",
            "east_west_1"
        ]
    },

    "j2_surge": {
        "multiplier": 1.0,
        "target": [
            "north_south_2",
            "south_north_2",
            "west_east_1",
            "east_west_1"
        ]
    },

    "j3_surge": {
        "multiplier": 1.0,
        "target": [
            "north_south_1",
            "south_north_1",
            "west_east_2",
            "east_west_2"
        ]
    },

    "j4_surge": {
        "multiplier": 1.0,
        "target": [
            "north_south_2",
            "south_north_2",
            "west_east_2",
            "east_west_2"
        ]
    }
}


def create_scenario(
    scenario_name,
    settings,
    root
):

    multiplier = settings["multiplier"]
    targets = settings["target"]


    for element in root.iter("flow"):

        flow_id = element.get("id")

        current_rate = float(
            element.get("vehsPerHour", "0")
        )


        # -----------------------------------------
        # Overall demand multiplier
        # -----------------------------------------

        if multiplier != 1.0:

            new_rate = (
                current_rate * multiplier
            )

            element.set(
                "vehsPerHour",
                str(int(new_rate))
            )


        # -----------------------------------------
        # Junction-specific surge
        # -----------------------------------------

        if targets is not None:

            if flow_id in targets:

                new_rate = (
                    current_rate * 2.0
                )

                element.set(
                    "vehsPerHour",
                    str(int(new_rate))
                )


    scenario_dir = os.path.join(
        OUTPUT_ROOT,
        scenario_name
    )

    os.makedirs(
        scenario_dir,
        exist_ok=True
    )


    output_file = os.path.join(
        scenario_dir,
        "traffix.rou.xml"
    )


    tree = ET.ElementTree(root)

    ET.indent(
        tree,
        space="    "
    )


    tree.write(
        output_file,
        encoding="UTF-8",
        xml_declaration=True
    )


    print(
        f"Created scenario: {scenario_name}"
    )

    print(
        f"  Output: {output_file}"
    )


def main():

    os.makedirs(
        OUTPUT_ROOT,
        exist_ok=True
    )


    for scenario_name, settings in SCENARIOS.items():

        # Read ORIGINAL route file every time.
        # This prevents one scenario from affecting another.

        tree = ET.parse(SOURCE_FILE)

        root = tree.getroot()

        create_scenario(
            scenario_name,
            deepcopy(settings),
            root
        )


    print()
    print("=" * 60)
    print("TRAFFIX SCENARIO GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()