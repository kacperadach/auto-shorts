import { supabase } from "../../lib/supabase";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import Logo from "../../logo.svg";

export default function Login() {
  return (
    <div className="h-full flex justify-center items-center">
      <div className="rounded-xl shadow-lg p-4 bg-white w-fit h-fit flex flex-col items-center prose">
        <div>
          <img
            src={Logo}
            alt="AutoRepurpose Logo"
            className="w-32 m-0"
            width="4rem"
            height="4rem"
          />
        </div>
        <h2 className="my-2">Sign in to AutoRepurpose</h2>
        <Auth
          supabaseClient={supabase}
          providers={[]}
          redirectTo={window.location.origin}
          appearance={{
            theme: ThemeSupa,
            style: {
              container: {
                width: "25rem",
              },
              button: {
                background: "white",
                color: "gray",
                borderColor: "gray",
              },
            },
          }}
        />
        <div>
          <a
            className="mx-2 text-brand-green cursor-pointer"
            href={process.env.REACT_APP_TERMS_OF_SERVICE_URL}
            target="_blank"
          >
            Terms of use
          </a>
          <span>{" | "}</span>
          <a
            className="mx-2 text-brand-green cursor-pointer"
            href={process.env.REACT_APP_PRIVACY_POLICY_URL}
            target="_blank"
          >
            Privacy Policy
          </a>
        </div>
      </div>
    </div>
  );
}
