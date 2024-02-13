interface WaveProps {
  direction: "up" | "down";
  colorClass: string;
}

export default function Wave(props: WaveProps) {
  const { direction, colorClass } = props;

  const fillStyle = { fill: `${colorClass}` };

  if (direction === "up") {
    return (
      <svg viewBox="0 0 1440 80" style={fillStyle}>
        <path d="M1440,21.2101911 L1440,120 L0,120 L0,21.2101911 C120,35.0700637 240,42 360,42 C480,42 600,35.0700637 720,21.2101911 C808.32779,12.416393 874.573633,6.87702029 918.737528,4.59207306 C972.491685,1.8109458 1026.24584,0.420382166 1080,0.420382166 C1200,0.420382166 1320,7.35031847 1440,21.2101911 Z"></path>
      </svg>
    );
  } else {
    return (
      <svg viewBox="0 50 1440 120" style={fillStyle}>
        <path d="M1440,98.7898089 C1320,84.9299363 1200,78 1080,78 C960,78 840,84.9299363 720,98.7898089 C631.67221,107.583607 565.426367,113.12298 521.262472,115.407927 C467.508315,118.189054 413.75416,119.579618 360,119.579618 C240,119.579618 120,112.649682 0,98.7898089 L0,0 L1440,0 Z"></path>
      </svg>
    );
  }
}
