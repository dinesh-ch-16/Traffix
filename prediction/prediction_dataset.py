import csv
import os


class PredictionDatasetBuilder:

    def __init__(self, input_file, output_file, horizon_seconds=300):

        self.input_file = input_file
        self.output_file = output_file
        self.horizon_seconds = horizon_seconds

        os.makedirs(
            os.path.dirname(output_file),
            exist_ok=True
        )


    def load_data(self):

        with open(
            self.input_file,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            data = list(reader)

        return data


    def build(self):

        data = self.load_data()

        # Convert numeric fields
        for row in data:

            row["timestamp"] = float(row["timestamp"])
            row["vehicle_count"] = int(row["vehicle_count"])
            row["queue_length"] = int(row["queue_length"])
            row["average_speed"] = float(row["average_speed"])
            row["average_waiting"] = float(row["average_waiting"])


        # Create lookup:
        # (timestamp, junction) -> traffic state

        state_lookup = {}

        for row in data:

            key = (
                row["timestamp"],
                row["junction"]
            )

            state_lookup[key] = row


        output_rows = []


        for current in data:

            current_time = current["timestamp"]
            junction = current["junction"]

            future_time = (
                current_time +
                self.horizon_seconds
            )


            future_key = (
                future_time,
                junction
            )


            # Future state must exist
            if future_key not in state_lookup:
                continue


            future = state_lookup[future_key]


            output_rows.append({

                "current_timestamp":
                    current_time,

                "junction":
                    junction,

                "current_vehicle_count":
                    current["vehicle_count"],

                "current_queue_length":
                    current["queue_length"],

                "current_average_speed":
                    current["average_speed"],

                "current_average_waiting":
                    current["average_waiting"],

                "current_congestion":
                    current["congestion_level"],


                "future_timestamp":
                    future_time,

                "future_vehicle_count":
                    future["vehicle_count"],

                "future_queue_length":
                    future["queue_length"],

                "future_average_speed":
                    future["average_speed"],

                "future_average_waiting":
                    future["average_waiting"],

                "future_congestion":
                    future["congestion_level"]
            })


        columns = [

            "current_timestamp",
            "junction",

            "current_vehicle_count",
            "current_queue_length",
            "current_average_speed",
            "current_average_waiting",
            "current_congestion",

            "future_timestamp",

            "future_vehicle_count",
            "future_queue_length",
            "future_average_speed",
            "future_average_waiting",
            "future_congestion"
        ]


        with open(
            self.output_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=columns
            )

            writer.writeheader()

            writer.writerows(output_rows)


        return len(output_rows)