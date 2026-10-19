
import numpy as np
from sklearn.cluster import DBSCAN


def cluster_grievances(coordinates, eps_km=0.5, min_samples=2):
    """
    Group grievances reported near one another using GPS coordinates.

    coordinates: list of (latitude, longitude) pairs
    eps_km: maximum neighborhood radius in kilometers
    min_samples: minimum points needed to form a cluster
    """

    if not coordinates:
        return []

    points = np.asarray(coordinates, dtype=float)

    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError(
            "Coordinates must contain latitude-longitude pairs."
        )

    if not np.isfinite(points).all():
        raise ValueError("Coordinates must be finite numbers.")

    if (
        (points[:, 0] < -90).any()
        or (points[:, 0] > 90).any()
        or (points[:, 1] < -180).any()
        or (points[:, 1] > 180).any()
    ):
        raise ValueError("Latitude or longitude is out of range.")

    if eps_km <= 0 or min_samples < 1:
        raise ValueError("eps_km must be positive and min_samples at least 1.")

    # DBSCAN with the haversine metric expects coordinates in radians.
    points_radians = np.radians(points)

    model = DBSCAN(
        eps=eps_km / 6371.0088,
        min_samples=min_samples,
        metric="haversine"
    )

    return model.fit_predict(points_radians).tolist()
