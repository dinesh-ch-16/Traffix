import os
import time
import socket
import threading
import subprocess
from pathlib import Path

import traci
from fastapi import APIRouter, HTTPException



router = APIRouter(
    prefix="/api",
    tags=["live simulation"],
)


# ============================================================
# SUMO PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SUMO_HOME = os.environ.get(
    "SUMO_HOME",
    r"C:\Program Files (x86)\Eclipse\Sumo",
)

SUMO_BINARY = Path(SUMO_HOME) / "bin" / "sumo.exe"
SUMO_GUI = Path(SUMO_HOME) / "bin" / "sumo-gui.exe"

SUMO_CONFIG = (
    PROJECT_ROOT
    / "simulation"
    / "sumo"
    / "configs"
    / "traffix.sumocfg"
)


# ============================================================
# GLOBAL STATE
# ============================================================

state_lock = threading.Lock()

simulation = {
    "running": False,
    "time": 0.0,
    "vehicles": 0,
    "started_at": None,
    "error": None,
}

junction_state = {}

# Snapshot of vehicles.
# ONLY the simulation thread writes this.
# API endpoints only read it.
vehicle_state = []

sumo_process = None
simulation_thread = None

# TraCI connection belongs exclusively to
# the simulation thread.
traci_connection = None


JUNCTIONS = [
    "J1",
    "J2",
    "J3",
    "J4",
]


# ============================================================
# ADAPTIVE SIGNAL CONTROL
# ============================================================

SIGNAL_JUNCTIONS = [
    "J1",
    "J2",
    "J3",
    "J4",
]


signal_control = {
    junction_id: {
        "junction": junction_id,
        "mode": "AUTO",
        "action": "NORMAL",
        "phase": 0,
        "phase_duration": 42.0,
        "next_switch": 0.0,
        "queue": 0,
        "vehicles": 0,
        "average_speed": 0.0,
        "average_waiting": 0.0,
        "extension": 0.0,
        "last_change": None,
        "error": None,
    }
    for junction_id in SIGNAL_JUNCTIONS
}


# ============================================================
# FIND FREE PORT
# ============================================================

def find_free_port():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    try:

        sock.bind(
            ("127.0.0.1", 0)
        )

        return sock.getsockname()[1]

    finally:

        sock.close()


# ============================================================
# CONGESTION
# ============================================================

def calculate_congestion(
    vehicle_count,
    queue_length,
    average_speed,
):

    vehicle_count = int(
        vehicle_count or 0
    )

    queue_length = int(
        queue_length or 0
    )

    average_speed = float(
        average_speed or 0
    )

    if vehicle_count == 0:
        return "LOW"

    if (
        average_speed < 3
        or queue_length >= 8
    ):
        return "CRITICAL"

    if (
        average_speed < 5
        or queue_length >= 5
    ):
        return "HIGH"

    if (
        average_speed < 9
        or queue_length >= 2
    ):
        return "MODERATE"

    return "LOW"


# ============================================================
# JUNCTION STATE
# ============================================================

def calculate_junction_state(
    conn,
    junction_id,
):

    try:

        incoming_edges = (
            conn.junction.getIncomingEdges(
                junction_id
            )
        )

    except Exception:

        incoming_edges = []

    vehicle_ids = set()

    total_speed = 0.0
    total_waiting = 0.0

    queue_length = 0

    for edge_id in incoming_edges:

        try:

            ids = (
                conn.edge.getLastStepVehicleIDs(
                    edge_id
                )
            )

        except Exception:

            continue

        for vehicle_id in ids:

            if vehicle_id in vehicle_ids:
                continue

            vehicle_ids.add(vehicle_id)

            try:

                speed = conn.vehicle.getSpeed(
                    vehicle_id
                )

                waiting = conn.vehicle.getWaitingTime(
                    vehicle_id
                )

                total_speed += float(speed)
                total_waiting += float(waiting)

                if float(speed) < 2.0:
                    queue_length += 1

            except Exception:

                continue

    count = len(vehicle_ids)

    if count > 0:

        average_speed = (
            total_speed / count
        )

        average_waiting = (
            total_waiting / count
        )

    else:

        average_speed = 0.0
        average_waiting = 0.0

    congestion = calculate_congestion(
        count,
        queue_length,
        average_speed,
    )

    return {
        "junction": junction_id,
        "vehicle_count": count,
        "queue_length": queue_length,
        "average_speed": round(
            average_speed,
            2,
        ),
        "average_waiting": round(
            average_waiting,
            2,
        ),
        "congestion_level": congestion,
    }


