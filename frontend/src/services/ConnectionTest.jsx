
import { useEffect, useState } from "react";
import api from "./api";

export default function ConnectionTest() {
  const [status, setStatus] = useState("Checking backend...");

  useEffect(() => {
    api.get("/api/health")
      .then((response) => {
        setStatus(
          `Backend reached! Status: ${response.data.status}`
        );
      })
      .catch((error) => {
        setStatus(
          `Connection failed: ${error.message}`
        );
      });
  }, []);

  return <p>{status}</p>;
}
