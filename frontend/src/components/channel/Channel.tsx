import { useEffect, useMemo } from "react";
import { RepurposerRun } from "../../lib/types";
import { fetchChannelRuns, removeChannel } from "../../lib/api";
import { useLocation, useNavigate, useParams } from "react-router";
import { getRepurposers, repurposerRuns, repurposers } from "../../lib/signals";
import RepurposerSidebar from "../repurposer/RepurposerSidebar";
import RepurposerBreadcrumbs from "../repurposer/RepurposerBreadcrumbs";
import { BsLink, BsTrash, BsYoutube } from "react-icons/bs";
import Swal from "sweetalert2";
import { CgExternal } from "react-icons/cg";
import RepurposerRunCard from "../run/RepurposerRunCard";

export default function Channel() {
  const navigate = useNavigate();

  const { repurposerId, channelId } = useParams();

  const selectedRepurposer = repurposers.value.find(
    (r) => r.id === repurposerId
  );

  const selectedChannel =
    selectedRepurposer &&
    selectedRepurposer.channels.find((c) => c.id === channelId);

  useEffect(() => {
    if (!selectedRepurposer) {
      getRepurposers();
    }
  }, [selectedRepurposer]);

  useEffect(() => {
    if (!selectedChannel) {
      return;
    }

    const getChannelRuns = async () => {
      const response = await fetchChannelRuns(
        selectedChannel.repurposer_id,
        selectedChannel.youtube_channel_id
      );
      if (response.success) {
        repurposerRuns.value = [
          ...repurposerRuns.value.filter(
            (run) => !response.data.find((r: RepurposerRun) => r.id === run.id)
          ),
          ...response.data,
        ];
      }
    };

    getChannelRuns();
  }, [selectedChannel]);

  const channelRuns = repurposerRuns.value.filter(
    (run) => run.channel_id === selectedChannel?.youtube_channel_id
  );

  channelRuns.sort((a, b) => b.created_at - a.created_at);

  if (!selectedChannel || !channelRuns) {
    return null;
  }

  return (
    <div className="flex my-8 w-full ">
      <div className="w-36">
        <RepurposerSidebar
          onMenuChange={() => navigate(`/repurposer/${selectedRepurposer.id}`)}
        />
      </div>
      <div className="flex-grow flex flex-col">
        <RepurposerBreadcrumbs />
        <div className="prose max-w-none w-full mx-8">
          <div className="flex items-center ">
            <img
              src={selectedChannel.thumbnail_url}
              alt="youtube channel thumbnail"
              className="w-24 h-24 rounded-full object-cover m-0 mr-4"
            />
            <div>
              <h1 className="m-0">{selectedChannel.name}</h1>
              <h3 className="m-0">
                {channelRuns?.length || 0} Video Repurposed
              </h3>
              <h5 className="m-0">
                <a
                  href={`https://www.youtube.com/channel/${selectedChannel.youtube_channel_id}`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center"
                >
                  <span>YouTube Channel </span>
                  <CgExternal size="1.5rem" />
                </a>
              </h5>
            </div>
            <div
              className="mx-4 p-4 rounded hover:bg-secondary"
              onClick={() => {
                Swal.fire({
                  title: "Warning!",
                  text: "Are you sure you want to remove this channel?",
                  icon: "warning",
                  confirmButtonText: "Yes",
                  showCancelButton: true,
                  cancelButtonText: "No",
                  customClass: "text-primary",
                  confirmButtonColor: "black",
                }).then(async (result) => {
                  if (result.isConfirmed) {
                    const response = await removeChannel(
                      selectedRepurposer.id,
                      selectedChannel.youtube_channel_id
                    );
                    if (response.success) {
                      repurposers.value = [
                        ...repurposers.value.map((r) => {
                          if (r.id !== selectedRepurposer.id) {
                            return r;
                          }

                          return {
                            ...r,
                            channels: r.channels.filter(
                              (c) => c.id !== selectedChannel.id
                            ),
                          };
                        }),
                      ];
                      navigate(`/repurposer/${selectedRepurposer.id}`);
                    }
                  }
                });
              }}
            >
              <BsTrash size="2rem" className="cursor-pointer" />
            </div>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-8 m-4">
          {channelRuns.map((run: RepurposerRun) => {
            return (
              <RepurposerRunCard
                run={run}
                repurposerId={selectedRepurposer.id}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
