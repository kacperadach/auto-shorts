import { CgDetailsMore, CgYoutube } from "react-icons/cg";
import { MdHistory, MdOutlineAccountCircle } from "react-icons/md";

import { repurposerMenu } from "../../lib/signals";

interface RepurposerSidebarProps {
  onMenuChange?: () => void;
}

export default function RepurposerSidebar(props: RepurposerSidebarProps) {
  const { onMenuChange } = props;

  return (
    <ul className="menu bg-base-200 rounded-box bg-transparent w-36">
      <li className="h-24 flex items-center  p-2">
        <a
          className="flex flex-col align-center justify-center w-full"
          onClick={() => {
            repurposerMenu.value = "details";
            onMenuChange && onMenuChange();
          }}
        >
          <CgDetailsMore size="3rem" className="text-primary" />
          <span className="text-center">Details</span>
        </a>
      </li>

      <li className="h-24 flex items-center  p-2">
        <a
          className="flex flex-col align-center justify-center w-full"
          onClick={() => {
            repurposerMenu.value = "history";
            onMenuChange && onMenuChange();
          }}
        >
          <MdHistory size="3rem" className="text-primary" />
          <span className="text-center">History</span>
        </a>
      </li>

      <li
        className="h-24 flex items-center p-2"
        onClick={() => {
          repurposerMenu.value = "channels";
          onMenuChange && onMenuChange();
        }}
      >
        <a className="flex flex-col align-center justify-center w-full">
          <CgYoutube size="3rem" className="text-primary" />
          <span className="text-center">Channels</span>
        </a>
      </li>
      <li
        className="h-24 flex items-center p-2"
        onClick={() => {
          repurposerMenu.value = "accounts";
          onMenuChange && onMenuChange();
        }}
      >
        <a className="flex flex-col align-center justify-center w-full">
          <MdOutlineAccountCircle size="3rem" className="text-primary" />
          <span className="text-center">Accounts</span>
        </a>
      </li>
    </ul>
  );
}
