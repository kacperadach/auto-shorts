import { useNavigate } from "react-router";
import { RepurposerRun } from "../../lib/types";
import { BsCheck, BsCheckCircle, BsXCircle } from "react-icons/bs";
import { capitalizeFirstLetter } from "../../lib/utils";
import { ClipLoader } from "react-spinners";

interface RepurposerRunCardProps {
  run: RepurposerRun;
  repurposerId: string;
}

export default function RepurposerRunCard(props: RepurposerRunCardProps) {
  const { run, repurposerId } = props;

  const navigate = useNavigate();

  return (
    <div
      key={run.id}
      className="flex flex-col justify-end items-center mx-4 w-auto flex-shrink-0 hover:bg-primary cursor-pointer transition duration-300 ease-in-out transform hover:text-base-100  hover:scale-105 p-4 rounded-lg shadow-lg h-fit"
      onClick={() => navigate(`/repurposer/${repurposerId}/run/${run.id}`)}
    >
      <img
        src={run.thumbnail_url}
        className="w-auto object-cover m-0 aspect-video"
      />
      <h5 className="font-semibold text-sm w-full text-left">
        {run.video_title}
      </h5>
      <a
        href={`https://www.youtube.com/watch?v=${run.video_id}`}
        target="_blank"
        className="link text-xs hover:text-secondary w-full text-left"
      >{`https://www.youtube.com/watch?v=${run.video_id}`}</a>
      <div className="flex mt-2 justify-start w-full">
        <div className="tooltip" data-tip={capitalizeFirstLetter(run.status)}>
          <span>
            {run.status === "completed" && (
              <BsCheckCircle size="1.5rem" color="green" />
            )}
            {run.status === "running" && <ClipLoader />}
            {run.status === "failed" && <BsXCircle size="1.5rem" color="red" />}
          </span>
        </div>
      </div>
    </div>
  );
}
