class CongestionDetector:

    def __init__(self):

        # Thresholds are intentionally simple for the prototype.
        self.speed_thresholds = {
            "low": 10.0,
            "moderate": 7.0,
            "high": 4.0
        }

        self.queue_thresholds = {
            "low": 3,
            "moderate": 6,
            "high": 10
        }

        self.waiting_thresholds = {
            "low": 5.0,
            "moderate": 10.0,
            "high": 15.0
        }


    def classify(self, traffic_state):

        speed = traffic_state["average_speed"]
        queue = traffic_state["queue_length"]
        waiting = traffic_state["average_waiting"]


        # -------------------------------------------------
        # CRITICAL
        # -------------------------------------------------

        if (
            speed < self.speed_thresholds["high"]
            and
            (
                queue >= self.queue_thresholds["high"]
                or
                waiting >= self.waiting_thresholds["high"]
            )
        ):
            level = "CRITICAL"


        # -------------------------------------------------
        # HIGH
        # -------------------------------------------------

        elif (
            speed < self.speed_thresholds["moderate"]
            or
            queue >= self.queue_thresholds["moderate"]
            or
            waiting >= self.waiting_thresholds["moderate"]
        ):
            level = "HIGH"


        # -------------------------------------------------
        # MODERATE
        # -------------------------------------------------

        elif (
            speed < self.speed_thresholds["low"]
            or
            queue >= self.queue_thresholds["low"]
            or
            waiting >= self.waiting_thresholds["low"]
        ):
            level = "MODERATE"


        # -------------------------------------------------
        # LOW
        # -------------------------------------------------

        else:
            level = "LOW"


        return level


    def analyze(self, traffic_state):

        level = self.classify(traffic_state)

        result = traffic_state.copy()

        result["congestion_level"] = level

        return result