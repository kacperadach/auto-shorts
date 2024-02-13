import { useMemo, useState } from "react";
import { BsX } from "react-icons/bs";
import { FaInfoCircle } from "react-icons/fa";
import { createRepurposer } from "../../lib/api";
import { addSuccessAlert } from "../../lib/signals";
import { PropagateLoader } from "react-spinners";
import {
  YOUTUBE_CHANNEL_REGEX,
  isValidYoutubeChannel,
} from "../../lib/channel";
import { SECONDARY_VIDEO_CATEGORIES } from "../../lib/types";
import { useNavigate } from "react-router";

const formatCategoryName = (category: string) => {
  return category
    .split("_")
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
};

interface CreateRepurposerProps {
  headerText: string;
  buttonText: string;
  showChannels: boolean;
  initialName?: string;
  initialSecondaryCategories?: string[];
  initialTopic?: string;
  onSubmit: (
    name: string,
    channels: string[],
    secondaryCategories: string[],
    topic: string
  ) => void;
}

export default function CreateRepurposer(props: CreateRepurposerProps) {
  const {
    headerText,
    buttonText,
    initialName,
    showChannels,
    initialSecondaryCategories,
    initialTopic,
    onSubmit,
  } = props;

  const navigate = useNavigate();

  const [repurposerName, setRepurposerName] = useState(initialName || "");
  const [channelName, setChannelName] = useState("");
  const [channels, setChannels] = useState<string[]>([]);
  const [secondaryCategories, setSecondaryCategories] = useState<string[]>(
    initialSecondaryCategories || []
  );
  const [topic, setTopic] = useState(initialTopic || "");
  const [isCreatingRepurposer, setIsCreatingRepurposer] = useState(false);

  const [nameError, setNameError] = useState(false);
  const [channelError, setChannelError] = useState(false);
  const [secondaryError, setSecondaryError] = useState(false);

  const validYoutubeChannel = useMemo(() => {
    if (!channelName) {
      return true;
    }

    return isValidYoutubeChannel(channelName);
  }, [channelName]);

  const duplicateYoutubeChannel = useMemo(() => {
    if (!channelName) {
      return false;
    }

    return channels.includes(channelName);
  }, [channelName, channels]);

  const addChannel = () => {
    if (!validYoutubeChannel || !channelName || duplicateYoutubeChannel) {
      return;
    }

    setChannels((prev) => [...prev, channelName]);
    setChannelName("");
  };

  const handleKeyPress = (event: any) => {
    if (event.key === "Enter") {
      console.log("Enter key pressed!");
      // Place your action here. For example, you could call a function.
      addChannel();
    }
  };

  const validateAndCreateRepurposer = async () => {
    if (isCreatingRepurposer) {
      return;
    }

    if (
      !repurposerName ||
      (showChannels && channels.length === 0) ||
      secondaryCategories.length === 0
    ) {
      if (!repurposerName) {
        setNameError(true);
      }

      if (channels.length === 0) {
        setChannelError(true);
      }

      if (secondaryCategories.length === 0) {
        setSecondaryError(true);
      }
      return;
    }

    console.log("Creating repurposer...");
    setIsCreatingRepurposer(true);

    
    await onSubmit(repurposerName, channels, secondaryCategories, topic);
    setIsCreatingRepurposer(false);
    // const response = await createRepurposer(
    //   repurposerName,
    //   channels,
    //   secondaryCategories,
    //   topic
    // );
    // setIsCreatingRepurposer(false);
    // if (response.success) {
    //   // setRepurposerName("");
    //   // setChannels([]);
    //   // setSecondaryCategories([]);
    //   // setTopic("");
    //   addSuccessAlert("Repurposer created successfully");
    //   navigate(`/repurposer/${response.data.id}`);
    // }
  };

  return (
    <div className="flex flex-col items-center w-full">
      <div className="prose w-1/3">
        <h1>{headerText}</h1>
        <div className="label">
          <span className="label-text">Name of Repurposer</span>
        </div>
        <input
          type="text"
          placeholder="Enter name here..."
          className={`input input-bordered w-full max-w-xs  ${
            nameError && "input-error"
          }`}
          value={repurposerName}
          onChange={(e) => {
            setNameError(false);
            setRepurposerName(e.target.value);
          }}
        />
        {nameError && (
          <div className="label">
            <span className="label-text-alt text-red-400">Enter a name</span>
          </div>
        )}

        {showChannels && (
          <>
            <div className="label mt-4">
              <span className="label-text flex items-center">
                Youtube Channels to Repurpose{" "}
                <span className="mx-1">
                  <div
                    className="tooltip"
                    data-tip="Channels that will automatically get repurposed when new videos get uploaded"
                  >
                    <FaInfoCircle />
                  </div>
                </span>
              </span>
            </div>
            <div>
              <input
                type="text"
                placeholder="Channel URL..."
                className={`input input-bordered w-full max-w-xs ${
                  !validYoutubeChannel && "input-error"
                }`}
                value={channelName}
                onChange={(e) => {
                  setChannelError(false);
                  setChannelName(e.target.value);
                }}
                onKeyPress={handleKeyPress}
              />
              {channelName &&
                validYoutubeChannel &&
                !duplicateYoutubeChannel && (
                  <button
                    className="btn btn-primary mx-2 px-8"
                    onClick={addChannel}
                  >
                    Add
                  </button>
                )}
            </div>
            <div className="label">
              {!validYoutubeChannel && (
                <span className="label-text-alt text-red-400">
                  Invalid Channel URL
                </span>
              )}
              {duplicateYoutubeChannel && (
                <span className="label-text-alt text-red-400">
                  Channel already added
                </span>
              )}
              {channelError && (
                <span className="label-text-alt text-red-400">
                  Add at least one channel
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              {channels.map((channel) => (
                <div
                  key={channel}
                  className="badge badge-primary badge-md text-white py-3 text-md"
                >
                  {YOUTUBE_CHANNEL_REGEX.exec(channel)![1]}
                  <BsX
                    className="text-xl cursor-pointer"
                    onClick={() => {
                      setChannels((prev) => prev.filter((c) => c !== channel));
                    }}
                  />
                </div>
              ))}
            </div>
          </>
        )}

        <div className="label">
          <span className="label-text flex items-center">
            Secondary Channel Themes{" "}
            <span className="mx-1">
              <div
                className="tooltip"
                data-tip="Theme of the videos that will be shown in the bottom half of the Reels"
              >
                <FaInfoCircle />
              </div>
            </span>
          </span>
        </div>
        <div className="mb-4">
          {SECONDARY_VIDEO_CATEGORIES.map((category) => (
            <div className="form-control" style={{ width: "fit-content" }}>
              <label className="cursor-pointer label justify-start">
                <input
                  type="checkbox"
                  checked={secondaryCategories.includes(category)}
                  className={`checkbox checkbox-secondary mr-2 ${
                    secondaryError && "checkbox-error"
                  }`}
                  onChange={(e) => {
                    setSecondaryError(false);
                    if (e.target.checked) {
                      setSecondaryCategories((prev) => [...prev, category]);
                    } else {
                      setSecondaryCategories((prev) =>
                        prev.filter((c) => c !== category)
                      );
                    }
                  }}
                />
                <label>{formatCategoryName(category)}</label>
              </label>
            </div>
          ))}
          {secondaryError && (
            <div className="label">
              <span className="label-text-alt text-red-400">
                Select at least one secondary category
              </span>
            </div>
          )}
        </div>
        <div className="label">
          <span className="label-text">
            What to Repurpose{" "}
            <span className="mx-1">
              <div
                className="tooltip"
                data-tip="By default, the repurposer AI will repurpose any interesting moments from the videos. You can specify topics here to help the AI understand what to look for in the videos."
              >
                <FaInfoCircle />
              </div>
            </span>
          </span>
        </div>
        <input
          type="text"
          placeholder="Enter topics here..."
          className="input input-bordered w-full max-w-xs mb-4"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />
        <div>
          <button
            className="btn btn-lg btn-primary w-full text-white"
            onClick={validateAndCreateRepurposer}
          >
            {isCreatingRepurposer ? (
              <PropagateLoader
                color="white"
                cssOverride={{ transform: "translate(-50%, -50%)" }}
              />
            ) : (
              `${buttonText}`
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
