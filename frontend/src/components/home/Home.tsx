import { useEffect, useState } from "react";
import Repurposers from "./Repurposers";
import CreateRepurposer from "./CreateRepurposer";
import {
  addSuccessAlert,
  getRepurposers,
  isCreatingRepurposer,
  repurposers,
  userSession,
} from "../../lib/signals";
import RepurposerDetails from "../repurposer/Repurporser";
import { createRepurposer, fetchRepurposers } from "../../lib/api";
import { useNavigate } from "react-router";
import { MdOutlineChevronLeft } from "react-icons/md";


export default function Home() {
  const navigate = useNavigate();

  useEffect(() => {
    getRepurposers();
  });

  return (
    <>
      {!isCreatingRepurposer.value && <Repurposers />}
      {isCreatingRepurposer.value && (
        <>
          <div className="w-full my-2 mb-6 flex justify-center">
            <div className="flex w-1/3 justify-start">
              <button
                className="btn btn-outline rounded-full"
                onClick={() => (isCreatingRepurposer.value = false)}
              >
                <MdOutlineChevronLeft size="2rem" /> Back
              </button>
            </div>
          </div>
          <CreateRepurposer
            headerText="Create New Repurposer"
            buttonText="Create"
            showChannels={true}
            onSubmit={async (
              name: string,
              channels: string[],
              secondaryCategories: string[],
              topic: string
            ) => {
              const response = await createRepurposer(
                name,
                channels,
                secondaryCategories,
                topic
              );

              if (response.success) {
                addSuccessAlert("Repurposer created successfully");
                navigate(`/repurposer/${response.data.id}`);
              }
            }}
          />
        </>
      )}
    </>
  );
}
