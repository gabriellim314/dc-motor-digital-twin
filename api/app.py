"""FastAPI application for the DC Motor Digital Twin."""

from __future__ import annotations

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    AdaptRequest,
    AdaptResponse,
    HealthResponse,
    MotorControlRequest,
    MotorStateResponse,
    SimulationResultsResponse,
    SimulationSample,
    SimulationStartRequest,
    SimulationStatusResponse,
    TwinErrorModel,
    TwinParametersModel,
    TwinStateResponse,
)
from dataclasses import asdict

from api.realtime import stream_simulation
from api.service import MotorTwinService, parameters_to_dict


def create_app(service: MotorTwinService | None = None) -> FastAPI:
    session = service or MotorTwinService()
    app = FastAPI(title="DC Motor Digital Twin API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/motor/state", response_model=MotorStateResponse)
    def motor_state() -> MotorStateResponse:
        return MotorStateResponse.model_validate(asdict(session.motor_state()))

    @app.get("/twin/state", response_model=TwinStateResponse)
    def twin_state() -> TwinStateResponse:
        snapshot = session.twin_state()
        return TwinStateResponse(
            rpm=float(snapshot["rpm"]),
            current=float(snapshot["current"]),
            voltage=float(snapshot["voltage"]),
            torque=float(snapshot["torque"]),
            temperature=float(snapshot["temperature"]),
            error=TwinErrorModel.model_validate(snapshot["error"]),
            parameters=TwinParametersModel.model_validate(snapshot["parameters"]),
            adaptation_status=str(snapshot["adaptation_status"]),
        )

    @app.get("/simulation/results", response_model=SimulationResultsResponse)
    def simulation_results() -> SimulationResultsResponse:
        frame = session.results()
        samples = [SimulationSample.model_validate(row) for row in frame.to_dict(orient="records")]
        return SimulationResultsResponse(running=session.running, samples=samples)

    @app.post("/simulation/start", response_model=SimulationStatusResponse)
    def simulation_start(request: SimulationStartRequest = SimulationStartRequest()) -> SimulationStatusResponse:
        session.start(
            t_end=request.t_end,
            dt=request.dt,
            voltage=request.voltage,
            load_torque=request.load_torque,
        )
        return SimulationStatusResponse(running=session.running, message="Simulation started.")

    @app.post("/simulation/stop", response_model=SimulationStatusResponse)
    def simulation_stop() -> SimulationStatusResponse:
        session.stop()
        return SimulationStatusResponse(running=session.running, message="Simulation stopped.")

    @app.post("/motor/control", response_model=MotorStateResponse)
    def motor_control(request: MotorControlRequest) -> MotorStateResponse:
        session.set_control(voltage=request.voltage, load_torque=request.load_torque)
        return MotorStateResponse.model_validate(asdict(session.motor_state()))

    @app.post("/twin/adapt", response_model=AdaptResponse)
    def twin_adapt(request: AdaptRequest = AdaptRequest()) -> AdaptResponse:
        result = session.adapt(free_params=request.free_params)
        return AdaptResponse(
            status=session.adaptation_status,
            rpm_rmse_before=result.before.rpm.rmse,
            rpm_rmse_after=result.after.rpm.rmse,
            current_rmse_before=result.before.current.rmse,
            current_rmse_after=result.after.current.rmse,
            initial_parameters=TwinParametersModel.model_validate(parameters_to_dict(result.initial_params)),
            estimated_parameters=TwinParametersModel.model_validate(
                parameters_to_dict(result.estimated_params)
            ),
            physical_parameters=TwinParametersModel.model_validate(
                parameters_to_dict(result.physical_params)
            ),
        )

    @app.websocket("/ws/simulation")
    async def simulation_ws(websocket: WebSocket, dt: float = 0.01, interval: float = 0.05) -> None:
        await stream_simulation(websocket, session, dt=dt, interval=interval)

    return app


app = create_app()
