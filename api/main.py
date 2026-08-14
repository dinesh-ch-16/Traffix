from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.live_simulation import (
    router as live_simulation_router,
    state_lock,
    simulation,
    junction_state,
)


# ============================================================
# TRAFFIX API
# ============================================================

app = FastAPI(
    title="Traffix Traffic Intelligence API",
    version="1.1.0",
)

app.include_router(live_simulation_router)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "traffic_states"
    / "scenarios"
    / "traffic_states_normal.csv"
)


# ============================================================
# COMMUTER OPTIMIZATION CONFIGURATION
# ============================================================

# Current project target:
# reduce commuter travel time by 10%.

COMMUTER_IMPROVEMENT_TARGET = 10.0

# Until the actual signal optimization experiment is connected,
# we use a 30-minute route benchmark for the commuter panel.
#
# IMPORTANT:
# This is a benchmark/target, NOT a claim that SUMO has already
# achieved a 10% improvement.

BASELINE_ROUTE_MINUTES = 30.0


# ============================================================
# DATA LOADER
# ============================================================

def load_data():

    if not DATA_FILE.exists():

        raise FileNotFoundError(
            f"Traffic dataset not found: {DATA_FILE}"
        )

    return pd.read_csv(DATA_FILE)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():

    return {
        "system": "TRAFFIX",
        "status": "online",
        "service": "Traffic Intelligence API",
    }


@app.get("/api/health")
def health():

    return {
        "status": "healthy",
        "system": "TRAFFIX",
    }


# ============================================================
# CURRENT TRAFFIC
# ============================================================

@app.get("/api/traffic/current")
def current_traffic():

    df = load_data()

    latest_timestamp = df["timestamp"].max()

    latest = df[
        df["timestamp"] == latest_timestamp
    ].copy()

    return {
        "timestamp": float(latest_timestamp),
        "junctions": latest.to_dict(
            orient="records"
        ),
    }


# ============================================================
# JUNCTION DATA
# ============================================================

@app.get("/api/traffic/junctions")
def junctions():

    df = load_data()

    latest_timestamp = df["timestamp"].max()

    latest = df[
        df["timestamp"] == latest_timestamp
    ].copy()

    junction_data = {}

    for _, row in latest.iterrows():

        junction_data[row["junction"]] = {

            "vehicles": int(
                row["vehicle_count"]
            ),

            "queue": int(
                row["queue_length"]
            ),

            "speed": float(
                row["average_speed"]
            ),

            "waiting": float(
                row["average_waiting"]
            ),

            "level": row[
                "congestion_level"
            ],
        }

    return {
        "timestamp": float(
            latest_timestamp
        ),

        "junctions": junction_data,
    }


# ============================================================
# TRAFFIC HISTORY
# ============================================================

@app.get("/api/traffic/history")
def traffic_history():

    df = load_data()

    history = (
        df.groupby("timestamp")
        .agg(
            vehicles=(
                "vehicle_count",
                "sum",
            ),

            queue=(
                "queue_length",
                "sum",
            ),

            average_speed=(
                "average_speed",
                "mean",
            ),
        )
        .reset_index()
    )

    return {
        "history": history.to_dict(
            orient="records"
        )
    }


# ============================================================
# SYSTEM STATUS
# ============================================================

@app.get("/api/system/status")
def system_status():

    return {
        "system": "TRAFFIX",
        "overall": "ONLINE",
        "computer_vision": "ONLINE",
        "prediction_engine": "ONLINE",
        "signal_network": "ONLINE",
        "connected_junctions": 4,
    }


# ============================================================
# ALERTS
# ============================================================

@app.get("/api/alerts")
def alerts():

    df = load_data()

    latest_timestamp = df["timestamp"].max()

    latest = df[
        df["timestamp"] == latest_timestamp
    ]

    alerts_list = []

    for _, row in latest.iterrows():

        level = row[
            "congestion_level"
        ]

        if level in [
            "HIGH",
            "CRITICAL",
        ]:

            alerts_list.append(
                {
                    "junction": row[
                        "junction"
                    ],

                    "level": level,

                    "queue": int(
                        row["queue_length"]
                    ),

                    "vehicles": int(
                        row["vehicle_count"]
                    ),

                    "message": (
                        "Congestion detected at "
                        f"{row['junction']}"
                    ),
                }
            )

    return {
        "timestamp": float(
            latest_timestamp
        ),

        "alerts": alerts_list,
    }


