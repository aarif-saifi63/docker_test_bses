import BranchAccordionSection from "../Branches/BranchAccordionSection";
import { getAccordionGroups } from "../../utils/branchUtils";

export default function BranchMessage({
  msgIdx,
  branchData,
  branchStates,
  setBranchState,
}) {
  return (
    <div className="bg-white rounded-xl border border-[#7D7878] shadow p-2">
      <BranchAccordionSection
        branchData={branchData}
        selectedDistance={branchStates[msgIdx]?.selectedDistance || null}
        setSelectedDistance={(val) =>
          setBranchState(msgIdx, "selectedDistance", val)
        }
        faqActiveIndex={branchStates[msgIdx]?.faqActiveIndex ?? null}
        setFaqActiveIndex={(val) =>
          setBranchState(msgIdx, "faqActiveIndex", val)
        }
        getAccordionGroups={() =>
          getAccordionGroups(branchData, branchStates[msgIdx]?.selectedDistance)
        }
      />
    </div>
  );
}
