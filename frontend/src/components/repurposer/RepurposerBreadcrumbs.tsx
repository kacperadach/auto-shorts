import { useNavigate, useParams } from "react-router";

export default function RepurposerBreadcrumbs() {
  const navigate = useNavigate();

  const { repurposerId, channelId, runId } = useParams();

  return (
    <div className="text-sm breadcrumbs mb-2">
      <ul>
        {repurposerId && (
          <li>
            <a onClick={() => navigate(`/repurposer/${repurposerId}`)}>
              Repurposer
            </a>
          </li>
        )}
        {repurposerId && channelId && (
          <li>
            <a
              onClick={() =>
                navigate(`/repurposer/${repurposerId}/channel/${channelId}`)
              }
            >
              Channel
            </a>
          </li>
        )}
        {repurposerId && runId && (
          <li>
            <a
              onClick={() =>
                navigate(`/repurposer/${repurposerId}/run/${runId}`)
              }
            >
              Run
            </a>
          </li>
        )}
      </ul>
    </div>
  );
}
