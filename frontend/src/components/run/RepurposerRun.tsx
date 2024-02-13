import { useNavigate, useParams } from "react-router";
import RepurposerBreadcrumbs from "../repurposer/RepurposerBreadcrumbs";
import RepurposerSidebar from "../repurposer/RepurposerSidebar";
import { useEffect } from "react";
import {
  getRepurposerRuns,
  getRepurposers,
  repurposerRuns,
  repurposers,
} from "../../lib/signals";
import { CgExternal } from "react-icons/cg";
import { capitalizeFirstLetter } from "../../lib/utils";
import { BsCheckCircle, BsXCircle } from "react-icons/bs";
import { ClipLoader } from "react-spinners";

export default function RepurposerRun() {
  const navigate = useNavigate();

  const { repurposerId, runId } = useParams();

  const selectedRepurposer = repurposers.value.find(
    (r) => r.id === repurposerId
  );

  const selectedRun = repurposerRuns.value.find((r) => r.id === runId);

  console.log(selectedRun);

  useEffect(() => {
    if (!selectedRepurposer) {
      getRepurposers();
    }
  }, [selectedRepurposer]);

  useEffect(() => {
    if (!selectedRun) {
      getRepurposerRuns(repurposerId as string);
    }
  }, [selectedRun, repurposerId]);

  return (
    <div className="flex my-8 w-full ">
      <div className="w-36">
        <RepurposerSidebar
          onMenuChange={() => navigate(`/repurposer/${repurposerId}`)}
        />
      </div>
      <div className="flex-grow flex flex-col">
        <RepurposerBreadcrumbs />
        <div className="prose max-w-none w-full overflow-scroll h-full">
          {selectedRun && (
            <>
              <div>
                <div className="w-1/4">
                  <img
                    src={selectedRun.thumbnail_url}
                    className="w-full object-cover m-0 aspect-video"
                  />
                  <h5 className="font-semibold text-lg w-full text-left">
                    {selectedRun.video_title}
                  </h5>
                  <div className="flex items-center justify-between">
                    <a
                      href={`https://www.youtube.com/watch?v=${selectedRun.video_id}`}
                      target="_blank"
                      className="link text-xs hover:text-secondary text-left"
                    >{`https://www.youtube.com/watch?v=${selectedRun.video_id}`}</a>
                    <div className="flex justify-start">
                      <div
                        className="tooltip"
                        data-tip={capitalizeFirstLetter(selectedRun.status)}
                      >
                        <span>
                          {selectedRun.status === "completed" && (
                            <BsCheckCircle size="1.5rem" color="green" />
                          )}
                          {selectedRun.status === "running" && <ClipLoader />}
                          {selectedRun.status === "failed" && (
                            <BsXCircle size="1.5rem" color="red" />
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="divider">
                  {selectedRun.renders.length} videos
                </div>
                <div className="grid grid-cols-6 gap-8 m-4">
                  {selectedRun.renders.map((render) => {
                    return (
                      <div key={render.id}>
                        <video controls className="m-0">
                          <source src={render.s3_url} type="video/mp4" />
                          Your browser does not support the video tag.
                        </video>
                      </div>
                    );
                  })}
                </div>
              </div>
              {/* <div className="divider" /> */}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
