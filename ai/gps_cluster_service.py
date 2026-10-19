
from collections import Counter

from database.db import get_grievances_with_gps
from ai.gps_clustering import cluster_grievances


def cluster_saved_grievances(eps_km=0.5, min_samples=2):
    grievances = get_grievances_with_gps()

    if not grievances:
        return []

    coordinates = [
        (item["latitude"], item["longitude"])
        for item in grievances
    ]

    labels = cluster_grievances(
        coordinates,
        eps_km=eps_km,
        min_samples=min_samples
    )

    results = []

    for grievance, cluster_id in zip(grievances, labels):
        results.append({
            "grievance_id": grievance["grievance_id"],
            "category": grievance["category"],
            "latitude": grievance["latitude"],
            "longitude": grievance["longitude"],
            "cluster_id": cluster_id
        })

    return results


def get_cluster_summary(eps_km=0.5, min_samples=2):
    results = cluster_saved_grievances(
        eps_km=eps_km,
        min_samples=min_samples
    )

    counts = Counter(
        item["cluster_id"]
        for item in results
        if item["cluster_id"] != -1
    )

    summary = []

    for cluster_id, count in sorted(counts.items()):
        cluster_grievances = [
            item for item in results
            if item["cluster_id"] == cluster_id
        ]

        categories = sorted({
            item["category"]
            for item in cluster_grievances
        })

        summary.append({
            "cluster_id": cluster_id,
            "grievance_count": count,
            "categories": categories,
            "grievance_ids": [
                item["grievance_id"]
                for item in cluster_grievances
            ]
        })

    return {
        "total_gps_grievances": len(results),
        "clusters_found": len(summary),
        "unclustered_grievances": sum(
            1 for item in results
            if item["cluster_id"] == -1
        ),
        "clusters": summary
    }
