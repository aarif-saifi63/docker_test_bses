import React, { useState } from "react";
import { Pencil, Trash2, ChevronDown, ChevronUp } from "lucide-react";

export default function MenuTable({
  menus = [],
  loading,
  onEdit,
  onDelete,
  onToggleActive,
  language,
}) {
  const [expandedMenus, setExpandedMenus] = useState([]);
  const [expandedExamples, setExpandedExamples] = useState({}); // 👈 track expanded intents

  if (loading) return <div className="text-center text-gray-500 py-6">Loading menus...</div>;

  if (!menus || menus.length === 0)
    return (
      <div className="text-center text-gray-400 py-6">
        No menus available for {language === "english" ? "English" : "Hindi"}.
      </div>
    );

  const toggleExpand = (menuId) => {
    setExpandedMenus((prev) =>
      prev.includes(menuId) ? prev.filter((id) => id !== menuId) : [...prev, menuId]
    );
  };

  const toggleExamples = (intentId) => {
    setExpandedExamples((prev) => ({
      ...prev,
      [intentId]: !prev[intentId],
    }));
  };

  return (
    <div className="overflow-x-auto border border-gray-200 rounded-lg">
      <table className="min-w-full border-collapse">
        <thead className="bg-gray-100 text-sm">
          <tr>
            <th className="px-4 py-2 text-left border-b">Menu Title</th>
            <th className="px-4 py-2 text-center border-b">Language</th>
            {/* <th className="px-4 py-2 text-center border-b">Visible</th> */}
            <th className="px-4 py-2 text-center border-b">Submenus</th>
            {/* <th className="px-4 py-2 text-center border-b">Actions</th> */}
          </tr>
        </thead>

        <tbody>
          {menus.map((menu) => {
            const isExpanded = expandedMenus.includes(menu.menu_id);
            return (
              <React.Fragment key={menu.menu_id}>
                {/* ----- MAIN MENU ROW ----- */}
                <tr
                  className="hover:bg-gray-50 transition cursor-pointer"
                  onClick={() => toggleExpand(menu.menu_id)}
                >
                  <td className="px-4 py-3 border-b font-medium flex items-center gap-2">
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                    {menu.menu_name}
                  </td>
                  <td className="px-4 py-3 border-b text-center capitalize">
                    {menu.lang === "en" ? "English" : "Hindi"}
                  </td>
                  {/* <td className="px-4 py-3 border-b text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleActive(menu);
                      }}
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        menu.is_visible
                          ? "bg-green-100 text-green-700 border border-green-300"
                          : "bg-gray-100 text-gray-700 border border-gray-300"
                      }`}
                    >
                      {menu.is_visible ? "Visible" : "Hidden"}
                    </button>
                  </td> */}
                  <td className="px-4 py-3 border-b text-center">{menu.sub_menus?.length || 0}</td>
                  {/* <td
                    className="px-4 py-3 border-b text-center flex justify-center gap-2"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={() => onEdit(menu)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <Pencil className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => onDelete(menu.menu_id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </td> */}
                </tr>

                {/* ----- EXPANDED SUBMENU SECTION ----- */}
                {isExpanded && (
                  <tr>
                    <td colSpan="5" className="bg-gray-50 border-b">
                      <div className="p-4 space-y-4">
                        {(menu.sub_menus || []).map((submenu) => (
                          <div
                            key={submenu.sub_menu_id}
                            className="border border-gray-200 rounded-lg bg-white shadow-sm"
                          >
                            {/* Submenu Header */}
                            {/* <div className="p-3 border-b flex justify-between items-center">
                              <div>
                                <h3 className="font-semibold text-gray-800">
                                  {submenu.sub_menu_name}
                                </h3>
                                <p className="text-xs text-gray-500">
                                  {submenu.lang === "en" ? "English" : "Hindi"} |{" "}
                                  {submenu.is_visible ? "Visible" : "Hidden"}
                                </p>
                              </div>
                              <span className="text-sm text-gray-500">
                                {submenu.intents?.length || 0} intents
                              </span>
                            </div> */}

                            {/* Intents */}
                            <div className="p-3 space-y-3">
                              {(submenu.intents || []).map((intent) => {
                                const isExpanded = expandedExamples[intent.intent_id];
                                const examples = intent.examples || [];
                                const displayedExamples = isExpanded
                                  ? examples
                                  : examples.slice(0, 5);

                                return (
                                  <div
                                    key={intent.intent_id}
                                    className="bg-gray-50 rounded-md p-3 border"
                                  >
                                    <p className="font-medium text-gray-700 mb-1">
                                      🧠 {intent.intent_name}
                                    </p>

                                    {/* Examples list */}
                                    <ul className="list-disc pl-5 text-sm text-gray-600">
                                      {displayedExamples.map((ex, idx) => (
                                        <li key={idx}>{ex}</li>
                                      ))}
                                    </ul>

                                    {/* Toggle button */}
                                    {examples.length > 5 && (
                                      <button
                                        onClick={() => toggleExamples(intent.intent_id)}
                                        className="mt-2 text-blue-600 text-sm hover:underline"
                                      >
                                        {isExpanded
                                          ? "Show less"
                                          : `Show ${examples.length - 5} more`}
                                      </button>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