# ============================================================
# VEHICLE SNAPSHOT
# ============================================================

def update_vehicle_state(conn):

    global vehicle_state

    vehicles = []

    try:

        vehicle_ids = (
            conn.vehicle.getIDList()
        )

    except Exception as exc:

        print(
            "[TRAFFIX] Vehicle list error:",
            repr(exc),
        )

        return

    for vehicle_id in vehicle_ids:

        try:

            x, y = (
                conn.vehicle.getPosition(
                    vehicle_id
                )
            )

            speed = (
                conn.vehicle.getSpeed(
                    vehicle_id
                )
            )

            waiting = (
                conn.vehicle.getWaitingTime(
                    vehicle_id
                )
            )

            road = (
                conn.vehicle.getRoadID(
                    vehicle_id
                )
            )

            vehicle_type = "car"

            try:

                vehicle_type_id = (
                    conn.vehicle.getTypeID(
                        vehicle_id
                    )
                )

                value = (
                    vehicle_type_id or ""
                ).lower()

                if "bus" in value:

                    vehicle_type = "bus"

                elif "truck" in value:

                    vehicle_type = "truck"

                elif (
                    "motorcycle" in value
                    or "bike" in value
                ):

                    vehicle_type = "motorcycle"

            except Exception:

                vehicle_type = "car"

            vehicles.append(
                {
                    "id": vehicle_id,

                    "speed": round(
                        float(speed),
                        2,
                    ),

                    "waiting": round(
                        float(waiting),
                        2,
                    ),

                    "road": road,

                    "type": vehicle_type,

                    "x": round(
                        float(x),
                        2,
                    ),

                    "y": round(
                        float(y),
                        2,
                    ),
                }
            )

        except Exception:

            continue

    with state_lock:

        vehicle_state = vehicles

        simulation["vehicles"] = len(
            vehicles
        )


# ============================================================
# LIVE JUNCTION STATE
# ============================================================

def update_live_state(conn):

    global junction_state

    current_time = (
        conn.simulation.getTime()
    )

    new_junction_state = {}

    for junction_id in JUNCTIONS:

        try:

            new_junction_state[junction_id] = (
                calculate_junction_state(
                    conn,
                    junction_id,
                )
            )

        except Exception as exc:

            new_junction_state[junction_id] = {
                "junction": junction_id,
                "vehicle_count": 0,
                "queue_length": 0,
                "average_speed": 0.0,
                "average_waiting": 0.0,
                "congestion_level": "LOW",
                "error": str(exc),
            }

    with state_lock:

        simulation["time"] = round(
            float(current_time),
            1,
        )

        junction_state = (
            new_junction_state
        )


# ============================================================
# SIGNAL DECISION
# ============================================================

def calculate_signal_action(
    queue_length,
    average_waiting,
    average_speed,
):

    queue_length = float(
        queue_length or 0
    )

    average_waiting = float(
        average_waiting or 0
    )

    average_speed = float(
        average_speed or 0
    )

    # CRITICAL
    if (
        queue_length >= 12
        or average_waiting >= 30
    ):

        return {
            "action": "EXTEND_GREEN",
            "extension": 8.0,
        }

    # HIGH
    if (
        queue_length >= 6
        or average_waiting >= 15
    ):

        return {
            "action": "EXTEND_GREEN",
            "extension": 4.0,
        }

    # VERY LOW SPEED
    if (
        average_speed > 0
        and average_speed < 3
    ):

        return {
            "action": "EXTEND_GREEN",
            "extension": 4.0,
        }

    # NORMAL
    return {
        "action": "NORMAL",
        "extension": 0.0,
    }


# ============================================================
# ADAPTIVE SIGNAL CONTROLLER
# ============================================================

