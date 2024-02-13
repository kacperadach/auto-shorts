import { BsStarFill } from "react-icons/bs";

export default function LaurelPraise() {
  return (
    <div className="relative w-48 mt-6">
      <div className="absolute w-full h-full flex flex-col items-center justify-center text-sm font-bold">
        <span>#1 Repurpose App</span>
        <div className="flex">
          <BsStarFill />
          <BsStarFill />
          <BsStarFill />
          <BsStarFill />
          <BsStarFill />
        </div>
      </div>
      <img src="/laurel.svg" alt="laurel" />
    </div>
  );
}
