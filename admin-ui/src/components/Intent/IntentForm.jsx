import React, { useState, useEffect, useRef } from "react";
import { Plus, Trash2, ChevronLeft, Check } from "lucide-react";

export default function IntentForm({
  intents: intentsProp,
  setIntents,
  onBack,
  onSave,
  embedded = false,
}) {
  const [errors, setErrors] = useState({});
  const warned = useRef(false);

  const safeIntents = Array.isArray(intentsProp)
    ? intentsProp
    : intentsProp && Array.isArray(intentsProp.intents)
    ? intentsProp.intents
    : [];

  useEffect(() => {
    if (!Array.isArray(intentsProp) && !warned.current) {
      console.warn("IntentForm: expected `intents` to be an array but received:", intentsProp);
      warned.current = true;
    }

    // ✅ Initialize first intent if empty
    if (safeIntents.length === 0 && typeof setIntents === "function") {
      setIntents([
        {
          tempId: Date.now().toString(),
          name: "",
          response_type: "dynamic",
          actions: [{ name: "" }],
          utters: [{ name: "", response: "" }],
          examples: [{ example: "" }],
        },
      ]);
    }
  }, [intentsProp, setIntents]);

  // ✅ Validation rules
  const validate = () => {
    const newErrors = {};
    safeIntents.forEach((intent) => {
      const err = {};
      const examples = intent.examples || [];

      if (!String(intent.name || "").trim()) err.name = "Intent name is required.";
      if (examples.filter((e) => (e.example || "").trim() !== "").length < 2)
        err.examples = "At least 2 examples are required.";

      if (intent.response_type === "dynamic") {
        const actions = intent.actions || [];
        if (!actions.some((a) => (a.name || "").trim() !== ""))
          err.actions = "Add at least one action.";
      } else {
        const utters = intent.utters || [];
        if (!utters.some((u) => u.name.trim() && u.response.trim()))
          err.utters = "Add at least one utter with name and response.";
      }

      if (Object.keys(err).length > 0) newErrors[intent.tempId] = err;
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const addIntent = () => {
    const newIntent = {
      tempId: Date.now().toString(),
      name: "",
      response_type: "dynamic",
      actions: [{ name: "" }],
      utters: [{ name: "", response: "" }],
      examples: [{ example: "" }],
    };
    if (typeof setIntents === "function") setIntents([...safeIntents, newIntent]);
  };

  const updateField = (tempId, field, value) => {
    if (typeof setIntents !== "function") return;
    setIntents(
      safeIntents.map((i) => {
        if (i.tempId === tempId && field === "response_type") {
          return {
            ...i,
            response_type: value,
            utters:
              value === "static"
                ? i.utters && i.utters.length > 0
                  ? i.utters
                  : [{ name: "", response: "" }]
                : i.utters,
          };
        }
        return i.tempId === tempId ? { ...i, [field]: value } : i;
      })
    );
  };

  const addNested = (tempId, field, newValue) => {
    if (typeof setIntents !== "function") return;
    setIntents(
      safeIntents.map((i) =>
        i.tempId === tempId
          ? {
              ...i,
              [field]: Array.isArray(i[field]) ? [...i[field], newValue] : [newValue],
            }
          : i
      )
    );
  };

  const updateNested = (tempId, field, idx, value, key = null) => {
    if (typeof setIntents !== "function") return;
    setIntents(
      safeIntents.map((i) =>
        i.tempId === tempId
          ? {
              ...i,
              [field]: (i[field] || []).map((v, i2) =>
                i2 === idx ? (key ? { ...v, [key]: value } : value) : v
              ),
            }
          : i
      )
    );
  };

  const updateUtterField = (tempId, idx, key, value) => {
    if (typeof setIntents !== "function") return;

    setIntents(
      safeIntents.map((i) => {
        if (i.tempId !== tempId) return i;

        const updatedUtters = (i.utters || []).map((u, i2) => {
          if (i2 !== idx) return u;

          if (key === "name") {
            const trimmed = value.trim().replace(/\s+/g, "_");
            let finalName = trimmed;
            if (trimmed && !trimmed.toLowerCase().startsWith("utter_")) {
              finalName = "utter_" + trimmed.replace(/^utter_+/i, "");
            }
            return { ...u, name: finalName };
          }

          return { ...u, [key]: value };
        });

        return { ...i, utters: updatedUtters };
      })
    );
  };

  const updateActionField = (tempId, idx, value) => {
    if (typeof setIntents !== "function") return;

    setIntents(
      safeIntents.map((i) => {
        if (i.tempId !== tempId) return i;

        const updatedActions = (i.actions || []).map((a, i2) => {
          if (i2 !== idx) return a;

          const trimmed = value.trim().replace(/\s+/g, "_");
          let finalValue = trimmed;
          if (trimmed && !trimmed.toLowerCase().startsWith("action_")) {
            finalValue = "action_" + trimmed.replace(/^action_+/i, "");
          }
          return { ...a, name: finalValue };
        });

        return { ...i, actions: updatedActions };
      })
    );
  };

  const deleteNested = (tempId, field, idx) => {
    if (typeof setIntents !== "function") return;
    setIntents(
      safeIntents.map((i) =>
        i.tempId === tempId ? { ...i, [field]: (i[field] || []).filter((_, i2) => i2 !== idx) } : i
      )
    );
  };

  const deleteIntent = (tempId) => {
    if (safeIntents.length === 1) return alert("At least one intent is required.");
    if (typeof setIntents === "function")
      setIntents(safeIntents.filter((i) => i.tempId !== tempId));
  };

  const handleSave = () => {
    if (validate()) {
      if (typeof onSave === "function") onSave(safeIntents);
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <div className={`space-y-6 ${embedded ? "pt-2" : ""}`}>
      {!embedded && (
        <h2 className="text-xl font-semibold text-gray-800 mb-2">🧠 Intent Configuration</h2>
      )}

      {safeIntents.map((intent, idx) => {
        const error = errors[intent.tempId] || {};
        const isStatic = intent.response_type === "static";

        return (
          <div
            key={intent.tempId}
            className={`border rounded-xl shadow-sm p-5 transition ${
              embedded ? "bg-gray-50 border-gray-200" : "bg-white border-gray-300 hover:shadow-md"
            }`}
          >
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-gray-700 font-semibold text-lg">Intent #{idx + 1}</h3>
              <button
                onClick={() => deleteIntent(intent.tempId)}
                className="text-red-500 hover:text-red-700"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              {/* Intent Name */}
              <input
                type="text"
                value={intent.name || ""}
                onChange={(e) => updateField(intent.tempId, "name", e.target.value)}
                placeholder="Intent Name"
                className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 ${
                  error.name ? "border-red-400" : "border-gray-300"
                }`}
              />
              {error.name && <p className="text-sm text-red-500">{error.name}</p>}

              {/* Response Type Selector */}
              <div className="flex items-center gap-4 mt-3">
                <label className="text-sm font-medium text-gray-700">Response Type:</label>
                <select
                  value={intent.response_type}
                  onChange={(e) => updateField(intent.tempId, "response_type", e.target.value)}
                  className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="dynamic">Dynamic (Actions)</option>
                  <option value="static">Static (Utters)</option>
                </select>
              </div>

              {/* Actions */}
              {!isStatic && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Actions:</label>
                  {(intent.actions || []).map((a, i) => (
                    <div key={i} className="flex gap-2 mt-2">
                      <input
                        type="text"
                        value={a.name || ""}
                        onChange={(e) => updateActionField(intent.tempId, i, e.target.value)}
                        placeholder="Enter action"
                        className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        onClick={() => deleteNested(intent.tempId, "actions", i)}
                        className="text-red-500"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  {error.actions && <p className="text-sm text-red-500">{error.actions}</p>}
                  <button
                    onClick={() => addNested(intent.tempId, "actions", { name: "" })}
                    className="mt-2 text-blue-600 text-sm flex items-center gap-1 hover:underline"
                  >
                    <Plus className="w-4 h-4" /> Add Action
                  </button>
                </div>
              )}

              {/* Utters */}
              {isStatic && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Utters:</label>
                  {(intent.utters || []).map((utter, i) => (
                    <div key={i} className="flex gap-2 mt-2">
                      <input
                        type="text"
                        value={utter.name}
                        onChange={(e) => updateUtterField(intent.tempId, i, "name", e.target.value)}
                        placeholder="Utter name (e.g., greet)"
                        className="border border-gray-300 rounded-lg px-3 py-2 w-1/3 focus:ring-2 focus:ring-blue-500"
                      />
                      <input
                        type="text"
                        value={utter.response}
                        onChange={(e) =>
                          updateUtterField(intent.tempId, i, "response", e.target.value)
                        }
                        placeholder="Response text"
                        className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        onClick={() => deleteNested(intent.tempId, "utters", i)}
                        className="text-red-500"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  {error.utters && <p className="text-sm text-red-500">{error.utters}</p>}
                  <button
                    onClick={() => addNested(intent.tempId, "utters", { name: "", response: "" })}
                    className="mt-2 text-blue-600 text-sm flex items-center gap-1 hover:underline"
                  >
                    <Plus className="w-4 h-4" /> Add Utter
                  </button>
                </div>
              )}

              {/* Examples */}
              <div className="pt-2">
                <label className="text-sm font-medium text-gray-700">Examples (min 2):</label>
                {(intent.examples || []).map((ex, i) => (
                  <div key={i} className="flex gap-2 mt-2">
                    <input
                      type="text"
                      value={ex.example || ""}
                      onChange={(e) =>
                        updateNested(intent.tempId, "examples", i, e.target.value, "example")
                      }
                      placeholder={`Example #${i + 1}`}
                      className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={() => deleteNested(intent.tempId, "examples", i)}
                      className="text-red-500"
                    >
                      ✕
                    </button>
                  </div>
                ))}
                {error.examples && <p className="text-sm text-red-500">{error.examples}</p>}
                <button
                  onClick={() => addNested(intent.tempId, "examples", { example: "" })}
                  className="mt-2 text-blue-600 text-sm flex items-center gap-1 hover:underline"
                >
                  <Plus className="w-4 h-4" /> Add Example
                </button>
              </div>
            </div>
          </div>
        );
      })}

      {!embedded && (
        <div className="flex justify-between items-center pt-6 border-t">
          <button
            onClick={addIntent}
            className="flex items-center gap-2 text-blue-600 hover:underline"
          >
            <Plus className="w-4 h-4" /> Add New Intent
          </button>

          <div className="flex gap-3">
            <button
              onClick={onBack}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100"
            >
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              <Check className="w-4 h-4" /> Save Menu & Intents
            </button>
          </div>
        </div>
      )}

      {embedded && (
        <button
          onClick={addIntent}
          className="mt-3 text-blue-600 text-sm flex items-center gap-1 hover:underline"
        >
          <Plus className="w-4 h-4" /> Add Another Intent
        </button>
      )}
    </div>
  );
}
