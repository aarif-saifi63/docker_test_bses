import { v4 as uuidv4 } from "uuid";
import React, { useState } from "react";
import apiClient from "../services/apiClient";
import { MESSAGE_IDS, hasMessageId } from "../constants/messageIds";

export const STATIC_WELCOME = `Hello ! I'm e-Mitra , yours BSES Rajdhani assistant .To get started , click the Home icon or Main Menu 

नमस्ते ! मैं ई-मित्र हूं, आपका बीएसईएस राजधानी सहायक। आरंभ करने के लिए, होम  के चिन्ह या मुख्य मेनू पर क्लिक करें`;

export const SERVICE_PROVIDERS = ["BSES Rajdhani"];


export const renderMessageWithLinks = (text, sender_id, isHistoryMessage = false, sender = "bot") => {
  if (!text) return null;
  const linkRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(linkRegex);

  return parts.map((part, index) => {
    if (linkRegex.test(part)) {
      // If sender is "user", show plain link. If "bot", show button
      if (sender === "user") {
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 underline hover:text-blue-300 break-all"
          >
            {part}
          </a>
        );
      }
      return <RevealLink
        key={index}
        link={part}
        sender_id={sender_id}
        isHistoryMessage={isHistoryMessage}
      />;
    }
    return <span key={index}>{part}</span>;
  });
};

const RevealLink = ({ link, sender_id, isHistoryMessage = false }) => {
  const handleClick = () => {
    if (isHistoryMessage) {
      return; // Do nothing if it's a history message
    }

    if (link === "https://www.bsesdelhi.com/web/brpl/quick-pay") {
      apiClient
        .post("/save-bill-pay-chat", {
          sender_id: sender_id,
          response: link,
        })
        .catch((err) => console.error("Failed to save bill pay chat", err));
    }

    if (
      link.startsWith(
        "https://byplchatbotbackend.expediensolutions.in/generated_pdfs/"
      )
    ) {
      apiClient
        .post("/save-duplicate-bill", {
          sender_id: sender_id,
          response: link,
        })
        .catch((err) => console.error("Failed to save duplicate bill", err));
    }

    // Always open the link in new tab
    window.open(link, "_blank", "noopener,noreferrer");
  };

  return (
    <button
      onClick={handleClick}
      disabled={isHistoryMessage}
      className={`px-3 py-1 ml-2 text-white rounded transition-all duration-200 ${isHistoryMessage
        ? 'bg-gray-400 cursor-not-allowed opacity-60'
        : 'gradientBtn hover:opacity-90'
        }`}
    >
      Open Link
    </button>
  );
};

export function isSpecialMenuResponse(response) {
  // Use ID-based check if utter_message_id is available
  if (response?.utter_message_id && Array.isArray(response.utter_message_id)) {
    return (
      response &&
      Array.isArray(response.buttons) &&
      response.buttons.some((b) => /^\d+\.\s/.test(b)) &&
      hasMessageId(response.utter_message_id, MESSAGE_IDS.LANGUAGE_UPDATED_EN, MESSAGE_IDS.LANGUAGE_UPDATED_HI)
    );
  }
}

export function groupButtons(buttons) {
  const groups = [];
  let currentGroup = null;
  let iconIndex = 0;

  buttons.forEach((btn) => {
    const headingMatch = btn.match(/^(\d+)\.\s*(.+)$/);
    if (headingMatch) {
      if (currentGroup) groups.push(currentGroup);
      currentGroup = {
        heading: headingMatch[2],
        options: [],
        headingIconIndex: iconIndex, // icon for heading
        iconStartIndex: iconIndex + 1, // first option icon index
      };
      iconIndex++; // move to next icon for first option
    } else {
      if (currentGroup) {
        currentGroup.options.push(btn);
        iconIndex++; // move to next icon for next option
      }
    }
  });

  if (currentGroup) groups.push(currentGroup);
  return groups;
}

export function getMainComplaintButtons(buttons) {
  // Get main buttons but strip numbers

  return buttons

    .filter(
      (btn) =>
        /^\d+\.\s+.+/.test(btn) && // Is a main button
        !/^\d+\.\d+\.\s+.+/.test(btn) // Not a sub-button
    )

    .map((btn) => ({
      original: btn, // Keep original for finding sub-buttons

      label: btn.replace(/^\d+\.\s*/, ""), // Remove number prefix
    }));
}

export function getSubComplaintButtons(buttons, parentBtn) {
  // Get sub-buttons for a parent, strip numbers

  const parentNum = parentBtn.match(/^(\d+)\./)[1];

  return buttons

    .filter(
      (btn) => btn.startsWith(`${parentNum}.`) && /^\d+\.\d+\.\s+.+/.test(btn)
    )

    .map((btn) => ({
      original: btn,

      label: btn.replace(/^\d+\.\d+\.\s*/, ""),
    }));
}