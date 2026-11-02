"""Measure response times of the main screens against a running EduTrack.

    python -m scripts.measure_performance                     # http://127.0.0.1:8000
    python -m scripts.measure_performance --runs 30 --url http://127.0.0.1:8000

Each screen is requested several times as the role that uses it; the script prints
p50, p95 and max and fails (exit code 1) when a p95 goes over the 2 second target.
Run it against the large demo school (python -m scripts.seed_dev --size large).
"""

import argparse
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any

import httpx

TARGET_SECONDS = 2.0
PASSWORD = "Edutrack123!"
ROLES = {
    "director": "director@edutrack.dev",
    "teacher": "docente@edutrack.dev",
    "analyst": "analista@edutrack.dev",
    "parent": "padre@edutrack.dev",
}


@dataclass
class Result:
    name: str
    times: list[float]

    @property
    def p50(self) -> float:
        return statistics.median(self.times)

    @property
    def p95(self) -> float:
        ordered = sorted(self.times)
        return ordered[max(0, round(0.95 * len(ordered)) - 1)]


def login(client: httpx.Client, email: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def measure(
    client: httpx.Client, name: str, path: str, headers: dict[str, str], runs: int
) -> Result:
    client.get(path, headers=headers).raise_for_status()  # warm-up, not counted
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        client.get(path, headers=headers).raise_for_status()
        times.append(time.perf_counter() - start)
    return Result(name, times)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args()

    with httpx.Client(base_url=f"{args.url}/api/v1", timeout=30) as client:
        auth = {role: login(client, email) for role, email in ROLES.items()}

        def get(role: str, path: str) -> Any:
            response = client.get(path, headers=auth[role])
            response.raise_for_status()
            return response.json()

        period = [p for p in get("analyst", "/periods") if p["has_grades"]][-1]["id"]
        classroom = get("teacher", "/classrooms")[0]["id"]
        student = get("teacher", f"/classrooms/{classroom}/students")[0]["id"]
        child = get("parent", "/me/children")[0]["id"]
        students = sum(item["student_count"] for item in get("director", "/classrooms"))

        # First the whole school is assessed, so the screens show real data.
        start = time.perf_counter()
        client.post(
            "/risk-assessments/run",
            json={"period_id": period},
            headers=auth["analyst"],
            timeout=300,
        ).raise_for_status()
        assessment = time.perf_counter() - start

        screens = [
            ("Resumen del director", "director", f"/dashboard/summary?period_id={period}"),
            ("Aulas", "director", "/classrooms"),
            ("Estudiantes de un aula", "teacher", f"/classrooms/{classroom}/students"),
            ("Ficha del estudiante", "teacher", f"/students/{student}"),
            ("Resumen del bimestre", "teacher", f"/students/{student}/summary?period_id={period}"),
            ("Alertas", "teacher", "/alerts"),
            ("Recomendaciones", "director", "/recommendations"),
            ("Registro: mis cursos", "teacher", "/me/teaching"),
            ("Asistencia del día", "teacher", f"/classrooms/{classroom}/attendance"),
            ("Portal de padres", "parent", f"/students/{child}/summary"),
            ("Rendimiento del modelo", "director", "/model-performance"),
        ]
        results = [
            measure(client, name, path, auth[role], args.runs) for name, role, path in screens
        ]

    print(f"\nColegio con {students} estudiantes, {args.runs} mediciones por pantalla\n")
    print(f"{'Pantalla':<28}{'p50':>9}{'p95':>9}{'máx':>9}")
    slow = []
    for result in results:
        flag = "" if result.p95 <= TARGET_SECONDS else "  > 2 s"
        print(
            f"{result.name:<28}{result.p50 * 1000:>7.0f}ms{result.p95 * 1000:>7.0f}ms"
            f"{max(result.times) * 1000:>7.0f}ms{flag}"
        )
        if flag:
            slow.append(result.name)
    print(f"\nEvaluación de riesgo de todo el colegio: {assessment:.1f} s")

    if slow:
        print(f"\nSobre la meta de {TARGET_SECONDS:.0f} s: {', '.join(slow)}")
        return 1
    print(f"\nTodas las pantallas bajo {TARGET_SECONDS:.0f} s (p95).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
