import FaqAccordion from "./FaqAccordion";

export default function FaqMessage({
  msgIdx,
  faqGroups,
  activeIndex,
  onHeadingClick,
  sender_id,
}) {
  return (
    <div className="bg-white rounded-xl border border-[#7D7878] shadow p-2">
      <FaqAccordion
        faqGroups={faqGroups}
        activeIndex={activeIndex}
        onHeadingClick={(idx) => onHeadingClick(msgIdx, idx)}
        sender_id={sender_id}
      />
    </div>
  );
}
