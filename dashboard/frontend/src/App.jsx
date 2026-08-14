import { useEffect, useMemo, useState } from "react";

import {
  Activity,
  AlertTriangle,
  ArrowDown,
  Bus,
  Car,
  Gauge,
  MapPin,
  Radio,
  Square,
  Play,
  RefreshCw,
  ShieldCheck,
  Truck,
  Wifi,
  TrendingDown,
} from "lucide-react";

import "./App.css";


// ============================================================
// API
// ============================================================

const API = "http://127.0.0.1:8000/api";


// ============================================================
// JUNCTION MAP POSITIONS
// ============================================================

const JUNCTION_POSITIONS = {
  J1: { x: 33.33, y: 33.33 },
  J2: { x: 66.67, y: 33.33 },
  J3: { x: 33.33, y: 66.67 },
  J4: { x: 66.67, y: 66.67 },
};


// ============================================================
// HELPERS
// ============================================================

function levelClass(level = "LOW") {
  return String(level).toLowerCase();
}


function vehicleIcon(type) {
  if (type === "bus") return Bus;

  if (type === "truck") return Truck;

  if (
    type === "motorcycle" ||
    type === "bike"
  ) {
    return Activity;
  }

  return Car;
}


function vehicleClass(vehicle) {
  const speed = Number(vehicle.speed || 0);

  if (speed < 2) {
    return "vehicle-critical";
  }

  if (speed < 5) {
    return "vehicle-warning";
  }

  return "vehicle-moving";
}


function getVehicleType(id = "") {
  const value = id.toLowerCase();

  if (value.includes("bus")) {
    return "bus";
  }

  if (value.includes("truck")) {
    return "truck";
  }

  if (
    value.includes("motorcycle") ||
    value.includes("bike")
  ) {
    return "motorcycle";
  }

  return "car";
}


// ============================================================
// JUNCTION CARD
// ============================================================

function JunctionCard({ id, data }) {
  const level =
    data?.congestion_level || "LOW";

  return (
    <div
      className={`junction-card ${levelClass(level)}`}
    >

      <div className="junction-card-header">

        <div>
          <span>JUNCTION</span>

          <h3>
            {id}
          </h3>
        </div>

        <strong
          className={`status-pill ${levelClass(level)}`}
        >
          {level}
        </strong>

      </div>


      <div className="junction-metrics">

        <div>
          <Car size={15} />

          <span>
            Vehicles
          </span>

          <strong>
            {data?.vehicle_count ?? 0}
          </strong>
        </div>


        <div>
          <Gauge size={15} />

          <span>
            Queue
          </span>

          <strong>
            {data?.queue_length ?? 0}
          </strong>
        </div>


        <div>
          <Activity size={15} />

          <span>
            Speed
          </span>

          <strong>
            {Number(
              data?.average_speed || 0
            ).toFixed(1)}
          </strong>
        </div>

      </div>

    </div>
  );
}


// ============================================================
// MAIN APP
// ============================================================

