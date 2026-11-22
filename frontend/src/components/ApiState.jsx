import { AlertTriangle, Loader2 } from "lucide-react";
import "./ApiState.css";

export function ApiError({ message, title = "Data unavailable" }) {
  if (!message) return null;
  return (
    <div className="api-state api-error" role="alert">
      <AlertTriangle size={16} />
      <div>
        <strong>{title}</strong>
        <span>{message}</span>
      </div>
    </div>
  );
}

export function ApiLoading({ label = "Loading data..." }) {
  return (
    <div className="api-state api-loading">
      <Loader2 size={16} className="api-spin" />
      <span>{label}</span>
    </div>
  );
}
