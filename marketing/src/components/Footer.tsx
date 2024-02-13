import { MdOutlineCopyright } from "react-icons/md";

export default function Footer() {
  return (
    <div className="w-full flex bg-base-content h-24 p-6 justify-center text-white">
      <div className="w-auto">
        <div className="flex items-center text-sm">
          <span className="mx-1 text-gray-500">Copyright</span>
          <MdOutlineCopyright className="mx-0.25 text-gray-500" />
          <span className="mx-1 text-gray-500">
            {new Date().getFullYear()} AutoRepurpose
          </span>
          <div className="mx-4" />
          <a href="/terms-of-service" className="mx-1 hover:underline">
            Terms
          </a>
          <span>|</span>
          <a href="/privacy-policy" className="mx-1 hover:underline">
            Privacy
          </a>
        </div>
      </div>
    </div>
  );
}
