import { useLocation, useParams } from "react-router";
import {
  addSuccessAlert,
  getRepurposers,
  repurposerMenu,
  repurposers,
} from "../../lib/signals";
import { Repurposer } from "../../lib/types";
import { useEffect, useMemo, useState } from "react";
import { manualRun, updateRepurposer } from "../../lib/api";
import { BsXCircle } from "react-icons/bs";
import { CgDetailsMore, CgPlayButtonO, CgYoutube } from "react-icons/cg";
import { FaHistory } from "react-icons/fa";
import { MdHistory } from "react-icons/md";
import RunHistory from "./RunHistory";
import Channels from "./Channels";
import RepurposerSidebar from "./RepurposerSidebar";
import RepurposerBreadcrumbs from "./RepurposerBreadcrumbs";
import Accounts from "./Accounts";
import CreateRepurposer from "../home/CreateRepurposer";

export default function RepurposerDetails() {
  const location = useLocation();

  const { repurposerId } = useParams();

  const selectedRepurposer = useMemo(() => {
    return repurposers.value.find((r) => r.id === repurposerId);
  }, [repurposers.value, location.pathname]);

  useEffect(() => {
    if (!selectedRepurposer) {
      getRepurposers();
    }
  }, [selectedRepurposer]);

  if (!selectedRepurposer) {
    return null;
  }

  return (
    <div className="flex my-8 w-full flex-grow">
      <div className="w-36">
        <RepurposerSidebar />
      </div>
      <div className="flex-grow flex flex-col">
        <RepurposerBreadcrumbs />
        <div className="prose max-w-none w-full overflow-scroll h-full">
          {repurposerMenu.value === "details" && (
            <CreateRepurposer
              headerText="Edit Repurposer"
              buttonText="Save Changes"
              initialName={selectedRepurposer.name}
              initialSecondaryCategories={
                selectedRepurposer.secondary_categories
              }
              initialTopic={selectedRepurposer.topic}
              showChannels={false}
              onSubmit={async (
                name: string,
                channels: string[],
                secondaryCategories: string[],
                topic: string
              ) => {
                const response = await updateRepurposer(
                  selectedRepurposer.id,
                  name,
                  secondaryCategories,
                  topic
                );
                if (response.success) {
                  addSuccessAlert("Repurposer updated successfully");
                }
              }}
            />
          )}
          {repurposerMenu.value === "history" && (
            <RunHistory repurposerId={repurposerId as string} />
          )}
          {repurposerMenu.value === "channels" && (
            <Channels selectedRepurposer={selectedRepurposer} />
          )}
          {repurposerMenu.value === "accounts" && (
            <Accounts selectedRepurposer={selectedRepurposer} />
          )}
        </div>
      </div>
    </div>
  );
}
