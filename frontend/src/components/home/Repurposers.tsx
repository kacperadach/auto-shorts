import { FaPencilAlt } from "react-icons/fa";
import { isCreatingRepurposer, repurposers } from "../../lib/signals";

import { useNavigate } from "react-router-dom";

export default function Repurposers() {
  const navigate = useNavigate();

  return (
    <>
      <div className="w-full flex justify-center mt-4">
        <div className="prose">
          <h1 className="text m-0 text-center">
            Welcome to <span className="tracking-tight">AutoRepurpose</span>
          </h1>
          <h2 className="text-primary my-2 mb-4 text-center">
            To get started, create a new Repurposer
          </h2>
          <div className="flex justify-center">
            <button
              className="btn btn-primary text-xl px-8 text-base-100"
              onClick={() => (isCreatingRepurposer.value = true)}
            >
              Create New
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-8 m-2">
        {repurposers.value.map((repurposer) => {
          return (
            <div
              key={repurposer.id}
              className="card w-full bg-base-100 shadow-xl hover:bg-primary hover:scale-105 transition duration-300 ease-in-out m-2"
            >
              <div
                className="flex flex-col items-center border-2 border-secondary p-8 m-8 prose h-full cursor-pointer bg-base-100"
                onClick={() => navigate(`/repurposer/${repurposer.id}`)}
              >
                <h2 className="my-2">{repurposer.name}</h2>
                <h3>{repurposer.channels.length} channels</h3>
                <div className="flex overflow-scroll w-full">
                  {repurposer.channels.map((channel) => {
                    return (
                      <div
                        key={channel.id}
                        className="flex flex-col justify-end items-center mx-4 w-auto flex-shrink-0"
                      >
                        <h3 className="text-sm truncate text-ellipsis overflow-hidden">
                          {channel.name}
                        </h3>
                        <img
                          src={channel.thumbnail_url}
                          alt="youtube channel thumbnail"
                          className="w-24 h-24 rounded-full object-cover"
                        />
                      </div>
                    );
                  })}
                </div>

                <button
                  className="btn btn-circle btn-outline"
                  onClick={() => navigate(`/repurposer/${repurposer.id}`)}
                >
                  <FaPencilAlt />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
