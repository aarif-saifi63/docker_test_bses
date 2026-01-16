import { useState } from "react";

// Parse branches for a given distance label (supports English & Hindi)
function parseBranchHeadings(headings, distanceLabel) {
  const startIdx = headings.findIndex((line) => line.startsWith(distanceLabel));
  if (startIdx === -1) return [];

  let endIdx = headings.length;
  for (let i = startIdx + 1; i < headings.length; i++) {
    // Detect next section header in either language
    if (/^\d+\.\s*(Branches within|भीतर शाखाएँ)/.test(headings[i])) {
      endIdx = i;
      break;
    }
  }

  const section = headings.slice(startIdx + 1, endIdx);
  const branches = [];

  for (let i = 0; i < section.length; i += 4) {
    const rawNameLine = section[i] || "";
    const rawAddressLine = section[i + 1] || "";
    const rawDistanceLine = section[i + 2] || "";
    const rawNavigateLine = section[i + 3] || "";

    const name = rawNameLine.replace(/•\s*(name|नाम):\s*/, "") || "";
    const address = rawAddressLine.replace(/•\s*(Address|पता):\s*/, "") || "";
    const distance =
      rawDistanceLine.replace(/•\s*(Distance|दूरी):\s*/, "") || "";
    const navigate =
      rawNavigateLine.replace(/•\s*(Navigate|नेविगेट करें):\s*/, "") || "";

    if (name) {
      branches.push({ name, address, distance, navigate });
    }
  }
  return branches;
}

export default function useBranchAccordion() {
  const [branchData, setBranchData] = useState(null);
  const [selectedDistance, setSelectedDistance] = useState(null);
  const [faqActiveIndex, setFaqActiveIndex] = useState(null);

  function handleBranchResponse(data) {
    setBranchData({
      buttons: data.response.buttons,
      rawHeadings: data.response.heading,
    });
    setSelectedDistance(null);
    setFaqActiveIndex(null);
  }

  function resetBranchAccordion() {
    setBranchData(null);
    setSelectedDistance(null);
    setFaqActiveIndex(null);
  }

 function getAccordionGroups() {
  if (!branchData || !selectedDistance) return [];

  const btn = branchData.buttons.find(b => b.includes(selectedDistance));

  const isHindi = branchData.buttons.some(b => b.includes("भीतर"));

  const branches = parseBranchHeadings(branchData.rawHeadings, btn);

  if (branches.length === 0) {
    // Return a FAQ group with no data message, label depending on language
    return [
      {
        title: isHindi ? "कोई जानकारी उपलब्ध नहीं है।" : "No information available.",
        content: [],
      },
    ];
  }

  return branches.map(branch => ({
    title: branch.name,
    content: isHindi
      ? [
          `पता: ${branch.address}`,
          `दूरी: ${branch.distance}`,
          `नेविगेट करें: ${branch.navigate}`,
        ]
      : [
          `Address: ${branch.address}`,
          `Distance: ${branch.distance}`,
          `Navigate: ${branch.navigate}`,
        ],
  }));
}


  return {
    branchData,
    selectedDistance,
    setSelectedDistance,
    faqActiveIndex,
    setFaqActiveIndex,
    handleBranchResponse,
    getAccordionGroups,
    resetBranchAccordion,
  };
}
