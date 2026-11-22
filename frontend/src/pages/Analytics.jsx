import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";
import {
  Activity,
  Satellite,
  Orbit,
  AlertTriangle,
  TrendingUp,
} from "lucide-react";

import { getAnalytics } from "../api/client";
import "./Analytics.css";

const colors = { LEO: "#65b9ff", MEO: "#b794f6", GEO: "#ffca72" };
const periods = ["7D", "30D", "90D", "1Y"];

function Analytics() {
  const [period, setPeriod] = useState("30D");
  const [result, setResult] = useState({ period: null, data: null, error: "" });

  useEffect(() => {
    const controller = new AbortController();
    getAnalytics(period, { signal: controller.signal })
      .then((response) => setResult({ period, data: response, error: "" }))
      .catch((requestError) => {
        if (requestError.name !== "AbortError") {
          setResult({ period, data: null, error: requestError.message });
        }
      });
    return () => controller.abort();
  }, [period]);

  const data = result.period === period ? result.data : null;
  const error = result.period === period ? result.error : "";
  const orbitData = useMemo(
    () => Object.entries(data?.satellites_by_orbit_class || {})
      .map(([name, value]) => ({ name, value, color: colors[name] || "#93a4b8" })),
    [data],
  );
  const typeData = useMemo(
    () => Object.entries(data?.satellites_by_object_type || {})
      .map(([name, value]) => ({ name, value }))
      .sort((left, right) => right.value - left.value)
      .slice(0, 8),
    [data],
  );
  const dailyData = useMemo(() => {
    const grouped = new Map();
    for (const event of data?.conjunctions_per_day || []) {
      const day = event.date.slice(0, 10);
      const item = grouped.get(day) || { name: day, high: 0, medium: 0, low: 0 };
      item[event.risk_tier] = event.count;
      grouped.set(day, item);
    }
    return [...grouped.values()];
  }, [data]);

  const totalObjects = Object.values(data?.satellites_by_object_type || {})
    .reduce((total, count) => total + count, 0);
  const conjunctionCount = dailyData.reduce(
    (total, day) => total + day.high + day.medium + day.low,
    0,
  );
  const totalOrbitObjects = orbitData.reduce((total, item) => total + item.value, 0);

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div>
          <p className="section-eyebrow">MISSION CONTROL / DATA INTELLIGENCE</p>
          <h1>Orbital Analytics</h1>
          <p>Dataset-backed catalogue distribution and predicted conjunction activity.</p>
        </div>
        <span className="analytics-demo-badge">LIVE CATALOGUE DATA</span>
      </div>

      <div className="analytics-periods">
        <span>CONJUNCTION WINDOW</span>
        {periods.map((item) => (
          <button key={item} className={period === item ? "active" : ""} onClick={() => setPeriod(item)}>
            {item}
          </button>
        ))}
      </div>

      {error && <p className="analytics-disclaimer" role="alert">{error}</p>}

      <div className="analytics-stats">
        <div className="analytics-stat-card">
          <Satellite />
          <span>CATALOGUE OBJECTS</span>
          <h2>{data ? totalObjects.toLocaleString() : "—"}</h2>
          <small>SATCAT dataset</small>
        </div>
        <div className="analytics-stat-card">
          <Orbit />
          <span>LEO OBJECTS</span>
          <h2>{(data?.satellites_by_orbit_class?.LEO || 0).toLocaleString()}</h2>
          <small>Latest available GP elements</small>
        </div>
        <div className="analytics-stat-card">
          <AlertTriangle />
          <span>PREDICTED APPROACHES</span>
          <h2>{conjunctionCount.toLocaleString()}</h2>
          <small>SOCRATES events in selected window</small>
        </div>
        <div className="analytics-stat-card">
          <Activity />
          <span>HIGH-RISK APPROACHES</span>
          <h2>{dailyData.reduce((total, day) => total + day.high, 0).toLocaleString()}</h2>
          <small>Risk tiers derived from source estimates</small>
        </div>
      </div>

      <div className="analytics-main-grid">
        <section className="analytics-chart-card population-chart">
          <div className="analytics-card-heading">
            <div>
              <h3>OBJECTS BY ORBIT CLASS</h3>
              <p>Classified from the latest available orbital elements</p>
            </div>
            <Activity size={19} />
          </div>
          <div className="chart-area">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={orbitData}>
                <CartesianGrid stroke="#26384b" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8494a8" fontSize={10} />
                <YAxis stroke="#8494a8" fontSize={10} />
                <Tooltip contentStyle={{ background: "#101a28", border: "1px solid #344b64", borderRadius: 8 }} />
                <Bar dataKey="value" fill="#65b9ff" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="analytics-legend">
            {orbitData.map((item) => (
              <span key={item.name}><i style={{ background: item.color }} /> {item.name}</span>
            ))}
          </div>
        </section>

        <section className="analytics-chart-card distribution-chart">
          <div className="analytics-card-heading">
            <div>
              <h3>ORBITAL DISTRIBUTION</h3>
              <p>Share of objects with classifiable orbital elements</p>
            </div>
            <Orbit size={19} />
          </div>
          <div className="donut-chart">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={orbitData} dataKey="value" nameKey="name" innerRadius={65} outerRadius={95} paddingAngle={4} stroke="none">
                  {orbitData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ background: "#101a28", border: "1px solid #344b64", borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="donut-center">
              <strong>{totalOrbitObjects.toLocaleString()}</strong>
              <span>CLASSIFIED</span>
            </div>
          </div>
          <div className="distribution-legend">
            {orbitData.map((item) => (
              <div key={item.name}>
                <span><i style={{ background: item.color }} /> {item.name}</span>
                <strong>{totalOrbitObjects ? `${Math.round(item.value / totalOrbitObjects * 100)}%` : "—"}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="analytics-chart-card activity-chart">
          <div className="analytics-card-heading">
            <div>
              <h3>CONJUNCTIONS BY DAY</h3>
              <p>Predicted SOCRATES events by derived risk tier</p>
            </div>
            <TrendingUp size={19} />
          </div>
          <div className="chart-area">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailyData}>
                <CartesianGrid stroke="#26384b" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8494a8" fontSize={10} />
                <YAxis stroke="#8494a8" fontSize={10} />
                <Tooltip contentStyle={{ background: "#101a28", border: "1px solid #344b64", borderRadius: 8 }} />
                <Area type="monotone" dataKey="high" stroke="#ff8585" fill="#ff858522" />
                <Area type="monotone" dataKey="medium" stroke="#f5d47a" fill="#f5d47a22" />
                <Area type="monotone" dataKey="low" stroke="#65b9ff" fill="#65b9ff22" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="analytics-legend">
            <span><i style={{ background: "#ff8585" }} /> HIGH</span>
            <span><i style={{ background: "#f5d47a" }} /> MEDIUM</span>
            <span><i style={{ background: "#65b9ff" }} /> LOW</span>
          </div>
        </section>

        <section className="analytics-chart-card activity-chart">
          <div className="analytics-card-heading">
            <div>
              <h3>OBJECT TYPE COUNTS</h3>
              <p>Classification provided by the catalogue dataset</p>
            </div>
            <Satellite size={19} />
          </div>
          <div className="chart-area">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeData} layout="vertical">
                <CartesianGrid stroke="#26384b" strokeDasharray="3 3" />
                <XAxis type="number" stroke="#8494a8" fontSize={10} />
                <YAxis dataKey="name" type="category" stroke="#8494a8" fontSize={9} width={90} />
                <Tooltip contentStyle={{ background: "#101a28", border: "1px solid #344b64", borderRadius: 8 }} />
                <Bar dataKey="value" fill="#b794f6" radius={[0, 5, 5, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <p className="analytics-disclaimer">
        Orbit classes are derived from mean motion. Conjunctions are predicted encounters from the SOCRATES sample,
        not observed collisions or validated collision probabilities.
      </p>
    </div>
  );
}

export default Analytics;
