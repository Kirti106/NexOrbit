import { useState } from "react";
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

import "./Analytics.css";

const orbitData = [
  { name: "LEO", value: 65, color: "#65b9ff" },
  { name: "MEO", value: 20, color: "#b794f6" },
  { name: "GEO", value: 15, color: "#ffca72" },
];


const chartDataByPeriod = {
  "7D": [
    { name: "Mon", leo: 45, meo: 18, geo: 12 },
    { name: "Tue", leo: 52, meo: 20, geo: 14 },
    { name: "Wed", leo: 49, meo: 22, geo: 15 },
    { name: "Thu", leo: 63, meo: 21, geo: 17 },
    { name: "Fri", leo: 68, meo: 25, geo: 18 },
    { name: "Sat", leo: 75, meo: 27, geo: 20 },
    { name: "Sun", leo: 82, meo: 29, geo: 21 },
  ],
  "30D": [
    { name: "Week 1", leo: 45, meo: 18, geo: 12 },
    { name: "Week 2", leo: 52, meo: 20, geo: 14 },
    { name: "Week 3", leo: 63, meo: 23, geo: 16 },
    { name: "Week 4", leo: 75, meo: 27, geo: 20 },
  ],
  "90D": [
    { name: "Month 1", leo: 45, meo: 18, geo: 12 },
    { name: "Month 2", leo: 60, meo: 22, geo: 16 },
    { name: "Month 3", leo: 78, meo: 28, geo: 21 },
  ],
  "1Y": [
    { name: "Q1", leo: 45, meo: 18, geo: 12 },
    { name: "Q2", leo: 58, meo: 21, geo: 15 },
    { name: "Q3", leo: 72, meo: 25, geo: 19 },
    { name: "Q4", leo: 88, meo: 32, geo: 24 },
  ],
};

const activityDataByPeriod = {
  "7D": [
    { name: "Mon", objects: 42 },
    { name: "Tue", objects: 55 },
    { name: "Wed", objects: 48 },
    { name: "Thu", objects: 68 },
    { name: "Fri", objects: 61 },
    { name: "Sat", objects: 78 },
    { name: "Sun", objects: 72 },
  ],
  "30D": [
    { name: "W1", objects: 45 },
    { name: "W2", objects: 58 },
    { name: "W3", objects: 64 },
    { name: "W4", objects: 78 },
  ],
  "90D": [
    { name: "M1", objects: 48 },
    { name: "M2", objects: 65 },
    { name: "M3", objects: 82 },
  ],
  "1Y": [
    { name: "Q1", objects: 42 },
    { name: "Q2", objects: 58 },
    { name: "Q3", objects: 75 },
    { name: "Q4", objects: 92 },
  ],
};


const periods = ["7D", "30D", "90D", "1Y"];

