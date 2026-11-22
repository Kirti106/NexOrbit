
import {
  Orbit,
  LayoutDashboard,
  Satellite,
  Globe2,
  AlertTriangle,
  BarChart3,
  Search,
  Bell,
  ChevronDown,
} from "lucide-react";

import { NavLink } from "react-router-dom";
import "./Navbar.css";

const navItems = [
  { label: "Overview", path: "/", icon: LayoutDashboard },
  { label: "Tracking", path: "/tracking", icon: Satellite },
  { label: "Orbit Map", path: "/orbit-map", icon: Globe2 },
  { label: "Alerts", path: "/alerts", icon: AlertTriangle },
  { label: "Analytics", path: "/analytics", icon: BarChart3 },
];

function Navbar() {
  return (
    <header className="nova-navbar">
      <NavLink to="/" className="nova-brand">
        <Orbit size={27} strokeWidth={1.5} />
        <span>NEXORBIT</span>
      </NavLink>

      <nav className="nova-navigation">
        {navItems.map((item) => {
          return (
            <NavLink
              to={item.path}
              key={item.label}
              end={item.path === "/"}
              className={({ isActive }) =>
                isActive ? "nav-link selected" : "nav-link"
              }
            >
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      <div className="navbar-actions">
        <button aria-label="Search">
          <Search size={18} />
        </button>

        <button aria-label="Notifications">
          <Bell size={18} />
        </button>

        <button className="user-profile">
          <span className="avatar">N</span>
          <span>Analyst</span>
          <ChevronDown size={14} />
        </button>
      </div>
    </header>
  );
}

export default Navbar;
