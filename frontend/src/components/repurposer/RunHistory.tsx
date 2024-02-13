import { useEffect, useMemo, useState } from "react";
import { manualRun } from "../../lib/api";
import { BsPlayCircle } from "react-icons/bs";
import {
  addSuccessAlert,
  getRepurposerRuns,
  repurposerRuns,
} from "../../lib/signals";
import RepurposerRunCard from "../run/RepurposerRunCard";

function isValidYoutubeVideoURL(url: string) {
  // Regular expression to match YouTube video URLs
  const regex =
    /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/(watch\?v=)?[a-zA-Z0-9_-]{11}$/;
  return regex.test(url);
}

interface RunHistoryProps {
  repurposerId: string;
}

export default function RunHistory(props: RunHistoryProps) {
  const { repurposerId } = props;
  const [youtubeVideoUrl, setYoutubeVideoUrl] = useState("");
  const [modalOpen, setModalOpen] = useState(false);

  const validUrl = useMemo(() => {
    if (!youtubeVideoUrl) {
      return true;
    }
    return isValidYoutubeVideoURL(youtubeVideoUrl);
  }, [youtubeVideoUrl]);

  useEffect(() => {
    getRepurposerRuns(repurposerId);
  }, []);

  return (
    <div>
      <button className="btn btn-primary text-base-100" onClick={() => setModalOpen(true)}>
        Run Now <BsPlayCircle size="1.5rem" />
      </button>
      <dialog
        id="my_modal_1"
        className="modal bg-black bg-opacity-50"
        open={modalOpen}
        onClose={() => setModalOpen(false)}
      >
        <div className="modal-box">
          <h3 className="font-bold text-lg">Run on YouTube video now</h3>
          <div className="label h-8">
            {!validUrl && (
              <span className="label-text text-red-400">Invalid URL</span>
            )}
          </div>
          <input
            type="text"
            placeholder="YouTube Video URL"
            className={`input input-bordered w-full max-w-none font-medium ${
              !validUrl && "input-error"
            }`}
            value={youtubeVideoUrl}
            onInput={(e) => setYoutubeVideoUrl(e.currentTarget.value)}
          />
          <div className="flex justify-center w-full mt-2">
            {validUrl && youtubeVideoUrl && (
              <button
                className="btn btn-primary text-white w-full"
                onClick={async () => {
                  const response = await manualRun(
                    repurposerId,
                    youtubeVideoUrl
                  );
                  if (response.success) {
                    setModalOpen(false);
                    addSuccessAlert("Run has started successfully.");
                  }
                }}
              >
                Run
              </button>
            )}
          </div>
          <div className="modal-action">
            <form method="dialog">
              <button className="btn">Close</button>
            </form>
          </div>
        </div>
      </dialog>
      <div className="grid grid-cols-4 gap-8 m-2 mt-4">
        {repurposerRuns.value.map((run) => {
          return (
            <RepurposerRunCard
              key={run.id}
              run={run}
              repurposerId={repurposerId}
            />
          );
        })}
      </div>
    </div>
  );
}
