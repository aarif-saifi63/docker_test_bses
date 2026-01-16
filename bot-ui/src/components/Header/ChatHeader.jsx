import React from "react";
import voltra from "../../assets/mascots/e-mitra-F 1.png";
import thunder from "../../assets/thunder-icon.png";
import { AiOutlineHome } from "react-icons/ai";

export default function ChatHeader({ onMenuClick, menuEnabled, resetChat }) {
  return (
    <div className="chatHeader bg-gradient-to-br from-[#d60000] to-[#9e0e0e] text-white px-4 pt-16 pb-5 relative rounded-t-2xl">
      <img src={thunder} alt="Thunder" className="thunderIcon" />
      <img src={voltra} alt="voltra" className="mascotsIcon" />

      <h1 className="font-semibold uppercase text-center">e-MITRA Rajdhani</h1>
      <button
        onClick={resetChat}
        className="homeBtn absolute top-5 right-5 h-[45px] w-[45px] flex items-center justify-center rounded-full transition bg-[#DE4247] hover:bg-[#F00E15] cursor-pointer"
        title="Home"
      >
        <AiOutlineHome size={24} />
      </button>
    </div>
  );
}
