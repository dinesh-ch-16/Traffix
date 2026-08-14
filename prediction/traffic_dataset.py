import csv
import os


class TrafficDatasetRecorder:

    def __init__(self, output_file):
        self.output_file = output_file

        # Create directory if it does not exist
        os.makedirs(
            os.path.dirname(output_file),
            exist_ok=True
        )

        self.columns = [
            "timestamp",
            "junction",
            "vehicle_count",
            "queue_length",
            "average_speed",
            "average_waiting",
            "congestion_level"
        ]

        # Create CSV with header if it does not exist
        if not os.path.exists(self.output_file):

            with open(
                self.output_file,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=self.columns
                )

                writer.writeheader()


    def record(self, timestamp, junction, traffic_state):

        row = {
            "timestamp": timestamp,
            "junction": junction,
            "vehicle_count": traffic_state["vehicle_count"],
            "queue_length": traffic_state["queue_length"],
            "average_speed": traffic_state["average_speed"],
            "average_waiting": traffic_state["average_waiting"],
            "congestion_level": traffic_state["congestion_level"]
        }

        with open(
            self.output_file,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=self.columns
            )

            writer.writerow(row)