def update_signal_control(conn):

    global signal_control

    try:

        traffic_lights = (
            conn.trafficlight.getIDList()
        )

    except Exception as exc:

        print(
            "[TRAFFIX] Traffic-light read error:",
            repr(exc),
        )

        return

    current_time = (
        conn.simulation.getTime()
    )

    for junction_id in SIGNAL_JUNCTIONS:

        if junction_id not in traffic_lights:
            continue

        try:

            phase = (
                conn.trafficlight.getPhase(
                    junction_id
                )
            )

            phase_duration = (
                conn.trafficlight.getPhaseDuration(
                    junction_id
                )
            )

            next_switch = (
                conn.trafficlight.getNextSwitch(
                    junction_id
                )
            )

            with state_lock:

                junction = (
                    junction_state.get(
                        junction_id,
                        {},
                    ).copy()
                )

            queue_length = junction.get(
                "queue_length",
                0,
            )

            vehicle_count = junction.get(
                "vehicle_count",
                0,
            )

            average_speed = junction.get(
                "average_speed",
                0,
            )

            average_waiting = junction.get(
                "average_waiting",
                0,
            )

            decision = (
                calculate_signal_action(
                    queue_length,
                    average_waiting,
                    average_speed,
                )
            )

            action = decision[
                "action"
            ]

            requested_extension = (
                decision[
                    "extension"
                ]
            )

            # Current network has:
            #
            # phase 0 = green
            # phase 1 = yellow
            # phase 2 = green
            # phase 3 = yellow

            green_phase = phase in (
                0,
                2,
            )

            remaining_time = (
                float(next_switch)
                - float(current_time)
            )

            applied_extension = 0.0

            should_extend = (
                action
                == "EXTEND_GREEN"
                and green_phase
                and requested_extension > 0
                and remaining_time <= 5.0
            )

            if should_extend:

                new_duration = (
                    float(phase_duration)
                    + float(
                        requested_extension
                    )
                )

                # Safety limits
                new_duration = max(
                    new_duration,
                    20.0,
                )

                new_duration = min(
                    new_duration,
                    60.0,
                )

                conn.trafficlight.setPhaseDuration(
                    junction_id,
                    new_duration,
                )

                applied_extension = (
                    new_duration
                    - float(
                        phase_duration
                    )
                )

            with state_lock:

                previous_change = (
                    signal_control[
                        junction_id
                    ].get(
                        "last_change"
                    )
                )

                signal_control[
                    junction_id
                ] = {

                    "junction": junction_id,

                    "mode": "AUTO",

                    "action": (
                        "EXTEND_GREEN"
                        if applied_extension > 0
                        else action
                    ),

                    "phase": int(
                        phase
                    ),

                    "phase_duration": round(
                        float(
                            phase_duration
                        ),
                        1,
                    ),

                    "next_switch": round(
                        float(
                            next_switch
                        ),
                        1,
                    ),

                    "queue": int(
                        queue_length
                    ),

                    "vehicles": int(
                        vehicle_count
                    ),

                    "average_speed": round(
                        float(
                            average_speed
                        ),
                        2,
                    ),

                    "average_waiting": round(
                        float(
                            average_waiting
                        ),
                        2,
                    ),

                    "extension": round(
                        float(
                            applied_extension
                        ),
                        1,
                    ),

                    "last_change": (
                        time.time()
                        if applied_extension > 0
                        else previous_change
                    ),

                    "error": None,
                }

        except Exception as exc:

            print(
                f"[TRAFFIX] Signal controller "
                f"{junction_id} error:",
                repr(exc),
            )

            with state_lock:

                signal_control[
                    junction_id
                ]["error"] = str(exc)


# ============================================================
# SIGNAL STATUS
# ============================================================

@router.get("/signals/status")
def signal_status():

    with state_lock:

        return {
            "running": simulation["running"],
            "simulation_time": simulation["time"],
            "controller": "AUTO",
            "junctions": {
                junction_id: data.copy()
                for junction_id, data
                in signal_control.items()
            },
        }


# ============================================================
# ENABLE AUTO CONTROL
# ============================================================

@router.post("/signals/auto")
def enable_signal_auto():

    with state_lock:

        for junction_id in SIGNAL_JUNCTIONS:

            signal_control[
                junction_id
            ]["mode"] = "AUTO"

    return {
        "status": "enabled",
        "controller": "AUTO",
        "junctions": SIGNAL_JUNCTIONS,
    }


# ============================================================
# SIMULATION LOOP
# ============================================================

