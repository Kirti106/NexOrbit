import { BrowserRouter, Routes, Route } from "react-router-dom";

import Navbar from "./components/Navbar";
import Overview from "./pages/Overview";
import Tracking from "./pages/Tracking";
import OrbitMap from "./pages/OrbitMap";
import Alerts from "./pages/Alerts";
import Analytics from "./pages/Analytics";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="nexorbit-app">
        <Navbar />

        <main>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/tracking" element={<Tracking />} />
            <Route path="/orbit-map" element={<OrbitMap />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
