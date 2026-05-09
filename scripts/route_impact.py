"""
Recalculate hospital route impact from active disaster alerts.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.relief.hospital_network import HospitalNetworkService


def print_impact_summary(service: HospitalNetworkService):
    routes = service.get_routes(recalculate=False)
    blocked = [route for route in routes if route.get("blocked")]
    affected = [route for route in routes if route.get("danger_level", 0) > 0]

    print("\n=== Route Impact Summary ===")
    print(f"Total routes: {len(routes)}")
    print(f"Affected routes: {len(affected)}")
    print(f"Blocked routes: {len(blocked)}")
    if routes:
        print(f"Percentage blocked: {(len(blocked) / len(routes)) * 100:.1f}%")

    by_type = {}
    for route in affected:
        for alert in route.get("affected_by", []):
            disaster_type = alert.get("disaster_type", "unknown")
            by_type[disaster_type] = by_type.get(disaster_type, 0) + 1

    if by_type:
        print("\nAffected route touches by disaster type:")
        for disaster_type, count in sorted(by_type.items()):
            print(f"  {disaster_type}: {count}")

    print("\nTop 5 highest-risk routes:")
    for route in sorted(affected, key=lambda item: item.get("danger_level", 0), reverse=True)[:5]:
        print(
            f"  {route['source_id']} -> {route['target_id']}: "
            f"danger={route['danger_level']:.2f}, blocked={route['blocked']}"
        )


if __name__ == "__main__":
    service = HospitalNetworkService()
    summary = service.refresh()
    print(f"Active alerts: {summary['active_alerts']}")
    print_impact_summary(service)
