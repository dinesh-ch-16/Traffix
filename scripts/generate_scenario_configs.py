import os
import xml.etree.ElementTree as ET


SCENARIOS = [
    "normal",
    "high",
    "j1_surge",
    "j2_surge",
    "j3_surge",
    "j4_surge",
]


NETWORK_FILE = "../../network/traffix.net.xml"


OUTPUT_ROOT = "simulation/sumo/scenarios"


def create_config(scenario):

    scenario_dir = os.path.join(
        OUTPUT_ROOT,
        scenario
    )

    os.makedirs(
        scenario_dir,
        exist_ok=True
    )

    route_file = "traffix.rou.xml"

    config_file = os.path.join(
        scenario_dir,
        "traffix.sumocfg"
    )

    root = ET.Element("configuration")

    # -----------------------------------------
    # INPUT
    # -----------------------------------------

    input_element = ET.SubElement(
        root,
        "input"
    )

    ET.SubElement(
        input_element,
        "net-file",
        value=NETWORK_FILE
    )

    ET.SubElement(
        input_element,
        "route-files",
        value=route_file
    )

    # -----------------------------------------
    # TIME
    # -----------------------------------------

    time_element = ET.SubElement(
        root,
        "time"
    )

    ET.SubElement(
        time_element,
        "begin",
        value="0"
    )

    ET.SubElement(
        time_element,
        "end",
        value="900"
    )

    # -----------------------------------------
    # PROCESSING
    # -----------------------------------------

    processing = ET.SubElement(
        root,
        "processing"
    )

    ET.SubElement(
        processing,
        "time-to-teleport",
        value="-1"
    )

    # -----------------------------------------
    # OUTPUT
    # -----------------------------------------

    output = ET.SubElement(
        root,
        "output"
    )

    ET.SubElement(
        output,
        "tripinfo-output",
        value="tripinfo.xml"
    )

    ET.indent(
        root,
        space="    "
    )

    tree = ET.ElementTree(root)

    tree.write(
        config_file,
        encoding="UTF-8",
        xml_declaration=True
    )

    print(
        f"Created config: {config_file}"
    )


def main():

    for scenario in SCENARIOS:

        create_config(
            scenario
        )

    print()
    print("=" * 60)
    print("TRAFFIX SCENARIO CONFIGURATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()