function Analytics() {
  const [period, setPeriod] = useState("30D");

  const populationData = chartDataByPeriod[period];
  const activityData = activityDataByPeriod[period];

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div>
          <p className="section-eyebrow">MISSION CONTROL / DATA INTELLIGENCE</p>
          <h1>Orbital Analytics</h1>
          <p>Explore orbital population, distribution and activity patterns.</p>
        </div>

        <span className="analytics-demo-badge">
          SIMULATED DATA
        </span>
      </div>

      <div className="analytics-periods">
        <span>TIME PERIOD</span>
        {periods.map((item) => (
          <button
            key={item}
            className={period === item ? "active" : ""}
            onClick={() => setPeriod(item)}
          >
            {item}
          </button>
        ))}
      </div>

      <div className="analytics-stats">
        <div className="analytics-stat-card">
          <Satellite />
          <span>TRACKED OBJECTS</span>
          <h2>24,580</h2>
          <small><TrendingUp size={13} /> Demo catalogue</small>
        </div>

        <div className="analytics-stat-card">
          <Orbit />
          <span>LEO POPULATION</span>
          <h2>15,977</h2>
          <small>65% of demo distribution</small>
        </div>

        <div className="analytics-stat-card">
          <AlertTriangle />
          <span>CONJUNCTION EVENTS</span>
          <h2>128</h2>
          <small>Illustrative event count</small>
        </div>

        <div className="analytics-stat-card">
          <Activity />
          <span>ORBITAL ACTIVITY</span>
          <h2>72%</h2>
          <small>Demo activity indicator</small>
        </div>
      </div>

      <div className="analytics-main-grid">
        <section className="analytics-chart-card population-chart">
          <div className="analytics-card-heading">
            <div>
              <h3>ORBITAL POPULATION TREND</h3>
              <p>Illustrative object distribution over time</p>
            </div>
            <Activity size={19} />
          </div>

          <div className="chart-area">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={populationData}>
                <defs>
                  <linearGradient id="leoGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#65b9ff" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#65b9ff" stopOpacity={0} />
                  </linearGradient>
                </defs>

                <CartesianGrid stroke="#26384b" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8494a8" fontSize={10} />
                <YAxis stroke="#8494a8" fontSize={10} />
                <Tooltip contentStyle={{ background: "#101a28", border: "1px solid #344b64", borderRadius: 8 }} />
                <Area type="monotone" dataKey="leo" stroke="#65b9ff" fill="url(#leoGradient)" strokeWidth={2} />
                <Area type="monotone" dataKey="meo" stroke="#b794f6" fill="none" strokeWidth={2} />
                <Area type="monotone" dataKey="geo" stroke="#ffca72" fill="none" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="analytics-legend">
            <span><i className="leo-color" /> LEO</span>
            <span><i className="meo-color" /> MEO</span>
            <span><i className="geo-color" /> GEO</span>
          </div>
        </section>

        <section className="analytics-chart-card distribution-chart">
          <div className="analytics-card-heading">
            <div>
              <h3>ORBITAL DISTRIBUTION</h3>
              <p>Share by orbital category</p>
            </div>
            <Orbit size={19} />
          </div>

          <div className="donut-chart">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={orbitData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={65}
                  outerRadius={95}
                  paddingAngle={4}
                  stroke="none"
                >
                  {orbitData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "#101a28", border: "1px solid #344b64", borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="donut-center">
              <strong>100%</strong>
              <span>DEMO SHARE</span>
            </div>
          </div>

          <div className="distribution-legend">
            {orbitData.map((item) => (
              <div key={item.name}>
                <span><i style={{ background: item.color }} /> {item.name}</span>
                <strong>{item.value}%</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="analytics-chart-card activity-chart">
          <div className="analytics-card-heading">
            <div>
              <h3>OBJECT ACTIVITY</h3>
              <p>Illustrative weekly activity index</p>
            </div>
            <TrendingUp size={19} />
          </div>

          <div className="chart-area">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData}>
                <CartesianGrid stroke="#26384b" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8494a8" fontSize={10} />
                <YAxis stroke="#8494a8" fontSize={10} />
                <Tooltip contentStyle={{ background: "#101a28", border: "1px solid #344b64", borderRadius: 8 }} />
                <Bar dataKey="objects" fill="#65b9ff" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="analytics-insight-card">
          <p className="section-eyebrow">ORBITAL INSIGHT</p>
          <h3>Understanding Earth's orbital environment</h3>
          <p>
            Low Earth Orbit represents the largest share in this
            illustrative dataset. Population density, orbital
            distribution and object activity are useful indicators
            for monitoring the space environment.
          </p>
          <div className="insight-footer">
            <Activity size={17} />
            DEMONSTRATION ANALYTICS
          </div>
        </section>
      </div>

      <p className="analytics-disclaimer">
        All charts, values and activity indicators are simulated frontend
        examples. They are not live measurements or verified orbital statistics.
      </p>
    </div>
  );
}

export default Analytics;
