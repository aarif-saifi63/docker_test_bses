import React, { useState, useEffect } from "react";
import {
  Plus,
  Trash2,
  ChevronLeft,
  Check,
  FolderTree,
  ChevronDown,
  ChevronUp,
  Image as ImageIcon,
} from "lucide-react";
import IntentForm from "../Intent/IntentForm";
import CircularProgress from "@mui/material/CircularProgress";

export default function SubmenuForm({
  submenus,
  setSubmenus,
  onBack,
  onSave,
  parentLang = "english",
  selectedUserName = "",
  loadingMenu,
}) {
  const [expandedSubmenu, setExpandedSubmenu] = useState(null);

  // Ensure there is at least one submenu
  useEffect(() => {
    if (submenus.length === 0) {
      addSubmenu();
    }
  }, []);

  const generateStoryName = (submenuName) => {
    const timestamp = Date.now();
    const safeUser = selectedUserName.replace(/\s+/g, "_");
    const safeName = submenuName.trim().replace(/\s+/g, "_");
    return `${safeUser}_${safeName}_${timestamp}`;
  };

  const addSubmenu = () => {
    const newSub = {
      tempId: Date.now().toString(),
      name: "",
      lang: parentLang,
      is_visible: true,
      story_name: "",
      icon_path: null, // 🆕 icon field
      intents: [
        {
          tempId: Date.now().toString() + "-i",
          name: "",
          actions: [{ name: "" }],
          utters: [{ name: "", response: "" }],
          examples: [{ example: "" }],
        },
      ],
    };
    setSubmenus((prev) => [...prev, newSub]);
  };

  const updateSubmenuName = (tempId, name) => {
    setSubmenus((prev) =>
      prev.map((s) =>
        s.tempId === tempId
          ? {
              ...s,
              name,
              story_name: generateStoryName(name),
            }
          : s
      )
    );
  };

  const toggleVisibility = (tempId) => {
    setSubmenus((prev) =>
      prev.map((s) => (s.tempId === tempId ? { ...s, is_visible: !s.is_visible } : s))
    );
  };

  const deleteSubmenu = (tempId) => {
    if (submenus.length === 1) return alert("At least one submenu is required.");
    if (window.confirm("Delete this submenu?")) {
      setSubmenus(submenus.filter((s) => s.tempId !== tempId));
    }
  };

  const updateIntents = (submenuTempId, updatedIntents) => {
    setSubmenus((prev) =>
      prev.map((s) => (s.tempId === submenuTempId ? { ...s, intents: updatedIntents } : s))
    );
  };

  const handleIconChange = (tempId, file) => {
    setSubmenus((prev) =>
      prev.map((s) =>
        s.tempId === tempId
          ? {
              ...s,
              icon_path: file,
            }
          : s
      )
    );
  };

  const removeIcon = (tempId) => {
    setSubmenus((prev) =>
      prev.map((s) =>
        s.tempId === tempId
          ? {
              ...s,
              icon_path: null,
            }
          : s
      )
    );
  };

  const handleSaveAll = () => {
    if (submenus.length === 0) return alert("Add at least one submenu.");
    for (let s of submenus) {
      if (!s.name.trim()) return alert("Each submenu must have a name.");
    }

 
    const cleanedSubmenus = submenus.map(({ tempId, intents, ...rest }) => ({
      ...rest,
      intents: intents.map(({ tempId: intentTempId, ...intentRest }) => intentRest),
    }));

    onSave(cleanedSubmenus);
  };

  const toggleExpand = (tempId) => {
    setExpandedSubmenu(expandedSubmenu === tempId ? null : tempId);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
        <FolderTree className="w-5 h-5 text-blue-600" />
        Configure Submenus & Intents
      </h2>

      <p className="text-sm text-gray-500 mb-3">
        Each submenu can contain multiple intents. Expand a submenu below to configure its intents.
      </p>

      {submenus.map((submenu, idx) => {
        const isOpen = expandedSubmenu === submenu.tempId;
        return (
          <div
            key={submenu.tempId}
            className="border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition bg-gray-50"
          >
            {/* SUBMENU HEADER */}
            <div
              className="flex justify-between items-center p-4 cursor-pointer"
              onClick={() => toggleExpand(submenu.tempId)}
            >
              <div className="flex flex-col w-full">
                <span className="font-semibold text-gray-800 mb-1">
                  Submenu #{idx + 1}: {submenu.name || "(Untitled)"}
                </span>

                {/* Submenu Name */}
                <input
                  type="text"
                  value={submenu.name}
                  onClick={(e) => e.stopPropagation()}
                  onChange={(e) => updateSubmenuName(submenu.tempId, e.target.value)}
                  placeholder="Submenu Name (e.g., Billing, Complaints)"
                  className="mt-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                />

                {/* Lang & Story Name Display */}
                <div className="mt-2 text-xs text-gray-500">
                  <p>
                    🌐 Language: <b>{submenu.lang}</b>
                  </p>
                  {submenu.story_name && (
                    <p>
                      🧾 Story Name:{" "}
                      <span className="text-gray-700 font-mono">{submenu.story_name}</span>
                    </p>
                  )}
                </div>

                {/* Submenu Icon Upload */}
                <div className="mt-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                    <ImageIcon className="w-4 h-4" /> Submenu Icon
                  </label>
                  <input
                    type="file"
                    accept="image/*"
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => {
                      const file = e.target.files[0];
                      if (file && file.type.startsWith("image/"))
                        handleIconChange(submenu.tempId, file);
                    }}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />

                  {submenu.icon_path && (
                    <div className="mt-2 flex flex-col items-start">
                      <img
                        src={
                          submenu.icon_path instanceof File
                            ? URL.createObjectURL(submenu.icon_path)
                            : submenu.icon_path
                        }
                        alt="Submenu Icon Preview"
                        className="w-32 h-32 object-cover rounded-lg border"
                      />

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeIcon(submenu.tempId);
                        }}
                        className="mt-2 text-sm text-red-600 hover:text-red-800"
                      >
                        Remove Icon
                      </button>
                    </div>
                  )}
                </div>

                {/* Visibility Toggle */}
                <div className="mt-2 flex items-center gap-2">
                  <label className="text-sm text-gray-600">Visible:</label>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleVisibility(submenu.tempId);
                    }}
                    className={`px-3 py-1 rounded-full text-sm border ${
                      submenu.is_visible
                        ? "bg-green-100 border-green-400 text-green-700"
                        : "bg-gray-100 border-gray-300 text-gray-600"
                    }`}
                  >
                    {submenu.is_visible ? "Yes" : "No"}
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-3 ml-4">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSubmenu(submenu.tempId);
                  }}
                  className="text-red-500 hover:text-red-700"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
                {isOpen ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </div>
            </div>

            {/* INTENTS SECTION */}
            {isOpen && (
              <div className="border-t border-gray-200 bg-white p-4">
                <div className="mb-4">
                  <h4 className="text-gray-700 font-medium mb-1">
                    🧠 Configure Intents for{" "}
                    <span className="font-semibold">{submenu.name || "this submenu"}</span>
                  </h4>
                  <p className="text-xs text-gray-500">
                    Add multiple intents with their actions and user examples.
                  </p>
                </div>

                <IntentForm
                  intents={submenu.intents}
                  setIntents={(updated) => updateIntents(submenu.tempId, updated)}
                  embedded={true}
                  onSave={(validated) => updateIntents(submenu.tempId, validated)}
                />
              </div>
            )}
          </div>
        );
      })}

      {/* FOOTER */}
      <div className="flex justify-between items-center pt-6 border-t">
        <button
          onClick={addSubmenu}
          className="flex items-center gap-2 text-blue-600 hover:underline"
        >
          <Plus className="w-4 h-4" /> Add New Submenu
        </button>

        <div className="flex gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100"
          >
            <ChevronLeft className="w-4 h-4" /> Back
          </button>
          <button
            onClick={handleSaveAll}
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            {loadingMenu ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <>
                <Check className="w-4 h-4" /> Save Menu
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
