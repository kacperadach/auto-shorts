import SimpleThumbnail from "../../logo.webp";
import { useState, useEffect } from "react";
import { CircleLoader } from "react-spinners";

export default function LoadingSpinner() {
  const [title, setTitle] = useState("");

  return (
    <div className="my-8" style={{ height: "100vh" }}>
      <div>
        <div className="my-16">
          <CircleLoader size="3rem" />
        </div>
        <div>
          <div className="logoText">Auto Repurpose</div>
        </div>
      </div>
    </div>
  );
}
