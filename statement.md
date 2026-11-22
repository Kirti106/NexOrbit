# NexOrbit: Project Statement

**Space traffic intelligence and orbital sustainability platform**

## 1. Problem

Earth orbit is getting crowded. Thousands of active satellites share space with debris and spent rocket bodies, and the number of objects keeps growing. Operators, researchers and students who want to understand this environment must pull data from several separate sources, in different formats, and interpret it themselves. There is no single, easy view that combines where objects are, which ones may pass close to each other, and how crowded each orbit is becoming.

## 2. Objective

NexOrbit is an integrated platform that brings these views together in one dashboard:

- **Satellite tracking:** locate and inspect catalogued objects, with positions computed from orbital elements.
- **Orbital analysis:** screen predicted close approaches (conjunctions) and rank them by risk tier.
- **AI-based intelligence:** flag objects with unusual orbit profiles and group objects by orbital regime.
- **Sustainability simulation:** project debris growth and compare simple scenarios (planned).

## 3. Scope

| Area | Status |
|---|---|
| CelesTrak GP elements and SATCAT catalogue ingestion | Done |
| SOCRATES conjunction ingestion and risk tiers | Done |
| SGP4 propagation, live positions, 3-hour ground tracks | Done |
| Cross-sectional anomaly scoring ("unusual orbit profile") | Done |
| Backend API and React + Cesium dashboard | Done, wired to live data |
| Clustering, object classification, debris forecast | Code written, not yet exposed in the API or dashboard |
| Maneuver detection from element history | Not started: needs at least two element snapshots per object |
| ISRO sources (Bhoonidhi, VEDAS, Bhuvan) | Deferred: interfaces stubbed, authentication and formats not yet confirmed |

## 4. Approach

**Data.** CelesTrak provides current orbital elements and the object catalogue. SOCRATES provides predicted close approaches for the next several days. Both are stored in PostgreSQL with PostGIS.

**Architecture.**

```
React + Cesium dashboard  ->  FastAPI backend  ->  FastAPI ML service  ->  PostgreSQL / PostGIS
```

The backend proxies the ML service, so every response keeps its model version, generation time, risk tier and basis label.

**Methods.**

- Positions: SGP4 propagation, converted to latitude, longitude and altitude with Skyfield.
- Conjunction risk: low, medium and high tiers derived from SOCRATES range and maximum probability. Same-constellation near-zero-range events are flagged as artifacts and excluded by default.
- Anomalies: robust (median and MAD) outlier scores on mean motion, eccentricity, inclination and drag term within one snapshot.
- Evaluation rules: time-based train and test splits only, and no use of the label source as a feature.

## 5. Honest limitations

- Orbital elements go stale within days, so positions are estimates, not precise tracking.
- SOCRATES results are **predictions**. The probability field is a maximum-probability estimate, not an observed or real collision probability, so the platform shows risk tiers first and the probability only as secondary detail.
- Anomaly scores describe unusual element profiles in a single snapshot. They do not indicate maneuvers or failures.
- The loaded catalogue currently classifies most objects as payload or unknown, so debris statistics are incomplete until debris groups are ingested and classified.
- The sustainability model, once exposed, will be a simplified scenario model, not a physics-based Kessler cascade simulation.

## 6. Expected outcome

A working dashboard where a user can search the catalogue, watch objects move on a 3D globe, inspect upcoming predicted close approaches by risk tier, and see how the catalogue is distributed by object type and orbit regime. All figures are labelled with their data source and time of generation.

## 7. Next steps

1. Take a second CelesTrak snapshot at least two hours after the first, to enable element-history anomaly detection.
2. Schedule ingestion: GP elements every 2 hours, SOCRATES daily.
3. Expose clustering, classification and debris-forecast endpoints and add them to the Analytics page.
4. Confirm access and formats for Bhoonidhi, VEDAS and Bhuvan before implementing their adapters.

## 8. Data sources and attribution

- CelesTrak (GP element sets, SATCAT, SOCRATES): https://celestrak.org
- ISRO portals (Bhoonidhi, VEDAS, Bhuvan): planned, subject to registration and usage terms.
