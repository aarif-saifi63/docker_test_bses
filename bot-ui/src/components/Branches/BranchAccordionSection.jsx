
import FaqAccordion from "../Faqs/FaqAccordion";
import { IoChevronBack } from "react-icons/io5";

export default function BranchAccordionSection({
  branchData,
  selectedDistance,
  setSelectedDistance,
  faqActiveIndex,
  setFaqActiveIndex,
  getAccordionGroups,
}) {
  if (!branchData) return null;

  const isHindi = branchData.buttons[0]?.includes("भीतर शाखाएँ");

  if (!selectedDistance) {
    return (
      <div className="mt-4">
        <p className="font-semibold">
          {isHindi ? "नज़दीकी शाखाएँ:" : "Nearby Branches:"}
        </p>
        <div className="flex flex-col gap-2 mt-2 ">
          {branchData.buttons.map((btn, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedDistance(btn.split(". ")[1])}
              className="bg-gray-200 hover:bg-gray-300 px-4 py-3 rounded-xl font-semibold text-left text-gray-700 boxBorderSub"
            >
              {btn.split(". ")[1]}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <button
        onClick={() => setSelectedDistance(null)}
        className="flex items-center justify-center text-md rounded-xl ps-7 pe-3 py-2 mb-3 relative boxBorderSub ms-auto backbutton"
      >
        {isHindi ? (
          <>
            <span className="icon boxBorderSub">
              <IoChevronBack size={26} />
            </span>{" "}
            विकल्पों पर वापस जाएं
          </>
        ) : (
          <>
            <span className="icon boxBorderSub">
              <IoChevronBack size={26} />
            </span>{" "}
            Back to options
          </>
        )}
      </button>
      <FaqAccordion
        faqGroups={getAccordionGroups()}
        activeIndex={faqActiveIndex}
        onHeadingClick={(idx) =>
          setFaqActiveIndex((prev) => (prev === idx ? null : idx))
        }
      />
    </div>
  );
}
