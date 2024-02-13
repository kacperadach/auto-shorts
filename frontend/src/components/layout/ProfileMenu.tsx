import { MdLogout, MdInfoOutline } from "react-icons/md";
import { userSession } from "../../lib/signals";
import { supabase } from "../../lib/supabase";

export default function ProfileMenu() {
  if (!userSession.value) {
    return null;
  }
  const { user } = userSession.value;

  return (
    <div className="dropdown dropdown-end">
      <div className="avatar placeholder" tabIndex={0} role="button">
        <div className="bg-primary text-neutral-content rounded-full w-10 cursor-pointer">
          <span className="text-xl">
            {user.email?.slice(0, 1).toUpperCase()}
          </span>
        </div>
      </div>
      <ul
        tabIndex={0}
        className="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-fit"
      >
        <div className="flex items-center justify-center">
          <div className="avatar placeholder ">
            <div className="bg-primary text-neutral-content rounded-full w-10 cursor-pointer">
              <span className="text-xl">
                {user.email?.slice(0, 1).toUpperCase()}
              </span>
            </div>
            <span className="font-semibold text-center m-auto ml-1">
              {user.email}
            </span>
          </div>
        </div>
        <div className="divider m-0" />
        <li>
          <button
            onClick={async () => {
              window.location.href =
                "https://www.autorepurpose.com/disclosure-statement";
            }}
          >
            <MdInfoOutline />
            <span>Data Disclosure</span>
          </button>
        </li>
        <li>
          <button
            onClick={async () => {
              const { error } = await supabase.auth.signOut();
              window.location.href = "/";
            }}
          >
            <MdLogout />
            <span>Logout</span>
          </button>
        </li>
      </ul>
    </div>
  );
}
