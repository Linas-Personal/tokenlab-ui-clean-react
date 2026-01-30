"""
Locust load testing suite for TokenLab ABM API

Run with:
    locust -f load-tests/locustfile.py --host=http://localhost:8000

For headless mode (100 users, 10/sec spawn rate, 5 min duration):
    locust -f load-tests/locustfile.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 5m --headless
"""

from locust import HttpUser, task, between
import json
import random

class ABMSimulationUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a user starts"""
        self.check_health()

    def check_health(self):
        """Verify backend is healthy"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Health check failed: {response.status_code}")

    @task(3)
    def submit_simple_simulation(self):
        """Submit a simple ABM simulation (most common scenario)"""
        config = {
            "token": {
                "name": f"LoadTest_{random.randint(1000, 9999)}",
                "total_supply": 1_000_000,
                "start_date": "2026-01-01",
                "horizon_months": 12
            },
            "buckets": [
                {
                    "bucket": "Team",
                    "allocation": 30,
                    "tge_unlock_pct": 0,
                    "cliff_months": 6,
                    "vesting_months": 18
                },
                {
                    "bucket": "Investors",
                    "allocation": 40,
                    "tge_unlock_pct": 10,
                    "cliff_months": 3,
                    "vesting_months": 12
                },
                {
                    "bucket": "Community",
                    "allocation": 30,
                    "tge_unlock_pct": 20,
                    "cliff_months": 0,
                    "vesting_months": 6
                }
            ],
            "abm": {
                "pricing_model": "constant",
                "agent_granularity": "meta_agents",
                "agents_per_cohort": 50,
                "initial_price": 1.0,
                "constant_price": 1.0
            }
        }

        with self.client.post(
            "/api/v2/abm/simulate",
            json=config,
            name="/api/v2/abm/simulate (simple)",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                if job_id:
                    response.success()
                    # Poll for completion
                    self.poll_job_status(job_id)
                else:
                    response.failure("No job_id in response")
            else:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def submit_complex_simulation(self):
        """Submit a complex ABM simulation with staking and Monte Carlo"""
        config = {
            "token": {
                "name": f"ComplexTest_{random.randint(1000, 9999)}",
                "total_supply": 10_000_000,
                "start_date": "2026-01-01",
                "horizon_months": 24
            },
            "buckets": [
                {
                    "bucket": "Team",
                    "allocation": 20,
                    "tge_unlock_pct": 0,
                    "cliff_months": 12,
                    "vesting_months": 24
                },
                {
                    "bucket": "Investors",
                    "allocation": 30,
                    "tge_unlock_pct": 5,
                    "cliff_months": 6,
                    "vesting_months": 18
                },
                {
                    "bucket": "Community",
                    "allocation": 25,
                    "tge_unlock_pct": 15,
                    "cliff_months": 0,
                    "vesting_months": 12
                },
                {
                    "bucket": "Reserve",
                    "allocation": 25,
                    "tge_unlock_pct": 0,
                    "cliff_months": 12,
                    "vesting_months": 36
                }
            ],
            "abm": {
                "pricing_model": "eoe",
                "agent_granularity": "meta_agents",
                "agents_per_cohort": 100,
                "initial_price": 1.0,
                "eoe_velocity": 2.0,
                "eoe_smoothing_factor": 0.3,
                "staking_enabled": True,
                "staking_apy": 0.12,
                "staking_max_capacity_pct": 40,
                "treasury_enabled": True,
                "treasury_tx_fee_pct": 0.5,
                "treasury_buyback_pct": 60,
                "treasury_burn_pct": 40
            },
            "monte_carlo": {
                "enabled": True,
                "num_trials": 10,
                "seed": random.randint(1, 100000)
            }
        }

        with self.client.post(
            "/api/v2/abm/simulate",
            json=config,
            name="/api/v2/abm/simulate (complex)",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                if job_id:
                    response.success()
                else:
                    response.failure("No job_id in response")
            else:
                response.failure(f"Status {response.status_code}")

    @task(2)
    def check_job_status(self):
        """Check status of a random job (simulates monitoring)"""
        # Simulate checking a job ID
        job_id = f"test_job_{random.randint(1, 100)}"
        with self.client.get(
            f"/api/v2/abm/jobs/{job_id}/status",
            name="/api/v2/abm/jobs/[id]/status",
            catch_response=True
        ) as response:
            # 404 is expected for non-existent jobs
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(1)
    def list_jobs(self):
        """List all jobs"""
        with self.client.get(
            "/api/v2/abm/jobs",
            name="/api/v2/abm/jobs",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def get_queue_stats(self):
        """Get queue statistics"""
        with self.client.get(
            "/api/v2/abm/queue/stats",
            name="/api/v2/abm/queue/stats",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    def poll_job_status(self, job_id, max_polls=5):
        """Poll job status until completion or max polls"""
        for _ in range(max_polls):
            with self.client.get(
                f"/api/v2/abm/jobs/{job_id}/status",
                name="/api/v2/abm/jobs/[id]/status (poll)",
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    if status in ["completed", "failed"]:
                        response.success()
                        return
                    response.success()
                else:
                    response.failure(f"Status {response.status_code}")
                    return

class ValidationErrorUser(HttpUser):
    """User that submits invalid configurations to test error handling"""
    wait_time = between(2, 5)

    @task
    def submit_invalid_allocation(self):
        """Submit config with allocation > 100%"""
        config = {
            "token": {
                "name": "InvalidTest",
                "total_supply": 1_000_000,
                "start_date": "2026-01-01",
                "horizon_months": 12
            },
            "buckets": [
                {
                    "bucket": "Team",
                    "allocation": 60,
                    "tge_unlock_pct": 0,
                    "cliff_months": 0,
                    "vesting_months": 12
                },
                {
                    "bucket": "Community",
                    "allocation": 60,
                    "tge_unlock_pct": 20,
                    "cliff_months": 0,
                    "vesting_months": 6
                }
            ],
            "abm": {
                "pricing_model": "constant",
                "agent_granularity": "meta_agents",
                "agents_per_cohort": 50,
                "initial_price": 1.0,
                "constant_price": 1.0
            }
        }

        with self.client.post(
            "/api/v2/abm/simulate",
            json=config,
            name="/api/v2/abm/simulate (validation error)",
            catch_response=True
        ) as response:
            if response.status_code == 422:
                response.success()  # Expected validation error
            elif response.status_code == 200:
                response.failure("Validation should have failed!")
            else:
                response.failure(f"Unexpected status {response.status_code}")
