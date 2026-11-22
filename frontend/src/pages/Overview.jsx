import {
  Satellite, Radio, AlertTriangle, Orbit, Activity,
  ShieldCheck, ArrowUpRight, Globe2,
} from "lucide-react";
import { useEffect, useState } from "react";

import Hero from "../components/Hero";
import "./Overview.css";

const fleetStatsTemplate = [
  {
    label: "TRACKED OBJECTS",
    value: "Awaiting data",
    description: "Satellite catalogue",
    icon: Satellite,
  },
  {
    label: "ACTIVE SATELLITES",
    value: "Awaiting data",
    description: "Operational spacecraft",
    icon: Radio,
  },
  {
    label: "ORBITAL DEBRIS",
    value: "Awaiting data",
    description: "Inactive objects and debris",
    icon: Orbit,
  },
  {
    label: "CLOSE APPROACHES",
    value: "Awaiting data",
    description: "Conjunction screening",
    icon: AlertTriangle,
  },
];

function Overview() {
  const [fleetStats, setFleetStats] = useState(fleetStatsTemplate);
  const [dataStatus, setDataStatus] = useState("DATA CONNECTION PENDING");

  useEffect(() => {
    const baseUrl = import.meta.env.VITE_ML_API_URL || "http://localhost:8001";
    fetch(`${baseUrl}/stats`)
      .then((response) => (response.ok ? response.json() : null))
      .then((stats) => {
        if (!stats) return;
        setDataStatus("ML TELEMETRY LIVE");
        setFleetStats([
          { ...fleetStatsTemplate[0], value: stats.tracked_satellites.toLocaleString() },
          {
            ...fleetStatsTemplate[1],
            value: (stats.satellites_by_object_type.PAYLOAD || 0).toLocaleString(),
          },
          {
            ...fleetStatsTemplate[2],
            value: (stats.satellites_by_object_type.DEBRIS ||
              stats.satellites_by_object_type.UNKNOWN || 0).toLocaleString(),
          },
          { ...fleetStatsTemplate[3], value: stats.conjunctions.toLocaleString() },
        ]);
      })
      .catch(() => setDataStatus("DATA CONNECTION PENDING"));
  }, []);

  return (
    <>
      <Hero />

      <section className="fleet-section" id="tracking">
        <div className="section-heading">
          <div>
            <p className="section-eyebrow">ORBITAL ENVIRONMENT</p>
            <h2>THE ORBITAL LANDSCAPE</h2>
            <p className="section-description">
              A unified overview of Earth's satellite environment.
            </p>
          </div>

          <div className="section-status">
            <span className="status-indicator"></span>
            {dataStatus}
          </div>
        </div>

        <div className="fleet-grid">
          {fleetStats.map((stat) => {
            const Icon = stat.icon;

            return (
              <article className="fleet-card" key={stat.label}>
                <div className="fleet-card-top">
                  <span>{stat.label}</span>
                  <Icon size={20} />
                </div>

                <h3>{stat.value}</h3>
                <p>{stat.description}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="intelligence-section" id="intelligence">
        <div className="intelligence-heading">
          <div>
            <p className="section-eyebrow">MISSION CONTROL</p>
            <h2>ORBITAL INTELLIGENCE</h2>
          </div>
          <Activity size={22} />
        </div>

        <div className="intelligence-grid">
          <article className="intelligence-card">
            <div className="intelligence-icon">
              <Globe2 size={22} />
            </div>
            <h3>Satellite Tracking</h3>
            <p>
              Monitor satellite positions and orbital movement using
              orbital catalogue data.
            </p>
            <span className="feature-status">IN DEVELOPMENT</span>
          </article>

          <article className="intelligence-card">
            <div className="intelligence-icon">
              <ShieldCheck size={22} />
            </div>
            <h3>Orbital Sustainability</h3>
            <p>
              Understand orbital congestion and support responsible
              space operations.
            </p>
            <span className="feature-status">IN DEVELOPMENT</span>
          </article>

          <article className="intelligence-card">
            <div className="intelligence-icon">
              <AlertTriangle size={22} />
            </div>
            <h3>Conjunction Monitoring</h3>
            <p>
              Identify potentially hazardous close approaches between
              tracked objects.
            </p>
            <span className="feature-status">IN DEVELOPMENT</span>
          </article>
        </div>
      </section>

      <section className="mission-banner">
        <div>
          <p className="section-eyebrow">OUR MISSION</p>
          <h2>A SAFER FUTURE IN SPACE.</h2>
          <p>
            Bringing orbital intelligence together to help protect
            Earth's increasingly valuable space environment.
          </p>
        </div>

        <div className="mission-symbol">
          <Orbit size={58} strokeWidth={1} />
        </div>

        <ArrowUpRight className="mission-arrow" size={22} />
      </section>

      <footer className="nexorbit-footer">
        <span>NEXORBIT © 2026</span>
        <span>
          SPACE TRAFFIC INTELLIGENCE & ORBITAL SUSTAINABILITY
        </span>
      </footer>
    </>
  );
}

export default Overview;
