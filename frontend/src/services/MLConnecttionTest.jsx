
import { useEffect, useState } from "react";
import mlApi from "./mlApi";

export default function MLConnectionTest() {
  const [status, setStatus] = useState("Connecting to ML service...");

  useEffect(() => {
    mlApi.get("/health")
      .then((response) => {
        setStatus(
          `ML service reachable. Database: ${response.data.database}`
        );
      })
      .catch((error) => {
        setStatus(`ML connection failed: ${error.message}`);
      });
  }, []);

  return <p>{status}</p>;
}
