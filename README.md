# DC Motor Digital Twin

A small Digital Twin platform for a brushed DC motor. The project is meant to walk through the full Digital Twin workflow:

**Physical system simulation → mathematical model → virtual model → synchronization → parameter estimation → adaptive Digital Twin → real-time API → 3D visualization**

This version contains the Python simulation backend, a FastAPI layer, and a React dashboard. The 3D motor view and database are still out of scope.

## Current scope

- First-principles DC motor model (electrical + mechanical ODEs)
- Simulated physical motor with its own parameter set
- Digital Twin with independent (intentionally incorrect) parameters
- Lockstep synchronization: measurement → prediction → error
- Adaptive parameter estimation of `J`, `b`, and `R` with SciPy
- Physical vs virtual comparison (error, MAE, relative error, RMSE)
- FastAPI backend for motor state, simulation control, and adaptation
- React / Vite dashboard with live WebSocket charts
- Numerical simulation with SciPy `solve_ivp`
- Matplotlib plots of current and RPM
- Unit tests for the model, simulator, Digital Twin, and API

## Requirements

- Python 3.11+
- NumPy, SciPy, Pandas, Matplotlib
- FastAPI, Uvicorn
- Node.js 20+ for the dashboard

## Project structure

```
dc-motor-digital-twin/
├── models/              # Mathematical motor model
├── simulation/          # Time-domain integration (solve_ivp)
├── identification/      # Parameter estimation
├── visualization/       # Matplotlib plots
├── api/                 # FastAPI backend
├── frontend/            # React dashboard
├── examples/            # Example simulations
├── tests/               # Unit tests
├── main.py              # Demo simulation
├── requirements.txt
└── README.md
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the demo

From the project root:

```bash
python main.py
```

Same example, called directly:

```bash
python examples/step_response.py
```

This starts the motor at rest, applies 12 V and a constant 0.05 N·m load for 5 seconds, and writes `outputs/step_response.png` (RPM and current).

Physical-motor measurements (reference plant):

```bash
python examples/physical_motor.py
```

This uses the physical parameter set, starts from rest at 12 V with a constant load, and writes `outputs/physical_measurements.csv`.

Physical motor vs Digital Twin (open-loop, no adaptation):

```bash
python examples/digital_twin.py
```

This writes `outputs/physical_vs_twin.png` and prints RPM/current RMSE.

Lockstep synchronization (still no parameter adaptation):

```bash
python examples/synchronize.py
```

This walks the physical measurements one sample at a time, stores the sync dataset, and writes `outputs/sync_dataset.csv` plus `outputs/sync_physical_vs_twin.png`.

Parameter adaptation (`J`, `b`, `R`; `Kt` and `Ke` stay fixed):

```bash
python examples/adapt.py
```

This prints RPM RMSE before and after, the initial / estimated / physical parameters, and writes `outputs/adaptation.png`.

## Run the API

```bash
python -m uvicorn api.app:app --reload
```

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness check |
| `GET` | `/motor/state` | Physical motor snapshot |
| `GET` | `/twin/state` | Digital Twin snapshot, error, parameters |
| `GET` | `/simulation/results` | Last synchronized time series |
| `POST` | `/simulation/start` | Run a simulation with the current controls |
| `POST` | `/simulation/stop` | Mark the session as stopped |
| `POST` | `/motor/control` | Set voltage and load torque |
| `POST` | `/twin/adapt` | Estimate `J`, `b`, `R` and update the twin |
| `WS` | `/ws/simulation` | Live physical vs twin frames while connected |

`/ws/simulation` streams JSON frames (`timestamp`, RPM/current, voltage, torque, `rpm_error`, `twin_accuracy`) until the client disconnects or `POST /simulation/stop` is called. Query parameters: `dt` (physics step) and `interval` (seconds between messages).

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Run the dashboard

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). The Vite dev server proxies REST and WebSocket calls to the API on port 8000.

The dashboard shows physical and twin RPM/current, voltage, torque, error, accuracy, live parameters, and a physical-vs-twin chart. Controls: start/stop, voltage, load torque, and Adapt Digital Twin.

## Run the tests

```bash
python -m unittest discover -s tests
```

## Motor model

The motor is represented by two coupled first-order ODEs:

```
V = R * i + L * di/dt + Ke * ω
J * dω/dt = Kt * i - b * ω - T_load
```

Implemented in `models/motor.py` as `MotorModel`.

| Symbol | Meaning |
| --- | --- |
| `R` | Armature resistance [Ω] |
| `L` | Armature inductance [H] |
| `J` | Rotor inertia [kg·m²] |
| `b` | Viscous friction [N·m·s/rad] |
| `Ke` | Back-EMF constant [V·s/rad] |
| `Kt` | Torque constant [N·m/A] |

States are armature current `i` and angular velocity `ω`. The simulator also reports:

- `rpm` = `ω * 60 / (2π)`
- `torque_em` = `Kt * i`

Physical and Digital Twin parameters are stored separately in `models/parameters.py`. The twin starts with intentionally incorrect values:

| Parameter | Physical | Digital Twin |
| --- | ---: | ---: |
| `R` | 2.2 Ω | 2.0 Ω |
| `L` | 0.5 H | 0.5 H |
| `J` | 0.013 kg·m² | 0.010 kg·m² |
| `b` | 0.12 N·m·s/rad | 0.10 N·m·s/rad |
| `Kt` | 0.05 N·m/A | 0.05 N·m/A |
| `Ke` | 0.05 V·s/rad | 0.05 V·s/rad |

## Next steps

- Online / recursive parameter updates
- 3D visualization and persistence

