
import axios from "axios";

const api = axios.create({
  baseURL: "https://nexorbit-backend.onrender.com",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;
