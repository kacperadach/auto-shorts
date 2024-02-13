import "./growth.css";

export default function Growth() {
  return (
    <div>
      <h3 className="font-bold text-4xl text-center mb-8">
        100% Hands Off Growth
      </h3>
      <svg width="600" height="300" xmlns="http://www.w3.org/2000/svg">
        <line
          x1="10"
          y1="290"
          x2="590"
          y2="290"
          stroke="black"
          strokeWidth="3"
        />

        <line x1="10" y1="290" x2="10" y2="10" stroke="black" strokeWidth="3" />

        <path
          d="M10 290 L100 280 L200 260 L300 220 L400 150 L500 90 L600 10"
          fill="none"
          stroke="oklch(var(--s))"
          strokeWidth="5"
          className="line-animation"
        />
      </svg>
      <h3 className="font-bold text-2xl text-center my-8">
        Let AI help your content grow
      </h3>
    </div>
  );
}
