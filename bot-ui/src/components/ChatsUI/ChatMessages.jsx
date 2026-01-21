import React, { useState } from "react";
import { renderMessageWithLinks } from "../../utils/extractors";
import SpecialMenuMainButtonsMessage from "../SpecialMenus/SpecialMenuMainButtonsMessage";
import { formatTimestamp } from "../../utils/timeUtils";
import BranchMessage from "../Branches/BranchMessage";
import FaqMessage from "../Faqs/FaqMessage";

export default function ChatMessages({
  messages,
  chatRef,
  onSend,
  onRemoveMenu,
  sender_id,
  adDownloadStates,
  handleAdDownload,
}) {
  const [branchStates, setBranchStates] = useState({});
  const [faqActiveIndices, setFaqActiveIndices] = useState({});

  const setBranchState = (msgIdx, key, value) => {
    setBranchStates((prev) => {
      const prevMsgState = prev[msgIdx] || {};
      const prevKeyValue =
        prevMsgState[key] !== undefined ? prevMsgState[key] : null;
      const newValue =
        typeof value === "function" ? value(prevKeyValue) : value;
      return { ...prev, [msgIdx]: { ...prevMsgState, [key]: newValue } };
    });
  };

  const handleFaqClick = (msgIdx, idx) => {
    setFaqActiveIndices((prev) => ({
      ...prev,
      [msgIdx]: prev[msgIdx] === idx ? null : idx,
    }));
  };

  return (
    <>
      {messages.map((msg, idx) => (
        <div key={msg.id || idx} className="flex flex-col mb-2 max-w-full">
          {msg.branchData ? (
            <BranchMessage
              msgIdx={idx}
              branchData={msg.branchData}
              branchStates={branchStates}
              setBranchState={setBranchState}
            />
          ) : msg.faqGroups ? (
            <FaqMessage
              msgIdx={idx}
              faqGroups={msg.faqGroups}
              activeIndex={faqActiveIndices[idx] ?? null}
              onHeadingClick={handleFaqClick}
              sender_id={sender_id}
            />
          ) : msg.type === "specialMenuMainButtons" ? (
            <SpecialMenuMainButtonsMessage msg={msg} onSend={onSend} onRemoveMenu={onRemoveMenu} />
          ) : (
            <div
              className={`text-start latoFont font-medium px-4 py-2 rounded-xl text-[15px] border border-[#7D7878] whitespace-pre-line break-words  max-w-[75%] ${
                msg.sender === "user"
                  ? "gradientBtn text-white ml-auto self-end shadow-md font-medium"
                  : "bg-white text-gray-800 shadow max-w-[calc(100%-50px)]"
              }`}
            >
              {/* {renderMessageWithLinks(msg.text, sender_id)} */}
               {renderMessageWithLinks(msg.text, sender_id, msg.isHistoryMessage)}
              {/* <div>
                {msg.ad && (
                  <div className="ad-option mb-2">
                    <img
                      src={msg.ad.image_url}
                      alt="Ad"
                      style={{
                        cursor: "pointer",
                        maxWidth: "250px",
                        borderRadius: "10px",
                      }}
                      onClick={() => window.open(msg.ad.pdf_url, "_blank")}
                    />
                    <div>
                      <a
                        href={msg.ad.pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-white rounded gradientBtn transition-all duration-200 px-3 py-1  font-medium  text-[15px] mt-10"
                        download
                      >
                        Download Flyer
                      </a>
                    </div>
                  </div>
                )}
              </div> */}
              <div>
                {msg.ad && (
                  <div className="ad-option mb-2">
                    {/* <img
                      src={msg.ad.image_url}
                      alt="Ad"
                      style={{
                        cursor: "pointer",
                        maxWidth: "250px",
                        borderRadius: "10px",
                      }}
                      onClick={() => window.open(msg.ad.pdf_url, "_blank")}
                    /> */}
                    <img
                      src={msg.ad.image_url}
                      alt="Ad"
                      style={{
                        cursor: "pointer",
                        maxWidth: "250px",
                        borderRadius: "10px",
                      }}
                      onClick={() => {
                        // silent tracking on image click as well
                        if (
                          handleAdDownload &&
                          msg.ad?.ad_id &&
                          !adDownloadStates?.[msg.ad.ad_id]
                        ) {
                          handleAdDownload(msg.ad.ad_id);
                        }
                        window.open(msg.ad.pdf_url, "_blank");
                      }}
                    />
                    <div>
                      <a
                        href={msg.ad.pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-white rounded gradientBtn transition-all duration-200 px-3 py-1 font-medium text-[15px] mt-10"
                        download
                        onClick={async (e) => {
                          if (
                            handleAdDownload &&
                            msg.ad &&
                            msg.ad.ad_id &&
                            !adDownloadStates?.[msg.ad.ad_id]
                          ) {
                            handleAdDownload(msg.ad.ad_id);
                          }
                        }}
                      >
                        Download Flyer
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {msg.timestamp && (
            <span
              className={`text-[11px] text-gray-500 mt-1 ${
                msg.sender === "user" ? "text-right pr-3" : "text-left pl-3"
              }`}
            >
              {formatTimestamp(msg.timestamp)}
            </span>
          )}
        </div>
      ))}
      <div ref={chatRef}></div>
    </>
  );
}
