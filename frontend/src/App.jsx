
import {
  LayoutDashboard,
  Globe2,
  Satellite,
  Radio,
  AlertTriangle,
  BarChart3,
  Settings,
  Search,
  Bell,
  Activity,
  Orbit,
  ShieldCheck,
  Menu
} from "lucide-react";

import "./App.css";

const stats = [
  {
    title: "Tracked Objects",
    value: "0",
    detail: "Awaiting orbital data",
    icon: Satellite,
  },
  {
    title: "Active Satellites",
    value: "0",
    detail: "Awaiting orbital data",
    icon: Radio,
  },
  {
    title: "Space Debris",
    value: "0",
    detail: "Awaiting orbital data",
    icon: AlertTriangle,
  },
  {
    title: "Close Approaches",
    value: "0",
    detail: "No events loaded",
    icon: Activity,
  },
];

const navigation = [
  { name: "Overview", icon: LayoutDashboard },
  { name: "Satellite Tracking", icon: Satellite },
  { name: "Orbital Visualisation", icon: Globe2 },
  { name: "Conjunction Alerts", icon: AlertTriangle },
  { name: "Analytics", icon: BarChart3 },
];

function App() {
  return (
    <div className="app-container">

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Orbit size={25} />
          </div>
          <div>
            <h2>NEXORBIT</h2>
            <span>SPACE INTELLIGENCE</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <nav className="navigation">
          {navigation.map((item, index) => {
            const Icon = item.icon;

            return (
              <div
                className={`nav-item ${index === 0 ? "active" : ""}`}
                key={item.name}
              >
                <Icon size={19} />
                <span>{item.name}</span>
              </div>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="nav-item">
            <Settings size={19} />
            <span>Settings</span>
          </div>

          <div className="system-status">
            <span className="status-dot"></span>
            SYSTEM INITIALIZED
          </div>
        </div>
      </aside>

      <main className="main-content">

        <header className="topbar">
          <div className="page-heading">
            <button className="mobile-menu">
              <Menu size={22} />
            </button>
            <div>
              <p>SPACE TRAFFIC INTELLIGENCE</p>
              <h1>Mission Overview</h1>
            </div>
          </div>

          <div className="topbar-actions">
            <div className="search-box">
              <Search size={17} />
              <span>Search objects...</span>
            </div>

            <button className="icon-button">
              <Bell size={19} />
            </button>

            <div className="profile">
              <div className="profile-avatar">N</div>
              <span>Analyst</span>
            </div>
          </div>
        </header>

        <section className="welcome-section">
          <div>
            <p className="eyebrow">ORBITAL INTELLIGENCE PLATFORM</p>
            <h2>Monitor Space. Protect Orbits.</h2>
            <p className="welcome-description">
              Unified satellite tracking, orbital analysis and
              space sustainability monitoring.
            </p>
          </div>

          <div className="system-badge">
            <ShieldCheck size={17} />
            Intelligence System
          </div>
        </section>

        <section className="stats-grid">
          {stats.map((stat) => {
            const Icon = stat.icon;

            return (
              <div className="stat-card" key={stat.title}>
                <div className="stat-top">
                  <span>{stat.title}</span>
                  <div className="stat-icon">
                    <Icon size={20} />
                  </div>
                </div>

                <h2>{stat.value}</h2>
                <p>{stat.detail}</p>
              </div>
            );
          })}
        </section>

        <section className="dashboard-grid">

          <div className="panel globe-panel">
            <div className="panel-heading">
              <div>
                <h3>Orbital Visualisation</h3>
                <p>Interactive Earth and satellite monitoring</p>
              </div>
              <span className="live-label">● INITIALISING</span>
            </div>

            <div className="globe-placeholder">
              <div className="globe-orbit orbit-one"></div>
              <div className="globe-orbit orbit-two"></div>
              <div className="globe">
                <Globe2 size={105} strokeWidth={0.8} />
              </div>

              <div className="globe-caption">
                <Orbit size={15} />
                3D ORBITAL VIEW WILL APPEAR HERE
              </div>
            </div>
          </div>

          <div className="panel alerts-panel">
            <div className="panel-heading">
              <div>
                <h3>Conjunction Alerts</h3>
                <p>Potential close-approach events</p>
              </div>
              <AlertTriangle size={20} className="alert-icon" />
            </div>

            <div className="empty-state">
              <div className="empty-icon">
                <ShieldCheck size={28} />
              </div>
              <h4>No events loaded</h4>
              <p>
                Connect orbital datasets to monitor
                potentially hazardous close approaches.
              </p>
            </div>
          </div>

          <div className="panel activity-panel">
            <div className="panel-heading">
              <div>
                <h3>Orbital Intelligence</h3>
                <p>Platform capabilities</p>
              </div>
              <Activity size={20} />
            </div>

            <div className="capability-list">
              <div>
                <Satellite size={19} />
                <span>Satellite tracking</span>
                <span className="capability-status">READY</span>
              </div>
              <div>
                <Orbit size={19} />
                <span>Orbital propagation</span>
                <span className="capability-status pending">PENDING</span>
              </div>
              <div>
                <BarChart3 size={19} />
                <span>AI risk analysis</span>
                <span className="capability-status pending">PENDING</span>
              </div>
            </div>
          </div>

          <div className="panel data-panel">
            <div className="panel-heading">
              <div>
                <h3>Data Sources</h3>
                <p>Orbital intelligence feeds</p>
              </div>
              <Globe2 size={20} />
            </div>

            <div className="data-source">
              <span>CELESTRAK</span>
              <span className="source-status">NOT CONNECTED</span>
            </div>
            <div className="data-source">
              <span>SOCRATES</span>
              <span className="source-status">NOT CONNECTED</span>
            </div>
          </div>

        </section>

        <footer>
          NEXORBIT © 2026 · AI-POWERED SPACE TRAFFIC INTELLIGENCE
        </footer>

      </main>
    </div>
  );
}

export default App;