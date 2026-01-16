import React, { useState } from "react";
import { FaMinus, FaPlus } from "react-icons/fa6";
import { getSubComplaintButtons } from "../../utils/extractors";

//  no complaint code 

export default function SpecialMenuMainButtonsMessage({ msg, onSend, onRemoveMenu }) {
  const [openParent, setOpenParent] = useState(null);
  const [subButtons, setSubButtons] = useState([]);

  return (
    <div className="mt-2">
      {msg.specialMenuMainButtons.map((btn, idx) => {
        const isOpen = openParent === btn.original;
        const hasSubMenu = btn.original.startsWith("2.");
        return (
          <div key={idx} className="mb-2">
            <button
              onClick={() => {
                if (hasSubMenu) {
                  if (isOpen) {
                    setOpenParent(null);
                    setSubButtons([]);
                  } else {
                    setOpenParent(btn.original);
                    setSubButtons(
                      getSubComplaintButtons(
                        msg.lastSpecialMenuButtons,
                        btn.original
                      )
                    );
                  }
                } else {
                  setOpenParent(null);
                  setSubButtons([]);
                  onRemoveMenu();
                  onSend(btn.label);
                }
              }}
              className={`boxBorder w-full text-left bg-white font-medium ps-2 pe-8 py-3 hover:bg-red-100 transition relative rounded-lg`}
            >
              {btn.label}
              {hasSubMenu && (
                <span className="absolute top-1/2 right-1 transform -translate-x-1/2 -translate-y-1/2">
                  {isOpen ? <FaMinus /> : <FaPlus />}
                </span>
              )}
            </button>
            {isOpen && subButtons.length > 0 && (
              <div className="ps-5 mt-1">
                {subButtons.map((subBtn, sIdx) => (
                  <button
                    key={sIdx}
                    className="bg-white boxBorderSub w-full text-start font-medium p-2 hover:bg-blue-100 transition relative"
                    onClick={() => {
                      setOpenParent(null);
                      setSubButtons([]);
                      onRemoveMenu();
                      onSend(subBtn.label);
                    }}
                  >
                    {subBtn.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