def simulation_loop(port):

    global traci_connection
    global sumo_process

    conn = None

    try:

        # ====================================================
        # CONNECT TO SUMO
        # ====================================================

        print(
            f"[TRAFFIX] Connecting to SUMO "
            f"on port {port}..."
        )

        conn = traci.connect(
            port=port,
            host="127.0.0.1",
        )

        traci_connection = conn

        print(
            "[TRAFFIX] TraCI connected."
        )

        # ====================================================
        # READ INITIAL TIME
        # ====================================================

        try:

            initial_time = (
                conn.simulation.getTime()
            )

            print(
                "[TRAFFIX] Initial SUMO time:",
                initial_time,
            )

        except Exception as exc:

            print(
                "[TRAFFIX] Initial time error:",
                repr(exc),
            )

        with state_lock:

            simulation["running"] = True
            simulation["error"] = None

        # ====================================================
        # MAIN LOOP
        # ====================================================

        while True:

            with state_lock:

                if not simulation["running"]:

                    print(
                        "[TRAFFIX] Stop requested."
                    )

                    break

            # =================================================
            # ADVANCE SUMO
            # =================================================

            try:

                conn.simulationStep()

            except Exception as exc:

                print(
                    "[TRAFFIX] simulationStep ERROR:",
                    repr(exc),
                )

                with state_lock:

                    simulation["running"] = False
                    simulation["error"] = str(
                        exc
                    )

                break

            # =================================================
            # READ TIME
            # =================================================

            try:

                current_time = (
                    conn.simulation.getTime()
                )

                print(
                    f"[TRAFFIX] SUMO time: "
                    f"{current_time}"
                )

                with state_lock:

                    simulation["time"] = round(
                        float(current_time),
                        1,
                    )

            except Exception as exc:

                print(
                    "[TRAFFIX] Time read error:",
                    repr(exc),
                )

            # =================================================
            # UPDATE VEHICLES
            # =================================================

            try:

                update_vehicle_state(
                    conn
                )

            except Exception as exc:

                print(
                    "[TRAFFIX] Vehicle update error:",
                    repr(exc),
                )

            # =================================================
            # UPDATE JUNCTIONS
            # =================================================

            try:

                update_live_state(
                    conn
                )

            except Exception as exc:

                print(
                    "[TRAFFIX] Junction update error:",
                    repr(exc),
                )

            # =================================================
            # ADAPTIVE SIGNAL CONTROL
            # =================================================

            try:

                update_signal_control(
                    conn
                )

            except Exception as exc:

                print(
                    "[TRAFFIX] Signal controller error:",
                    repr(exc),
                )

                with state_lock:

                    simulation["error"] = (
                        f"Signal controller: {exc}"
                    )

            # =================================================
            # REAL-TIME PACE
            # =================================================

            time.sleep(0.5)

    except Exception as exc:

        print(
            "[TRAFFIX] Simulation worker ERROR:",
            repr(exc),
        )

        with state_lock:

            simulation["running"] = False
            simulation["error"] = str(exc)

    finally:

        print(
            "[TRAFFIX] Simulation worker stopping."
        )

        # ====================================================
        # CLOSE TRACI
        # ====================================================

        try:

            if conn is not None:

                conn.close()

        except Exception as exc:

            print(
                "[TRAFFIX] TraCI close error:",
                repr(exc),
            )

        traci_connection = None

        # ====================================================
        # RESET STATE
        # ====================================================

        with state_lock:

            simulation["running"] = False

        # ====================================================
        # STOP SUMO
        # ====================================================

        try:

            if (
                sumo_process is not None
                and sumo_process.poll() is None
            ):

                print(
                    "[TRAFFIX] Closing SUMO..."
                )

                sumo_process.terminate()

                try:
                    sumo_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    sumo_process.kill()

        except Exception as exc:

            print(
                "[TRAFFIX] SUMO close error:",
                repr(exc),
            )

        sumo_process = None

        print(
            "[TRAFFIX] Simulation worker finished."
        )


# ============================================================
# START SIMULATION
# ============================================================

