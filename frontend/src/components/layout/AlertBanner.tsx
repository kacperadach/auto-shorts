import { alerts } from "../../lib/signals";
import Alert from "./Alert";

export default function AlertBanner() {
  return (
    <div
      className="absolute"
      style={{
        width: "fit-content",
        top: "5%",
        zIndex: 100,
        left: "50%",
        transform: "translateX(-50%)",
      }}
    >
      {alerts.value.map((alert) => {
        return <Alert key={alert.id} alert={alert} />;
      })}
    </div>
  );
}
