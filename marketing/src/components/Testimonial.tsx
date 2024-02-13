import { RiDoubleQuotesL, RiDoubleQuotesR } from "react-icons/ri";
import "./testimonial.css";

interface TestimonialProps {
  name: string;
  text: string;
  imageSrc: string;
  position: "left" | "center" | "right";
}

export default function Testimonial(props: TestimonialProps) {
  const { name, text, imageSrc, position } = props;

  return (
    <div
      className={`flex flex-col justify-between w-64 h-72 shadow-lg border-2 border-gray-200 rounded testimonial bg-base-100 ${
        position === "left" && "testimonial-left"
      } ${position === "right" && "testimonial-right"}`}
      
    >
      <div>
        <div className="w-full mb-1">
          <RiDoubleQuotesL size="2rem" />
        </div>
        <p className="p-2 text-gray-600">{text}</p>
        <div className="w-full my-1 flex justify-end">
          <RiDoubleQuotesR size="2rem" />
        </div>
      </div>

      <div className="relative h-24 flex flex-col">
        <div className="absolute -top-4 w-full flex justify-center">
          <div className="w-12 h-12 rounded-full overflow-hidden">
            <img className="w-full h-full" src={imageSrc} alt={name} />
          </div>
        </div>
        <svg
          viewBox="0 0 1440 120"
          className="wave"
          style={{ fill: "oklch(var(--p))" }}
        >
          <path d="M0,60 C240,120 240,0 480,60 C720,120 720,0 960,60 C1200,120 1200,0 1440,60 L1440,120 L0,120 Z"></path>
        </svg>
        <div className="bg-primary flex flex-1 text-white justify-center pt-6">
          <span>{name}</span>
        </div>
      </div>
    </div>
  );
}
