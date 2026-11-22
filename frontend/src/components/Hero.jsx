import "./Hero.css";
import { ArrowUpRight, Globe2, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import OrbitalGlobe from "./OrbitalGlobe";

function Hero() {
  const [stats, setStats] = useState(null);
  const [live, setLive] = useState([]);

  useEffect(() => {
    const baseUrl = import.meta.env.VITE_ML_API_URL || "http://localhost:8001";
    Promise.allSettled([
      fetch(`${baseUrl}/stats`).then((response) => response.ok ? response.json() : null),
      fetch(`${baseUrl}/satellites/live?limit=3`).then((response) => response.ok ? response.json() : null),
    ]).then(([statsResult, liveResult]) => {
      if (statsResult.status === "fulfilled" && statsResult.value) {
        setStats(statsResult.value);
      }
      if (liveResult.status === "fulfilled" && liveResult.value) {
        setLive(liveResult.value.items || []);
      }
    });
  }, []);

  return (
    <section className="hero-section">
      <div className="hero-grid-overlay"></div>

      <div className="hero-content">
        <div className="hero-status">
          <span className="status-indicator"></span>
          ORBITAL INTELLIGENCE SYSTEM
          <span className="nominal">NOMINAL</span>
        </div>

        <p className="hero-eyebrow">SPACE TRAFFIC INTELLIGENCE</p>

        <h1>
          MONITOR.
          <br />
          TRACK.
          <br />
          <span>PROTECT.</span>
        </h1>

        <p className="hero-description">
          Navigate Earth's orbital environment, monitor satellite
          activity and support a safer, more sustainable space future.
        </p>

        <div className="hero-buttons">
          <a href="#tracking" className="primary-hero-button">
            EXPLORE ORBITS
            <ArrowUpRight size={17} />
          </a>

          <a href="#intelligence" className="secondary-hero-button">
            <Globe2 size={17} />
            VIEW INTELLIGENCE
          </a>
        </div>

        <div className="hero-trust">
          <ShieldCheck size={16} />
          SPACE SITUATIONAL AWARENESS PLATFORM
        </div>
      </div>

      <div className="hero-globe-area">
        <div className="globe-glow"></div>

        <div className="hero-globe">
          <OrbitalGlobe />
        </div>

        <div className="orbit-label">
          <span className="label-dot"></span>
          EARTH ORBIT
        </div>

        <div className="hero-coordinate">
          ORBITAL VIEW <br />
          <span>3D VISUALISATION</span>
        </div>

        {live.length > 0 && (
          <div className="hero-live-stack">
            <p>LIVE PROPAGATION</p>
            {live.map((item) => (
              <div className="hero-live-row" key={item.norad_id}>
                <span>{item.name}</span>
                <strong>{item.altitude_km.toFixed(0)} km</strong>
              </div>
            ))}
          </div>
        )}
      </div>

      {stats && (
        <div className="hero-console-strip">
          <div>
            <span>TRACKED</span>
            <strong>{stats.tracked_satellites.toLocaleString()}</strong>
          </div>
          <div>
            <span>CONJUNCTIONS</span>
            <strong>{stats.conjunctions.toLocaleString()}</strong>
          </div>
          <div>
            <span>HIGH RISK</span>
            <strong>{stats.high_risk_conjunctions.toLocaleString()}</strong>
          </div>
        </div>
      )}

    </section>
  );
}

export default Hero;
