import {
  Satellite, Radio, AlertTriangle, Orbit, Activity,
  ShieldCheck, ArrowUpRight, Globe2,
} from "lucide-react";

import Hero from "../components/Hero";
import { ApiError } from "../components/ApiState";
import { useApi } from "../hooks/useApi";
import { getStats } from "../api/client";
import { fmtInt, fmtUtc } from "../utils/format";
import "./Overview.css";

function buildFleetStats(stats) {
  const types = stats?.satellites_by_object_type || {};
  const value = (n) => (stats ? fmtInt(n) : "Loading...");
  return [
    {
      label: "TRACKED OBJECTS",
      value: value(stats?.tracked_satellites),
      description: "Objects in the satellite catalogue",
      icon: Satellite,
    },
    {
      label: "PAYLOADS",
      value: value(types.PAYLOAD),
      description: "Catalogued payloads (not all operational)",
      icon: Radio,
    },
    {
      label: "DEBRIS & ROCKET BODIES",
      value: value((types.DEBRIS || 0) + (types["ROCKET BODY"] || 0)),
      description: "Classified debris and rocket bodies",
      icon: Orbit,
    },
    {
      label: "HIGH-TIER CLOSE APPROACHES",
      value: value(stats?.high_risk_conjunctions),
      description: "Predicted (SOCRATES-derived), not observed",
      icon: AlertTriangle,
    },
  ];
}

function Overview() {
  const { data: stats, error } = useApi(getStats, [], { intervalMs: 60000 });
  const fleetStats = buildFleetStats(stats);

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
            {stats
              ? `LIVE · ELEMENTS AS OF ${fmtUtc(stats.gp_freshest_at).toUpperCase()}`
              : error
                ? "BACKEND OFFLINE"
                : "CONNECTING..."}
          </div>
        </div>

        <ApiError message={error} title="Could not load catalogue statistics" />

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
            <span className="feature-status">LIVE</span>
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
            <span className="feature-status">LIVE</span>
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