# ============================================================
# COMMUTER IMPACT
# ============================================================
#
# This endpoint exposes the project's 10% commuter-time
# improvement target.
#
# At this stage:
#
# baseline = benchmark route time
# optimized = baseline * 0.90
#
# The endpoint also reports live SUMO conditions.
#
# Later, when the actual signal optimization controller is
# implemented, this endpoint can be changed to compare:
#
#   baseline SUMO run
#             VS
#   optimized SUMO run
#
# and calculate the REAL measured improvement.
# ============================================================

@app.get("/api/commuter/impact")
def commuter_impact():

    # --------------------------------------------------------
    # Read current live simulation state
    # --------------------------------------------------------

    with state_lock:

        running = bool(
            simulation["running"]
        )

        simulation_time = float(
            simulation["time"]
        )

        total_vehicles = int(
            simulation["vehicles"]
        )

        current_junctions = dict(
            junction_state
        )

    # --------------------------------------------------------
    # Calculate network conditions
    # --------------------------------------------------------

    speeds = []

    queues = []

    congestion_levels = []

    for data in current_junctions.values():

        try:

            speeds.append(
                float(
                    data.get(
                        "average_speed",
                        0,
                    )
                )
            )

        except Exception:

            pass

        try:

            queues.append(
                float(
                    data.get(
                        "queue_length",
                        0,
                    )
                )
            )

        except Exception:

            pass

        congestion_levels.append(
            data.get(
                "congestion_level",
                "LOW",
            )
        )

    average_speed = (
        sum(speeds) / len(speeds)
        if speeds
        else 0.0
    )

    total_queue = (
        sum(queues)
        if queues
        else 0.0
    )

    critical_junctions = congestion_levels.count(
        "CRITICAL"
    )

    high_junctions = congestion_levels.count(
        "HIGH"
    )

    # --------------------------------------------------------
    # Benchmark commuter time
    # --------------------------------------------------------

    baseline_minutes = (
        BASELINE_ROUTE_MINUTES
    )

    optimized_minutes = (
        baseline_minutes
        * (
            1
            - COMMUTER_IMPROVEMENT_TARGET
            / 100
        )
    )

    time_saved = (
        baseline_minutes
        - optimized_minutes
    )

    # --------------------------------------------------------
    # Optimization state
    # --------------------------------------------------------
    #
    # For now the panel is considered available whenever the
    # SUMO simulation is running.
    #
    # This does NOT mean the actual 10% improvement has been
    # experimentally achieved yet.
    # --------------------------------------------------------

    optimization_active = running

    # --------------------------------------------------------
    # Confidence indicator
    # --------------------------------------------------------

    if not running:

        confidence = "WAITING"

    elif critical_junctions > 0:

        confidence = "MONITORING"

    elif high_junctions > 0:

        confidence = "MONITORING"

    else:

        confidence = "READY"

    return {

        "route": {
            "from": "Andheri",
            "to": "Bandra",
        },

        "baseline_eta_minutes": round(
            baseline_minutes,
            1,
        ),

        "optimized_eta_minutes": round(
            optimized_minutes,
            1,
        ),

        "time_saved_minutes": round(
            time_saved,
            1,
        ),

        "improvement_percent": round(
            COMMUTER_IMPROVEMENT_TARGET,
            1,
        ),

        "target_percent": round(
            COMMUTER_IMPROVEMENT_TARGET,
            1,
        ),

        "optimization_active": (
            optimization_active
        ),

        "status": (
            "ACTIVE"
            if optimization_active
            else "STANDBY"
        ),

        "confidence": confidence,

        "live_network": {

            "running": running,

            "simulation_time": round(
                simulation_time,
                1,
            ),

            "vehicles": total_vehicles,

            "average_speed": round(
                average_speed,
                2,
            ),

            "total_queue": round(
                total_queue,
                1,
            ),

            "high_junctions": high_junctions,

            "critical_junctions": (
                critical_junctions
            ),
        },

        "measurement": {
            "type": "benchmark_target",
            "measured": False,
            "message": (
                "10% is currently the commuter "
                "optimization target. Actual measured "
                "improvement will be calculated after "
                "the signal optimization controller "
                "is connected to SUMO."
            ),
        },
    }