import React, { useState, useEffect } from "react";
import { ChevronRight, Layers3 } from "lucide-react";
import SubmenuForm from "./SubmenuForm";
import { toast } from "sonner";

export default function MenuModal({
  formData,
  onClose,
  onSave,
  onInputChange,
  editMode,
  rajdhaniUsers = [],
  user_id,
  loadingMenu,
}) {
  const [step, setStep] = useState(1);
  const [submenus, setSubmenus] = useState(formData.submenus || []);
  const [localUserId, setLocalUserId] = useState(user_id || null);

  // Automatically set language from selected user
  useEffect(() => {
    if (localUserId) {
      const selectedUser = rajdhaniUsers.find((u) => u.id === Number(localUserId));
      if (selectedUser && selectedUser.lang && selectedUser.lang !== formData.lang) {
        onInputChange("lang", selectedUser.lang);
      }
    }
  }, [localUserId, rajdhaniUsers, onInputChange, formData.lang]);

  // Initialize submenus if empty
  useEffect(() => {
    if (!formData.submenus || formData.submenus.length === 0) {
      setSubmenus([
        {
          tempId: Date.now().toString(),
          name: "",
          lang: formData.lang || "english",
          is_visible: true,
          intents: [
            {
              tempId: Date.now().toString() + "-i",
              name: "",
              actions: [""],
              examples: [""],
            },
          ],
        },
      ]);
    }
  }, [formData.submenus, formData.lang]);

  const handleNext = () => {
    if (!formData.name.trim()) return toast.error("Menu title is required!");
    if (!localUserId) return toast.error("Please select a Rajdhani user!");
    setStep(2);
  };

  const handleSaveFinal = (validatedSubmenus) => {
    const normalizedSubmenus = validatedSubmenus.map((s) => ({
      ...s,
      lang: s.lang || formData.lang,
    }));

    onSave({
      ...formData,
      submenus: normalizedSubmenus,
      user_id: localUserId,
    });
  };

  const selectedUser = rajdhaniUsers.find((u) => u.id === Number(localUserId));

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white shadow-2xl rounded-2xl w-full max-w-4xl flex flex-col max-h-[90vh]">
        {/* HEADER */}
        <div className="sticky top-0 bg-white z-10 border-b p-5 flex justify-between items-center rounded-t-2xl">
          <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
            <Layers3 className="w-5 h-5 text-blue-600" />
            {editMode ? "Edit Menu" : "Create Menu"}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition text-lg"
          >
            ✕
          </button>
        </div>

        {/* BODY */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {step === 1 && (
            <div className="space-y-5 animate-fadeIn">
              {/* Rajdhani User Dropdown */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rajdhani User
                </label>
                <select
                  value={localUserId || ""}
                  onChange={(e) => setLocalUserId(Number(e.target.value))}
                  className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 transition"
                >
                  <option value="">Select Rajdhani User</option>
                  {rajdhaniUsers.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Language (Read-Only) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
                <input
                  type="text"
                  value={
                    selectedUser?.lang
                      ? selectedUser.lang === "hi"
                        ? "Hindi"
                        : "English"
                      : formData.lang === "hi"
                      ? "Hindi"
                      : "English"
                  }
                  readOnly
                  className="w-full border border-gray-200 bg-gray-100 rounded-lg px-3 py-2 text-gray-600 cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">
                  (Language is set automatically from the selected Rajdhani user)
                </p>
              </div>

              {/* Menu Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Menu Title</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => onInputChange("name", e.target.value)}
                  placeholder="Enter menu title (e.g., Main Menu)"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 transition"
                />
              </div>

              {/* Menu Icon Upload */}
              {/* <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Menu Icon</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => {
                    const file = e.target.files[0];
                    if (file && file.type.startsWith("image/")) {
                      onInputChange("icon_path", file);
                    } else {
                      onInputChange("icon_path", null);
                    }
                  }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 transition"
                />

                {formData.icon_path && (
                  <div className="mt-3">
                    <img
                      src={
                        formData.icon_path instanceof File
                          ? URL.createObjectURL(formData.icon_path)
                          : formData.icon_path
                      }
                      alt="Menu Icon Preview"
                      className="w-40 h-40 object-cover rounded-lg border"
                    />
                    <button
                      onClick={() => onInputChange("icon_path", null)}
                      className="mt-2 text-sm text-red-600 hover:text-red-800"
                    >
                      Remove Icon
                    </button>
                  </div>
                )}
              </div> */}
              
              {/* Menu Icon Upload (Secure for SVG XSS) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Menu Icon (PNG / JPEG / JPG / SVG)
                </label>
                <input
                  type="file"
                  accept=".png,.jpg,.jpeg,.svg"
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file) return onInputChange("icon_path", null);

                    const allowedTypes = ["image/png", "image/jpeg", "image/svg+xml"];
                    if (!allowedTypes.includes(file.type)) {
                      toast.error("Unsupported file type!");
                      e.target.value = "";
                      return;
                    }

                    // Scan SVG for XSS only if it's SVG
                    if (file.type === "image/svg+xml") {
                      const text = await file.text();
                      const lower = text.toLowerCase();

                      const badPatterns = [
                        /<script[\s\S]*?>/gi,
                        /\bon\w+=/gi,                        // onload/onerror/onmouseover...
                        /javascript:/gi,
                        /<foreignobject[\s\S]*?>/gi,
                        /<!entity/gi,
                        /<iframe/gi,
                        /<embed/gi,
                        /<object/gi,
                        /data:text\/html/gi,
                        /href=['"]javascript:/gi,
                      ];

                      if (badPatterns.some((p) => p.test(lower))) {
                        toast.error("❌ Malicious SVG detected! Upload blocked.");
                        e.target.value = "";
                        return;
                      }
                    }

                    onInputChange("icon_path", file);
                  }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 transition"
                />

                {formData.icon_path && (
                  <div className="mt-3">
                    <img
                      src={
                        formData.icon_path instanceof File
                          ? URL.createObjectURL(formData.icon_path)
                          : formData.icon_path
                      }
                      alt="Menu Icon Preview"
                      className="w-40 h-40 object-cover rounded-lg border"
                    />
                    <button
                      onClick={() => onInputChange("icon_path", null)}
                      className="mt-2 text-sm text-red-600 hover:text-red-800"
                    >
                      Remove Icon
                    </button>
                  </div>
                )}
              </div>


              {/* Active Status */}
              <div className="flex items-center gap-3">
                <label className="text-sm font-medium text-gray-700">Active Status:</label>
                <button
                  onClick={() => onInputChange("is_visible", !formData.is_visible)}
                  className={`px-5 py-1.5 rounded-full text-sm font-medium transition ${
                    formData.is_visible
                      ? "bg-green-100 text-green-700 border border-green-400"
                      : "bg-gray-100 text-gray-700 border border-gray-300"
                  }`}
                >
                  {formData.is_visible ? "Active" : "Inactive"}
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <SubmenuForm
              submenus={submenus}
              setSubmenus={setSubmenus}
              onBack={() => setStep(1)}
              onSave={handleSaveFinal}
              parentLang={formData.lang}
              selectedUserName={selectedUser?.name || ""}
              loadingMenu={loadingMenu}
            />
          )}
        </div>

        {/* FOOTER */}
        <div className="sticky bottom-0 bg-white border-t p-4 flex justify-end gap-3 rounded-b-2xl">
          {step === 1 && (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleNext}
                className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