@router.post("/simulation/start")
def start_simulation():

    global sumo_process
    global simulation_thread
    global vehicle_state

    # ========================================================
    # PREVENT DUPLICATE SIMULATION
    # ========================================================

    with state_lock:

        if simulation["running"]:

            return {
                "status": "already_running",
                **simulation,
            }

    # ========================================================
    # VALIDATE SUMO
    # ========================================================

    if not SUMO_BINARY.exists():

        raise HTTPException(
            status_code=500,
            detail=(
                f"SUMO binary not found: "
                f"{SUMO_BINARY}"
            ),
        )

    # ========================================================
    # VALIDATE CONFIG
    # ========================================================

    if not SUMO_CONFIG.exists():

        raise HTTPException(
            status_code=500,
            detail=(
                f"SUMO config not found: "
                f"{SUMO_CONFIG}"
            ),
        )

    # ========================================================
    # CLEAN OLD SUMO PROCESS
    # ========================================================

    try:

        if (
            sumo_process is not None
            and sumo_process.poll() is None
        ):

            print(
                "[TRAFFIX] Stopping previous SUMO process..."
            )

            sumo_process.terminate()

            try:

                sumo_process.wait(
                    timeout=3
                )

            except subprocess.TimeoutExpired:

                sumo_process.kill()

    except Exception as exc:

        print(
            "[TRAFFIX] Old SUMO cleanup error:",
            repr(exc),
        )

    # ========================================================
    # FIND PORT
    # ========================================================

    port = find_free_port()

    print(
        f"[TRAFFIX] Starting SUMO "
        f"on port {port}"
    )

    # ========================================================
    # RESET STATE
    # ========================================================

    with state_lock:

        simulation["running"] = False
        simulation["time"] = 0.0
        simulation["vehicles"] = 0
        simulation["started_at"] = time.time()
        simulation["error"] = None

        junction_state.clear()

        vehicle_state = []

        for junction_id in SIGNAL_JUNCTIONS:

            signal_control[
                junction_id
            ] = {

                "junction": junction_id,

                "mode": "AUTO",

                "action": "NORMAL",

                "phase": 0,

                "phase_duration": 42.0,

                "next_switch": 0.0,

                "queue": 0,

                "vehicles": 0,

                "average_speed": 0.0,

                "average_waiting": 0.0,

                "extension": 0.0,

                "last_change": None,

                "error": None,
            }

    # ========================================================
    # SUMO COMMAND
    # ========================================================

    command = [

        str(SUMO_BINARY),

        "-c",

        str(SUMO_CONFIG),

        "--remote-port",

        str(port),

        # Start simulation automatically.
        "--start",

        # Close SUMO when simulation reaches its end.
        "--quit-on-end",

        # Run simulation at normal speed.
        "--delay",

        "0",

    ]

    print(
        "[TRAFFIX] SUMO command:",
        " ".join(command),
    )

    # ========================================================
    # START SUMO
    # ========================================================

    try:

        sumo_process = subprocess.Popen(
            command,
            cwd=str(PROJECT_ROOT),
        )

    except Exception as exc:

        with state_lock:

            simulation["error"] = str(
                exc
            )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to start SUMO: "
                f"{exc}"
            ),
        )

    # ========================================================
    # START SIMULATION THREAD
    # ========================================================

    simulation_thread = threading.Thread(
        target=simulation_loop,
        args=(port,),
        daemon=True,
        name="TraffixSUMOThread",
    )

    simulation_thread.start()

    # ========================================================
    # WAIT FOR TRACI CONNECTION
    # ========================================================

    for _ in range(50):

        time.sleep(0.2)

        with state_lock:

            if simulation["running"]:

                return {
                    "status": "started",
                    "sumo": "SUMO",
                    "port": port,
                    **simulation,
                }

            error = simulation["error"]

        # ----------------------------------------------------
        # SUMO crashed
        # ----------------------------------------------------

        if (
            sumo_process is not None
            and sumo_process.poll() is not None
        ):

            with state_lock:

                if not simulation["error"]:

                    simulation["error"] = (
                        "SUMO exited before "
                        "TraCI connected."
                    )

                error = simulation["error"]

            break

        if error:

            break

    # ========================================================
    # CONNECTION FAILED
    # ========================================================

    with state_lock:

        error = simulation["error"]

    if error:

        try:

            if (
                sumo_process is not None
                and sumo_process.poll() is None
            ):

                sumo_process.terminate()

        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=error,
        )

    # ========================================================
    # STILL STARTING
    # ========================================================

    return {
        "status": "starting",
        "sumo": "SUMO",
        "port": port,
        **simulation,
    }


# ============================================================
# STOP SIMULATION
# ============================================================

@router.post("/simulation/stop")
def stop_simulation():

    with state_lock:

        if not simulation["running"]:

            return {
                "status": "already_stopped",
                **simulation,
            }

        simulation["running"] = False

    return {
        "status": "stopping",
        **simulation,
    }


# ============================================================
# SIMULATION STATUS
# ============================================================

@router.get("/simulation/status")
def simulation_status():

    with state_lock:

        return {
            "running": simulation["running"],
            "time": simulation["time"],
            "vehicles": simulation["vehicles"],
            "started_at": simulation["started_at"],
            "error": simulation["error"],
        }


# ============================================================
# LIVE TRAFFIC
# ============================================================

@router.get("/traffic/live")
def live_traffic():

    with state_lock:

        return {
            "running": simulation["running"],
            "timestamp": simulation["time"],
            "vehicles": simulation["vehicles"],
            "junctions": {
                junction_id: data.copy()
                for junction_id, data
                in junction_state.items()
            },
        }


# ============================================================
# LIVE VEHICLES
# ============================================================

@router.get("/traffic/vehicles")
def live_vehicles():

    with state_lock:

        return {
            "running": simulation["running"],
            "vehicles": [
                vehicle.copy()
                for vehicle in vehicle_state
            ],
        }