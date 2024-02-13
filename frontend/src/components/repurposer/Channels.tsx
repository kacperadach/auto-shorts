import { useEffect, useMemo, useState } from "react";
import { Repurposer, RepurposerChannel, RepurposerRun } from "../../lib/types";
import { BsPlus, BsPlusCircle, BsTrash } from "react-icons/bs";
import { addChannel, fetchChannelRuns } from "../../lib/api";
import { repurposerRuns, repurposers } from "../../lib/signals";
import { useNavigate } from "react-router";
import { isValidYoutubeChannel } from "../../lib/channel";

interface ChannelsProps {
  selectedRepurposer: Repurposer;
}

export default function Channels(props: ChannelsProps) {
  const { selectedRepurposer } = props;

  const [modalOpen, setModalOpen] = useState(false);
  const [channelUrl, setChannelUrl] = useState("");

  const navigate = useNavigate();

  const validYoutubeChannel = useMemo(() => {
    if (!channelUrl) {
      return true;
    }

    return isValidYoutubeChannel(channelUrl);
  }, [channelUrl]);

  useEffect(() => {
    const handleKeyDown = (event: any) => {
      if (event.key === "Escape") {
        setModalOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  if (!selectedRepurposer) {
    return null;
  }

  return (
    <>
      <div>
        <button
          className="btn btn-primary text-base-100"
          onClick={() => setModalOpen(true)}
        >
          Add New Channel <BsPlusCircle size="1.5rem" />
        </button>
      </div>
      <dialog
        id="my_modal_1"
        className="modal bg-black bg-opacity-50"
        open={modalOpen}
        onClose={() => setModalOpen(false)}
      >
        <div className="modal-box">
          <h3 className="font-bold text-lg">Add New Channel</h3>
          <input
            type="text"
            placeholder="YouTube Channel URL"
            className="input input-bordered w-full max-w-xs"
            value={channelUrl}
            onChange={(e) => setChannelUrl(e.target.value)}
          />
          {validYoutubeChannel && channelUrl && (
            <button
              className="btn btn-active btn-primary mx-2 px-6"
              onClick={async () => {
                const response = await addChannel(
                  selectedRepurposer.id,
                  channelUrl
                );
                if (response.success) {
                  repurposers.value = [
                    ...repurposers.value.map((r) => {
                      if (r.id !== selectedRepurposer.id) {
                        return r;
                      }

                      return response.data;
                    }),
                  ];
                  setModalOpen(false);
                }
              }}
            >
              Add
            </button>
          )}
          <div className="label">
            {!validYoutubeChannel && (
              <span className="label-text-alt text-red-400">
                Invalid Channel URL
              </span>
            )}
          </div>

          <div className="modal-action">
            <form method="dialog">
              <button className="btn">Close</button>
            </form>
          </div>
        </div>
      </dialog>
      <div className="grid grid-cols-6 gap-8 m-2">
        {selectedRepurposer.channels.map((channel) => {
          return (
            <div
              key={channel.id}
              className="flex flex-col justify-end items-center mx-4 w-auto flex-shrink-0 hover:bg-primary hover:text-base-100 cursor-pointer transition duration-300 ease-in-out transform hover:scale-105 p-4 rounded-lg shadow-lg"
              onClick={() =>
                navigate(
                  `/repurposer/${selectedRepurposer.id}/channel/${channel.id}`
                )
              }
            >
              <span className="text-sm truncate text-ellipsis overflow-hidden font-semibold">
                {channel.name}
              </span>
              <img
                src={channel.thumbnail_url}
                alt="youtube channel thumbnail"
                className="w-24 h-24 rounded-full object-cover"
              />
            </div>
          );
        })}
      </div>
    </>
  );
}
