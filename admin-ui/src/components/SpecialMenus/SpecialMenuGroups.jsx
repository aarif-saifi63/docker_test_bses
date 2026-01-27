
import React from "react";
import { FaMinus, FaPlus } from "react-icons/fa6";

export default function SpecialMenuGroups({
  specialMenuGroups,
  specialMenuActiveIdx,
  handleSpecialMenuHeading,
  handleSpecialMenuOption,
  icons = [],
}) {
  if (!specialMenuGroups.length) return null;

  return (
    <div className="mt-2">
      {specialMenuGroups.map((group, i) => (
        <div key={i} className="mb-2">
          <div className="flex gap-5">
            {/* Heading icon */}
            {icons[group.headingIconIndex] && (
              <img
                src={icons[group.headingIconIndex]}
                className="w-[40px]"
                alt="icon"
              />
            )}
            <button
              onClick={() => handleSpecialMenuHeading(i)}
              className={`boxBorder w-full text-left bg-white font-medium ps-2 pe-8 py-3 hover:bg-red-100 transition relative ${
                specialMenuActiveIdx === i ? "rounded-l-lg" : "rounded-lg"
              }`}
            >
              {group.heading}
              <span className="absolute top-1/2 right-1 transform -translate-x-1/2 -translate-y-1/2">
                {specialMenuActiveIdx === i ? <FaMinus /> : <FaPlus />}
              </span>
            </button>
          </div>
          {specialMenuActiveIdx === i && (
            <div className="ps-10">
              {group.options.map((opt, oi) => (
                <div className="flex" key={oi}>
                  {/* Option icon */}
                  {icons[group.iconStartIndex + oi] && (
                    <img
                      src={icons[group.iconStartIndex + oi]}
                      className="w-[34px]"
                      alt="icon"
                    />
                  )}
                  <button
                    onClick={() => handleSpecialMenuOption(opt)}

                    className="bg-white boxBorderSub w-full text-start font-medium p-2 hover:bg-blue-100 transition relative"
                  >
                    {opt}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
