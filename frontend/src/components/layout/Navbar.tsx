import { userSession } from "../../lib/signals";
import Logo from "../../logo.svg";
import ProfileMenu from "./ProfileMenu";

export default function Navbar() {
  return (
    <div className="navbar bg-base-200 shadow-lg flex justify-between">
      <div>
        <a href="/" className="flex items-center">
          <img src={Logo} alt="Auto Repurpose Logo" style={{ width: "3rem" }} />
          <span className="logoText text-xl ml-2 font-bold">AutoRepurpose</span>
        </a>
      </div>
      <div>
        <ProfileMenu />
      </div>
    </div>
  );
}
