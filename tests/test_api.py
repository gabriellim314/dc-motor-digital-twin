"""Basic FastAPI tests for the MotorTwin backend."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from api.app import create_app
from api.service import MotorTwinService


LIVE_KEYS = (
    "timestamp",
    "physical_rpm",
    "twin_rpm",
    "physical_current",
    "twin_current",
    "voltage",
    "torque",
    "load_torque",
    "temperature",
    "rpm_error",
    "current_error",
    "twin_accuracy",
)


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MotorTwinService()
        self.client = TestClient(create_app(self.service))

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_motor_state_at_rest(self) -> None:
        response = self.client.get("/motor/state")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["rpm"], 0.0)
        self.assertEqual(body["current"], 0.0)
        self.assertIn("temperature", body)
        self.assertIn("torque", body)

    def test_twin_state_exposes_parameters_and_error(self) -> None:
        response = self.client.get("/twin/state")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("parameters", body)
        self.assertIn("error", body)
        self.assertEqual(body["adaptation_status"], "idle")
        self.assertEqual(body["parameters"]["R"], 2.0)

    def test_start_and_results(self) -> None:
        started = self.client.post(
            "/simulation/start",
            json={"t_end": 0.4, "dt": 0.02, "voltage": 12.0, "load_torque": 0.05},
        )
        self.assertEqual(started.status_code, 200)
        self.assertTrue(started.json()["running"])

        results = self.client.get("/simulation/results")
        self.assertEqual(results.status_code, 200)
        samples = results.json()["samples"]
        self.assertGreater(len(samples), 1)
        self.assertIn("physical_rpm", samples[-1])
        self.assertIn("twin_rpm", samples[-1])
        self.assertIn("rpm_error", samples[-1])

        motor = self.client.get("/motor/state").json()
        self.assertGreater(motor["rpm"], 0.0)

    def test_control_and_stop(self) -> None:
        control = self.client.post("/motor/control", json={"voltage": 8.0, "load_torque": 0.02})
        self.assertEqual(control.status_code, 200)
        self.assertEqual(control.json()["voltage"], 8.0)

        self.client.post("/simulation/start", json={"t_end": 0.2, "dt": 0.02})
        stopped = self.client.post("/simulation/stop")
        self.assertEqual(stopped.status_code, 200)
        self.assertFalse(stopped.json()["running"])
        self.assertFalse(self.client.get("/simulation/results").json()["running"])

    def test_adapt_updates_status_and_reduces_error(self) -> None:
        self.client.post("/simulation/start", json={"t_end": 1.2, "dt": 0.02})
        adapted = self.client.post("/twin/adapt", json={"free_params": ["J", "b", "R"]})
        self.assertEqual(adapted.status_code, 200)
        body = adapted.json()
        self.assertEqual(body["status"], "completed")
        self.assertLess(body["rpm_rmse_after"], body["rpm_rmse_before"])
        self.assertAlmostEqual(body["estimated_parameters"]["Kt"], 0.05)
        self.assertAlmostEqual(body["estimated_parameters"]["Ke"], 0.05)

        twin = self.client.get("/twin/state").json()
        self.assertEqual(twin["adaptation_status"], "completed")

    def test_websocket_streams_live_state(self) -> None:
        with self.client.websocket_connect("/ws/simulation?dt=0.01&interval=0.01") as websocket:
            frame = websocket.receive_json()
            for key in LIVE_KEYS:
                self.assertIn(key, frame)
            self.assertGreater(frame["timestamp"], 0.0)
            self.assertGreaterEqual(frame["twin_accuracy"], 0.0)
            self.assertLessEqual(frame["twin_accuracy"], 1.0)
            self.client.post("/simulation/stop")
            status = None
            for _ in range(20):
                payload = websocket.receive_json()
                if payload.get("status") == "stopped":
                    status = payload
                    break
            self.assertEqual(status, {"status": "stopped"})
        self.assertFalse(self.service.running)

    def test_websocket_disconnect_stops_simulation(self) -> None:
        with self.client.websocket_connect("/ws/simulation?dt=0.01&interval=0.01") as websocket:
            websocket.receive_json()
            self.assertTrue(self.service.running)
        self.assertFalse(self.service.running)

    def test_websocket_rejects_invalid_timestep(self) -> None:
        with self.client.websocket_connect("/ws/simulation?dt=0&interval=0.01") as websocket:
            payload = websocket.receive_json()
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["detail"], "invalid state")

    def test_adapt_without_prior_start(self) -> None:
        adapted = self.client.post("/twin/adapt", json={"free_params": ["J", "b", "R"]})
        self.assertEqual(adapted.status_code, 200)
        body = adapted.json()
        self.assertEqual(body["status"], "completed")
        self.assertLess(body["rpm_rmse_after"], body["rpm_rmse_before"])
        self.assertFalse(self.service.live)
        self.assertEqual(self.service.physical.state.current, 0.0)
        self.assertEqual(self.service.physical.state.omega, 0.0)

    def test_live_results_and_twin_error(self) -> None:
        self.service.begin_live()
        last = None
        for _ in range(12):
            last = self.service.step_live(0.01)
        self.assertIsNotNone(last)
        results = self.client.get("/simulation/results")
        self.assertEqual(results.status_code, 200)
        samples = results.json()["samples"]
        self.assertGreaterEqual(len(samples), 12)
        self.assertIn("current_error", samples[-1])

        twin = self.client.get("/twin/state").json()
        self.assertAlmostEqual(twin["rpm"], last["twin_rpm"])
        self.assertNotEqual(twin["error"]["rpm_error"], 0.0)

    def test_live_control_updates_next_frame(self) -> None:
        self.service.begin_live()
        first = self.service.step_live(0.01)
        self.assertIsNotNone(first)
        self.assertEqual(first["voltage"], 12.0)
        self.service.set_control(8.0, 0.02)
        frame = self.service.step_live(0.01)
        self.assertIsNotNone(frame)
        self.assertEqual(frame["voltage"], 8.0)
        self.assertEqual(frame["load_torque"], 0.02)

    def test_live_adapt_preserves_session_and_updates_parameters(self) -> None:
        self.service.begin_live()
        self.service.set_control(12.0, 0.05)
        for _ in range(25):
            self.service.step_live(0.01)

        time_before = self.service.time
        physical_before = self.service.physical.state
        params_before = self.service.twin.params
        self.assertTrue(self.service.live)

        result = self.service.adapt()
        self.assertLess(result.after.rpm.rmse, result.before.rpm.rmse)
        self.assertTrue(self.service.live)
        self.assertTrue(self.service.running)
        self.assertAlmostEqual(self.service.time, time_before)
        self.assertAlmostEqual(self.service.physical.state.omega, physical_before.omega)
        self.assertAlmostEqual(self.service.physical.state.current, physical_before.current)
        self.assertNotEqual(self.service.twin.params.J, params_before.J)

        frame = self.service.step_live(0.01)
        self.assertIsNotNone(frame)
        self.assertGreater(frame["timestamp"], time_before)

    def test_live_error_drops_after_adaptation(self) -> None:
        self.service.begin_live()
        self.service.set_control(12.0, 0.05)
        before = []
        for _ in range(60):
            frame = self.service.step_live(0.01)
            before.append(abs(frame["rpm_error"]))

        result = self.service.adapt()
        self.assertLess(result.after.rpm.rmse, result.before.rpm.rmse)

        after = []
        for _ in range(60):
            frame = self.service.step_live(0.01)
            after.append(abs(frame["rpm_error"]))

        self.assertLess(sum(after[-15:]) / 15, sum(before[-15:]) / 15)


if __name__ == "__main__":
    unittest.main()
