// Parse branch headings and extract branch details
export function parseBranchHeadings(headings, distanceLabel) {
  const startIdx = headings.findIndex((line) => line.startsWith(distanceLabel));
  if (startIdx === -1) return [];

  let endIdx = headings.length;
  for (let i = startIdx + 1; i < headings.length; i++) {
    if (/^\d+\.\s*(Branches within|भीतर शाखाएँ)/.test(headings[i])) {
      endIdx = i;
      break;
    }
  }

  const section = headings.slice(startIdx + 1, endIdx);
  const branches = [];

  for (let i = 0; i < section.length; i += 3) {
    // Now each branch has 3 lines
    const name = (section[i] || "").replace(/•\s*(name|नाम):\s*/, "");
    const address = (section[i + 1] || "").replace(/•\s*(Address|पता):\s*/, "");
    const navigate = (section[i + 2] || "").replace(
      /•\s*(Navigate|नेविगेट करें):\s*/,
      ""
    );
    if (name) branches.push({ name, address, navigate }); // distance removed
  }

  return branches;
}


export function getAccordionGroups(branchData, selectedDistance) {
  if (!branchData || !selectedDistance) return [];

  // Try to match button for the selected distance
  const btn = branchData.buttons.find((b) => b.includes(selectedDistance));
  if (!btn) return [];

  // Detect Hindi text in either button or rawHeadings
  const isHindi =
    /[\u0900-\u097F]/.test(btn) ||
    (branchData.rawHeadings &&
      branchData.rawHeadings.some((line) => /[\u0900-\u097F]/.test(line)));

  // Parse branches for the selected button
  const branches = parseBranchHeadings(branchData.rawHeadings, btn);

  // No branches found
  if (!branches.length) {
    return [
      {
        title: isHindi
          ? "कोई जानकारी उपलब्ध नहीं है।"
          : "No information available.",
        content: [],
      },
    ];
  }

  // Return properly localized accordion groups
  return branches.map((branch) => ({
    title: branch.name,
    content: isHindi
      ? [
          `पता: ${branch.address || "—"}`,
        
          `${branch.navigate || "—"}`,
        ]
      : [
          `Address: ${branch.address || "—"}`,
          
          `${branch.navigate || "—"}`,
        ],
  }));
}
