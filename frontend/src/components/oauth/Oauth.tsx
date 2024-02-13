import { useState } from "react";
import {
  initiate_oauth_youtube,
  initiate_oauth_facebook,
  manualUpload,
} from "../../lib/api";

export default function Oauth() {
  const [url, setUrl] = useState("");
  const [accessToken, setAccessToken] = useState("");

  return (
    <div>
      <div className="m-4">
        <button
          className="btn btn-primary"
          onClick={async () => {
            const response = await initiate_oauth_youtube();
            if (!response.success) {
              console.log("Failed to initiate oauth");
              return;
            }

            const { auth_url } = response.data;

            window.open(auth_url, "_blank");
          }}
        >
          Initiate OAuth Google
        </button>
      </div>
      <div>
        <input
          type="text"
          placeholder="Video URL"
          className="input input-bordered w-full max-w-xs mx-2"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <input
          type="text"
          placeholder="Access Token"
          className="input input-bordered w-full max-w-xs mx-2"
          value={accessToken}
          onChange={(e) => setAccessToken(e.target.value)}
        />
        <button
          className="btn btn-secondary"
          onClick={async () => {
            const response = await manualUpload(url, accessToken);
          }}
        >
          Upload
        </button>
      </div>
      {/* <div className="m-4">
        <button
          className="btn btn-primary"
          onClick={async () => {
            const response = await initiate_oauth_facebook();
            if (!response.success) {
              console.log("Failed to initiate oauth");
              return;
            }

            const { auth_url } = response.data;

            window.open(auth_url, "_blank");
          }}
        >
          Initiate OAuth Facebook
        </button>
      </div> */}
    </div>
  );
}
