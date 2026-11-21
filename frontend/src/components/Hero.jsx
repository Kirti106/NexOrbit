import "./Hero.css";
import { ArrowUpRight, Globe2, ShieldCheck } from "lucide-react";
import OrbitalGlobe from "./OrbitalGlobe";

function Hero() {
  return (
    <section className="hero-section">

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
      </div>

    </section>
  );
}

export default Hero;
