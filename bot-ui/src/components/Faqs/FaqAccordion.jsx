import { ChevronDown, ChevronUp } from "lucide-react";
import { renderMessageWithLinks } from "../../utils/extractors";

const FaqAccordion = ({
  faqGroups,
  activeIndex,
  onHeadingClick,
  sender_id,
}) => {
  if (!Array.isArray(faqGroups)) return null;

  return (
    <div className="space-y-2">
      {faqGroups.map((group, idx) => {
        if (!group?.title || !group?.content) return null;

        const cleanTitle = group.title.replace(/^\d+\.\s*/, "");

        return (
          <div
            key={idx}
            className="bg-white border border-gray-200 rounded-xl shadow-sm boxBorderSub"
          >
            <button
              className="w-full flex justify-between items-center px-4 py-3 font-semibold text-left text-gray-700 "
              onClick={() => onHeadingClick(idx)}
            >
              <span>{cleanTitle}</span>
              {activeIndex === idx ? (
                <ChevronUp size={20} />
              ) : (
                <ChevronDown size={20} />
              )}
            </button>

            {activeIndex === idx && (
              <div className="px-4 pb-4 text-[15px] text-start text-gray-700 space-y-2">
                {group.content.map((line, i) => (
                  <div key={i}>
                    {renderMessageWithLinks(
                      line.replace(/^\d+\.\s*/, ""),
                      sender_id
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default FaqAccordion;