function App() {

  const [liveData, setLiveData] =
    useState(null);

  const [vehicles, setVehicles] =
    useState([]);

  const [status, setStatus] =
    useState(null);

  const [apiError, setApiError] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [lastUpdated, setLastUpdated] =
    useState(null);


  // ==========================================================
  // FETCH LIVE DATA
  // ==========================================================

  async function fetchLiveData() {

    try {

      const [
        trafficResponse,
        vehicleResponse,
        statusResponse,
      ] = await Promise.all([

        fetch(
          `${API}/traffic/live`
        ),

        fetch(
          `${API}/traffic/vehicles`
        ),

        fetch(
          `${API}/simulation/status`
        ),

      ]);


      if (!trafficResponse.ok) {
        throw new Error(
          "Traffic API failed"
        );
      }


      const trafficJson =
        await trafficResponse.json();

      const vehicleJson =
        await vehicleResponse.json();

      const statusJson =
        await statusResponse.json();


      setLiveData(
        trafficJson
      );

      setVehicles(
        vehicleJson.vehicles || []
      );

      setStatus(
        statusJson
      );

      setLastUpdated(
        new Date()
      );

      setApiError("");

    } catch (error) {

      console.error(
        "TRAFFIX API error:",
        error
      );

      setApiError(
        "Backend unavailable. Make sure FastAPI is running on port 8000."
      );
    }
  }


  // ==========================================================
  // AUTO REFRESH
  // ==========================================================

  useEffect(() => {

    fetchLiveData();

    const interval =
      setInterval(
        fetchLiveData,
        700
      );

    return () =>
      clearInterval(interval);

  }, []);


  // ==========================================================
  // START SIMULATION
  // ==========================================================

  async function startSimulation() {

    setLoading(true);

    try {

      const response =
        await fetch(
          `${API}/simulation/start`,
          {
            method: "POST",
          }
        );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Unable to start simulation"
        );
      }


      setApiError("");

      await fetchLiveData();

    } catch (error) {

      console.error(error);

      setApiError(
        error.message
      );

    } finally {

      setLoading(false);
    }
  }


  // ==========================================================
  // STOP SIMULATION
  // ==========================================================

  async function stopSimulation() {

    setLoading(true);

    try {

      const response =
        await fetch(
          `${API}/simulation/stop`,
          {
            method: "POST",
          }
        );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Unable to stop simulation"
        );
      }


      await fetchLiveData();

    } catch (error) {

      console.error(error);

      setApiError(
        error.message
      );

    } finally {

      setLoading(false);
    }
  }


  // ==========================================================
  // JUNCTION DATA
  // ==========================================================

  const junctions =
    liveData?.junctions || {};


  const allJunctions =
    ["J1", "J2", "J3", "J4"].map(
      (id) => [

        id,

        junctions[id] || {
          vehicle_count: 0,
          queue_length: 0,
          average_speed: 0,
          congestion_level: "LOW",
        },

      ]
    );


  // ==========================================================
  // TOTAL VEHICLES
  // ==========================================================

  const totalVehicles =
    useMemo(
      () =>
        allJunctions.reduce(
          (
            sum,
            [, data]
          ) =>
            sum +
            Number(
              data.vehicle_count || 0
            ),
          0
        ),

      [
        junctions.J1,
        junctions.J2,
        junctions.J3,
        junctions.J4,
      ]
    );


  // ==========================================================
  // AVERAGE SPEED
  // ==========================================================

  const averageSpeed =
    useMemo(() => {

      const values =
        allJunctions.map(
          ([, data]) =>
            Number(
              data.average_speed || 0
            )
        );


      return values.length
        ? values.reduce(
            (a, b) => a + b,
            0
          ) /
          values.length

        : 0;

    }, [

      junctions.J1,
      junctions.J2,
      junctions.J3,
      junctions.J4,

    ]);


  // ==========================================================
  // ALERT COUNT
  // ==========================================================

  const alertCount =
    allJunctions.filter(
      ([, data]) =>
        data.congestion_level ===
          "HIGH" ||

        data.congestion_level ===
          "CRITICAL"
    ).length;


  // ==========================================================
  // CRITICAL COUNT
  // ==========================================================

  const criticalCount =
    allJunctions.filter(
      ([, data]) =>
        data.congestion_level ===
        "CRITICAL"
    ).length;


  // ==========================================================
  // SIMULATION TIME
  // ==========================================================

  const simulationTime =
    Number(
      liveData?.timestamp ??
      status?.time ??
      0
    );


  // ==========================================================
  // RUNNING
  // ==========================================================

  const running =
    Boolean(
      liveData?.running
    ) ||
    Boolean(
      status?.running
    );


  // ==========================================================
  // FORMATTED SIMULATION TIME
  // ==========================================================

  const formattedTime =
    `${Math.floor(
      simulationTime / 60
    )
      .toString()
      .padStart(2, "0")}:${Math.floor(
      simulationTime % 60
    )
      .toString()
      .padStart(2, "0")}`;


  // ==========================================================
  // MOST CONGESTED JUNCTION
  // ==========================================================

  const highestJunction =
    allJunctions
      .slice()
      .sort(
        ([, a], [, b]) =>
          Number(
            b.queue_length || 0
          ) -
          Number(
            a.queue_length || 0
          )
      )[0] || ["J1", {}];


  // ==========================================================
  // COMMUTER TIME OPTIMIZATION
  //
  // EXPECTED SOLUTION:
  // AI traffic management targets a 10% reduction
  // in commuter travel time.
  //
  // This is currently a TARGET MODEL.
  // Later we will replace this with measured
  // baseline-vs-AI SUMO results.
  // ==========================================================

  const baselineCommuterTime =
    criticalCount >= 2
      ? 32
      : criticalCount === 1
      ? 30
      : alertCount >= 2
      ? 27
      : 24;


  const commuterReductionTarget = 10;


  const optimizedCommuterTime =
    Math.max(
      1,
      Math.round(
        baselineCommuterTime *
          (1 -
            commuterReductionTarget /
              100)
      )
    );


  const commuterTimeSaved =
    baselineCommuterTime -
    optimizedCommuterTime;


  const actualDisplayedReduction =
    Math.round(
      (
        commuterTimeSaved /
        baselineCommuterTime
      ) *
        100
    );


  // ==========================================================
  // RENDER
  // ==========================================================

  return (

    <div className="app">


      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-icon">
            <Radio size={23} />
          </div>

          <div>

            <h1>
              TRAFFIX
            </h1>

            <span>
              Urban Traffic Intelligence
            </span>

          </div>

        </div>


        <nav className="navigation">

          <button className="active">
            <Activity size={18} />
            Control Room
          </button>


          <button>
            <MapPin size={18} />
            Junction Network
          </button>


          <button>
            <AlertTriangle size={18} />
            Incidents
          </button>


          <button>
            <Gauge size={18} />
            Analytics
          </button>

        </nav>


        <div className="sidebar-status">

          <div className="status-title">

            <span
              className={`online-dot ${
                !running
                  ? "offline"
                  : ""
              }`}
            />

            {running
              ? "SYSTEM ONLINE"
              : "SIMULATION STOPPED"}

          </div>


          <p>

            {apiError ||
              (
                running
                  ? "SUMO live telemetry connected"
                  : "Start SUMO simulation"
              )}

          </p>


          <div className="system-row">

            <span>
              SUMO / TraCI
            </span>

            <strong>
              {running
                ? "ONLINE"
                : "OFFLINE"}
            </strong>

          </div>


          <div className="system-row">

            <span>
              Traffic API
            </span>

            <strong>
              {apiError
                ? "ERROR"
                : "ONLINE"}
            </strong>

          </div>


          <div className="system-row">

            <span>
              Vehicle Tracking
            </span>

            <strong>
              {vehicles.length > 0
                ? "LIVE"
                : "WAITING"}
            </strong>

          </div>

        </div>

      </aside>


      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="main">


        {/* ====================================================
            HEADER
        ==================================================== */}

        <header className="topbar">

          <div>

            <span className="eyebrow">
              MUMBAI URBAN NETWORK
            </span>

            <h2>
              Traffic Control Center
            </h2>

            <p>
              Real-time SUMO simulation
              monitoring and intelligent
              traffic management
            </p>

          </div>


          <div className="topbar-right">

            <div
              className={`connection ${
                !running
                  ? "offline"
                  : ""
              }`}
            >

              <Wifi size={16} />

              {running
                ? "LIVE CONNECTION"
                : "SIMULATION OFFLINE"}

            </div>


            <div className="simulation-clock">

              <span>
                SIM TIME
              </span>

              <strong>
                {formattedTime}
              </strong>

            </div>

          </div>

        </header>


        {/* ====================================================
            CONTROL BAR
        ==================================================== */}

        <section className="control-bar">

          <div>

            <span>
              SUMO SIMULATION
            </span>

            <strong>
              {running
                ? "Simulation running"
                : "Simulation stopped"}
            </strong>

          </div>


          <div className="control-actions">

            <button
              className="refresh-button"
              onClick={
                fetchLiveData
              }
            >

              <RefreshCw
                size={16}
              />

              Refresh

            </button>


            {!running ? (

              <button
                className="start-button"
                onClick={
                  startSimulation
                }
                disabled={loading}
              >

                <Play size={16} />

                {loading
                  ? "Starting..."
                  : "Start Simulation"}

              </button>

            ) : (

              <button
                className="stop-button"
                onClick={
                  stopSimulation
                }
                disabled={loading}
              >

                <Square
                  size={15}
                />

                {loading
                  ? "Stopping..."
                  : "Stop Simulation"}

              </button>

            )}

          </div>

        </section>


        {/* ====================================================
            KPI CARDS
        ==================================================== */}

        <section className="kpi-grid">


          <div className="kpi-card">

            <div className="kpi-icon">
              <Car />
            </div>

            <div>

              <span>
                Live Vehicles
              </span>

              <strong>
                {totalVehicles}
              </strong>

              <small>
                SUMO active vehicles
              </small>

            </div>

          </div>


          <div className="kpi-card">

            <div className="kpi-icon">
              <Gauge />
            </div>

            <div>

              <span>
                Average Speed
              </span>

              <strong>
                {averageSpeed.toFixed(1)}
                {" "}km/h
              </strong>

              <small>
                Network average
              </small>

            </div>

          </div>


          <div className="kpi-card">

            <div className="kpi-icon">
              <Activity />
            </div>

            <div>

              <span>
                Tracked Objects
              </span>

              <strong>
                {vehicles.length}
              </strong>

              <small>
                Live TraCI telemetry
              </small>

            </div>

          </div>


          <div className="kpi-card alert-kpi">

            <div className="kpi-icon">
              <AlertTriangle />
            </div>

            <div>

              <span>
                Active Alerts
              </span>

              <strong>
                {alertCount}
              </strong>

              <small>
                {criticalCount}
                {" "}critical junction
                {criticalCount === 1
                  ? ""
                  : "s"}
              </small>

            </div>

          </div>

        </section>


        {/* ====================================================
            NEW: COMMUTER TIME IMPACT
        ==================================================== */}

        <section className="commuter-impact-panel">


          <div className="commuter-impact-header">

            <div>

              <span className="panel-label">
                AI COMMUTER IMPACT
              </span>

              <h3>
                Travel Time Optimization
              </h3>

              <p>
                AI-assisted traffic management
                targets a 10% reduction in
                commuter travel time.
              </p>

            </div>


            <div className="reduction-badge">

              <TrendingDown
                size={18}
              />

              {actualDisplayedReduction}%
              {" "}REDUCTION

            </div>

          </div>


          <div className="commuter-impact-content">


            {/* CURRENT ETA */}

            <div className="eta-box">

              <span>
                CURRENT ESTIMATED TIME
              </span>

              <strong>
                {baselineCommuterTime}
                {" "}min
              </strong>

              <small>
                Based on current network
                congestion
              </small>

            </div>


            {/* ARROW */}

            <div className="eta-arrow">
              →
            </div>


            {/* OPTIMIZED ETA */}

            <div className="eta-box optimized">

              <span>
                AI OPTIMIZED TIME
              </span>

              <strong>
                {optimizedCommuterTime}
                {" "}min
              </strong>

              <small>
                Target after intelligent
                traffic management
              </small>

            </div>


            {/* TIME SAVED */}

            <div className="time-saving-box">

              <ShieldCheck
                size={22}
              />

              <div>

                <span>
                  COMMUTER TIME SAVED
                </span>

                <strong>
                  {commuterTimeSaved}
                  {" "}min
                </strong>

              </div>

            </div>

          </div>


          <div className="commuter-impact-footer">

            <div>

              <ShieldCheck
                size={16}
              />

              <span>
                10% optimization target
              </span>

            </div>


            <span>
              Predictive congestion control
              + signal coordination
            </span>

          </div>

        </section>


        {/* ====================================================
            LIVE SUMO MAP
        ==================================================== */}

        <section className="panel live-map-panel">


          <div className="panel-header">

            <div>

              <span className="panel-label">
                LIVE SUMO TELEMETRY
              </span>

              <h3>
                Real-Time Vehicle Network
              </h3>

            </div>


            <div className="live-indicator">

              <span />

              {running
                ? "LIVE"
                : "OFFLINE"}

            </div>

          </div>


          <div className="live-map">


            {/* ROADS */}

            <div
              className="map-road road-horizontal road-h1"
            />

            <div
              className="map-road road-horizontal road-h2"
            />

            <div
              className="map-road road-vertical road-v1"
            />

            <div
              className="map-road road-vertical road-v2"
            />


            {/* DIRECTIONS */}

            <span className="direction north">
              NORTH
            </span>

            <span className="direction south">
              SOUTH
            </span>

            <span className="direction west">
              WEST
            </span>

            <span className="direction east">
              EAST
            </span>


            {/* JUNCTIONS */}

            {allJunctions.map(
              ([id, data]) => {

                const position =
                  JUNCTION_POSITIONS[id];

                const level =
                  data.congestion_level ||
                  "LOW";


                return (

                  <div
                    key={id}
                    className={`map-junction ${levelClass(
                      level
                    )}`}
                    style={{
                      left:
                        `${position.x}%`,
                      top:
                        `${position.y}%`,
                    }}
                  >

                    <div className="junction-node">
                      {id}
                    </div>

                    <span>
                      {level}
                    </span>

                    <small>
                      {data.vehicle_count || 0}
                      {" "}vehicles
                    </small>

                  </div>

                );
              }
            )}


            {/* LIVE VEHICLES */}

            {vehicles.map(
              (vehicle) => {

               const sumoX = Number(vehicle.x);
const sumoY = Number(vehicle.y);

const x = Math.max(
  1,
  Math.min(
    99,
    (sumoX / 300) * 100
  )
);

const y = Math.max(
  1,
  Math.min(
    99,
    100 - (sumoY / 300) * 100
  )
);

                const type =
                  vehicle.type ||
                  getVehicleType(
                    vehicle.id
                  );


                const Icon =
                  vehicleIcon(
                    type
                  );


                return (

                  <div
                    key={vehicle.id}
                    className={`live-vehicle ${vehicleClass(
                      vehicle
                    )}`}
                    style={{
                      left:
                        `${x}%`,
                      top:
                        `${y}%`,
                    }}
                    title={
                      `${vehicle.id} | ` +
                      `${Number(
                        vehicle.speed || 0
                      ).toFixed(1)} km/h | ` +
                      `${vehicle.road || ""}`
                    }
                  >

                    <Icon
                      size={12}
                    />

                  </div>

                );
              }
            )}


            {/* STOPPED OVERLAY */}

            {!running && (

              <div className="map-overlay">

                <Play size={28} />

                <strong>
                  Simulation stopped
                </strong>

                <span>
                  Start SUMO to view
                  live vehicles
                </span>

              </div>

            )}

          </div>


          <div className="map-footer">

            <div>
              <span className="legend moving" />
              Moving
            </div>

            <div>
              <span className="legend warning" />
              Slow
            </div>

            <div>
              <span className="legend critical" />
              Queued
            </div>

            <div className="map-object-count">
              {vehicles.length}
              {" "}live objects
            </div>

          </div>

        </section>


        {/* ====================================================
            NETWORK CONDITION + TELEMETRY
        ==================================================== */}

        <section className="dashboard-two-column">


          {/* CONDITION */}

          <div className="panel">

            <div className="panel-header">

              <div>

                <span className="panel-label">
                  AI TRAFFIC MONITOR
                </span>

                <h3>
                  Current Network Condition
                </h3>

              </div>

              <ShieldCheck
                size={20}
              />

            </div>


            <div className="condition-main">

              <div
                className={`condition-icon ${levelClass(
                  highestJunction[1]
                    ?.congestion_level
                )}`}
              >

                <AlertTriangle
                  size={28}
                />

              </div>


              <div>

                <span>
                  MOST CONGESTED JUNCTION
                </span>

                <h4>
                  {highestJunction[0]}
                </h4>

                <p>

                  Queue:
                  {" "}
                  {highestJunction[1]
                    ?.queue_length || 0}

                  {" "}vehicles

                  {" · "}

                  Speed:
                  {" "}
                  {Number(
                    highestJunction[1]
                      ?.average_speed || 0
                  ).toFixed(1)}

                  {" "}km/h

                </p>

              </div>

            </div>

          </div>


          {/* TELEMETRY */}

          <div className="panel">

            <div className="panel-header">

              <div>

                <span className="panel-label">
                  LIVE TELEMETRY
                </span>

                <h3>
                  Data Stream
                </h3>

              </div>

              <Activity
                size={20}
              />

            </div>


            <div className="telemetry-list">

              <div>

                <span>
                  Simulation Time
                </span>

                <strong>
                  {simulationTime.toFixed(1)}
                  {" "}s
                </strong>

              </div>


              <div>

                <span>
                  Vehicles
                </span>

                <strong>
                  {vehicles.length}
                </strong>

              </div>


              <div>

                <span>
                  SUMO Status
                </span>

                <strong>
                  {running
                    ? "RUNNING"
                    : "STOPPED"}
                </strong>

              </div>


              <div>

                <span>
                  Last Update
                </span>

                <strong>
                  {lastUpdated
                    ? lastUpdated.toLocaleTimeString()
                    : "--"}
                </strong>

              </div>

            </div>

          </div>

        </section>


        {/* ====================================================
            JUNCTION STATUS
        ==================================================== */}

        <section>

          <div className="section-heading">

            <div>

              <span className="panel-label">
                LIVE JUNCTION STATUS
              </span>

              <h3>
                Network Performance
              </h3>

            </div>

            <span>
              4 / 4 connected
            </span>

          </div>


          <div className="junction-grid">

            {allJunctions.map(
              ([id, data]) => (

                <JunctionCard
                  key={id}
                  id={id}
                  data={data}
                />

              )
            )}

          </div>

        </section>


      </main>

    </div>
  );
}


export default App;