import React from "react";
import ButtonIcon from "./ButtonIcon";
import { SERVICE_PROVIDERS } from "../../utils/extractors";

export default function ChatButtons({
  buttons = [],
  icons = [],
  handleButton,
  isBotLoading = false,
  disableIcons = false,
} = {}) {
  if (!buttons.length) return null;

  const isLanguageButton =
    buttons.includes("english") || buttons.includes("हिंदी");
  const isNewConsumer =
    buttons.includes("New Consumer / नया उपभोक्ता") ||
    buttons.includes("नया एप्लिकेशन उपयोगकर्ता") ||
    buttons.includes("Registered Consumer / पंजीकृत उपभोक्ता") ||
    buttons.includes("पंजीकृत उपभोक्ता");

  return (
    <div
      className={`flex justify-center flex-wrap gap-3 mt-2
        ${isNewConsumer ? "newConsumerBtn" : ""}
        ${isLanguageButton ? "languageBtn" : ""}
        `}
    >
      {buttons.map((btn, i) => {
        const isStatic =
          btn.includes("English") ||
          btn.includes("हिंदी") ||
          btn.includes("New Consumer / नया उपभोक्ता") ||
          btn.includes("नया एप्लिकेशन उपयोगकर्ता") ||
          btn.includes("Registered Consumer / पंजीकृत उपभोक्ता") ||
          btn.includes("पंजीकृत उपभोक्ता");

        return (   
          <div
            key={i}
            className="newConsumerBoxes"
            onClick={() => !isBotLoading && handleButton?.(btn)}
          >
            {!disableIcons &&
              (isStatic ? (
                <ButtonIcon btn={btn} />
              ) : (
                JSON.stringify(buttons) !== JSON.stringify(SERVICE_PROVIDERS) &&
                icons[i] && (
                  <img
                    src={icons[i]}
                    alt="icon"
                    className="w-8 h-8 mb-1 object-contain"
                    loading="lazy"
                  />
                )
              ))}

            <button
              onClick={(e) => {
                e.stopPropagation();
                !isBotLoading && handleButton?.(btn);
              }}
              className="bg-white border border-red-400 text-red-600 font-medium px-4 py-2 rounded-full focus:outline-0 transition text-sm w-full cursor-pointer"
              disabled={isBotLoading}
            >
              {btn}
            </button>
          </div>
        );
      })}
    </div>
  );
}
