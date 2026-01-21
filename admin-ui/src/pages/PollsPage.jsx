import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Plus, Pencil, Trash2 } from "lucide-react";
import apiClient from "../services/apiClient";
import { toast } from "sonner";
import Select from "react-select";
import { useConfirm } from "../hooks/useConfirm";
import { usePermission } from "../hooks/usePermission";

const Card = ({ children, className = "", ...props }) => (
  <div
    className={`bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow ${className}`}
    {...props}
  >
    {children}
  </div>
);

const CardContent = ({ children, className = "" }) => (
  <div className={`p-5 ${className}`}>{children}</div>
);

const QUESTION_TYPES = [
  { value: "text", label: "Text" },
  { value: "yesno", label: "Yes / No" },
  { value: "star", label: "Star Rating" },
  { value: "emoji", label: "Emoji" },
  { value: "slider", label: "Slider" },
  { value: "thumbs", label: "Thumbs Up / Down" },
];

export default function PollsPage() {
  const [polls, setPolls] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editPoll, setEditPoll] = useState(null);
  const [divisions, setDivisions] = useState([]);

  const [formData, setFormData] = useState({
    title: "",
    start_time: "",
    end_time: "",
    is_active: false,
    questions: [{ question: "", type: "text", options: [""] }],
    division_list: [],
  });

  const { confirm, ConfirmDialog } = useConfirm();
  const { can,has } = usePermission();

  // ---------------- FETCH POLLS ----------------
  const fetchPolls = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get("/polls");
      setPolls(res?.polls || []);
    } catch (err) {
      console.error("Error fetching polls:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDivisions = async () => {
    try {
      const res = await apiClient.get("/divisions");
      const data = res.data?.data || res.data || [];

      console.log(data);
      setDivisions(
        data.map((div) => ({
          value: div.name || div.division_name || div.id,
          label: div.name || div.division_name || `Division ${div.id}`,
          id: div.id,
        }))
      );
    } catch {
      toast.error("Failed to fetch divisions");
    }
  };

  useEffect(() => {
    fetchPolls();
    fetchDivisions();
  }, []);

  // ---------------- INPUT HANDLERS ----------------
  const handleInputChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleQuestionChange = (index, field, value) => {
    const updated = [...formData.questions];
    const current = { ...updated[index], [field]: value };

    // Auto-set options based on type
    if (field === "type") {
      if (value === "thumbs") {
        current.options = ["👍", "👎"];
      } else if (value === "yesno") {
        current.options = ["Yes", "No"];
      } else if (value === "emoji") {
        current.options = [""];
      } else if (value === "text") {
        current.options = [""];
      } else if (value === "slider") {
        current.slider_min = 0;
        current.slider_max = 10;
      } else if (value === "star") {
        current.max_stars = 5;
      }
    }

    updated[index] = current;
    setFormData({ ...formData, questions: updated });
  };

  const handleOptionChange = (qIndex, oIndex, value) => {
    const updated = [...formData.questions];
    const opts = [...(updated[qIndex].options || [])];
    opts[oIndex] = value;
    updated[qIndex].options = opts;
    setFormData({ ...formData, questions: updated });
  };

  const addQuestion = () => {
    setFormData({
      ...formData,
      questions: [...formData.questions, { question: "", type: "text", options: [""] }],
    });
  };

  const addOption = (qIndex) => {
    const updated = [...formData.questions];
    updated[qIndex].options = [...(updated[qIndex].options || []), ""];
    setFormData({ ...formData, questions: updated });
  };

  const removeOption = (qIndex, oIndex) => {
    const updated = [...formData.questions];
    const opts = [...(updated[qIndex].options || [])];
    opts.splice(oIndex, 1);
    updated[qIndex].options = opts.length ? opts : [""];
    setFormData({ ...formData, questions: updated });
  };

  const resetForm = () => {
    setFormData({
      title: "",
      start_time: "",
      end_time: "",
      is_active: false,
      division_list: [],
      questions: [{ question: "", type: "text", options: [""] }],
    });
    setEditPoll(null);
  };

  // const handleCreatePoll = async () => {
  //   if (!has("polls-create")) {
  //     toast.error("You don't have permission to create polls.");
  //     return; // Stop the operation if no permission
  //   }

  //   if (!formData.title) return alert("Title is required!");

  //   const payload = {
  //     title: formData.title,
  //     start_time: formData.start_time,
  //     end_time: formData.end_time,
  //     is_active: formData.is_active,
  //     division_list: formData?.division_list?.map((d) => d.value),
  //     questions: formData.questions.map((q) => {
  //       const base = { type: q.type, question: q.question };

  //       switch (q.type) {
  //         case "emoji":
  //           return { ...base, options: q.options.filter((opt) => opt?.trim()) };

  //         case "slider":
  //           return {
  //             ...base,
  //             slider_min: q.slider_min ?? 0,
  //             slider_max: q.slider_max ?? 10,
  //           };

  //         case "yesno":
  //           return { ...base, options: ["Yes", "No"] };

  //         case "thumbs":
  //           return { ...base, options: ["👍", "👎"] };

  //         case "star":
  //           return { ...base, max_stars: 5 };

  //         case "text":
  //         default:
  //           return { ...base, options: [""] };
  //       }
  //     }),
  //   };
  //   setLoading(true);
  //   try {
  //     await apiClient.post("/poll/create", payload);
  //     toast.success("Poll created successfully!");
  //     setShowModal(false);
  //     fetchPolls();
  //   } catch (err) {
  //     console.log("Error creating poll:", err);
  //     toast.error(err?.response?.data?.message);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const handleCreatePoll = async () => {
    if (!can("polls-create")) {
      toast.error("You don't have permission to create polls.");
      return;
    }

    // --- Basic field validation ---
    if (!formData.title?.trim()) {
      toast.error("Poll title is required!");
      return;
    }

    if (!formData.start_time || !formData.end_time) {
      toast.error("Start and end time are required!");
      return;
    }

    if (!Array.isArray(formData.questions) || formData.questions.length === 0) {
      toast.error("At least one question is required!");
      return;
    }

    // --- Validate each question ---
    for (let i = 0; i < formData.questions.length; i++) {
      const q = formData.questions[i];
      const index = i + 1;

      if (!q.question?.trim()) {
        toast.error(`Question #${index} text is required!`);
        return;
      }

      if (!q.type) {
        toast.error(`Question #${index} type is required!`);
        return;
      }

      switch (q.type) {
        case "emoji":
          if (!Array.isArray(q.options) || q.options.filter((opt) => opt?.trim()).length < 2) {
            toast.error(`Question #${index}: at least two emoji options are required!`);
            return;
          }
          break;

        case "slider":
          if (
            typeof q.slider_min !== "number" ||
            typeof q.slider_max !== "number" ||
            q.slider_min >= q.slider_max
          ) {
            toast.error(`Question #${index}: slider_min must be less than slider_max!`);
            return;
          }
          break;

        case "yesno":
        case "thumbs":
        case "star":
        case "text":
          // No further validation needed
          break;

        default:
          toast.error(`Question #${index}: invalid question type "${q.type}"!`);
          return;
      }
    }

    // --- Build payload ---
    const payload = {
      title: formData.title.trim(),
      start_time: formData.start_time,
      end_time: formData.end_time,
      is_active: formData.is_active,
      division_list: formData?.division_list?.map((d) => d.value) || [],
      questions: formData.questions.map((q) => {
        const base = { type: q.type, question: q.question.trim() };

        switch (q.type) {
          case "emoji":
            return { ...base, options: q.options.filter((opt) => opt?.trim()) };
          case "slider":
            return {
              ...base,
              slider_min: q.slider_min ?? 0,
              slider_max: q.slider_max ?? 10,
            };
          case "yesno":
            return { ...base, options: ["Yes", "No"] };
          case "thumbs":
            return { ...base, options: ["👍", "👎"] };
          case "star":
            return { ...base, max_stars: 5 };
          case "text":
          default:
            return { ...base, options: [""] };
        }
      }),
    };

    // --- API call ---
    setLoading(true);
    try {
      await apiClient.post("/poll/create", payload);
      toast.success("Poll created successfully!");
      setShowModal(false);
      fetchPolls();
    } catch (err) {
      console.error("Error creating poll:", err);
      toast.error(err?.response?.data?.message || "Failed to create poll");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- UPDATE POLL ----------------
  // const handleUpdatePoll = async () => {
  //   if (!formData.title) return alert("Title is required!");

  //   const payload = {
  //     ...formData,
  //     division_list: formData?.division_list?.map((d) => d.value),
  //     questions: formData.questions.map((q) => ({
  //       question: q.question,
  //       type: q.type,
  //       options: q.options?.filter((opt) => opt?.trim()) || [""],
  //       ...(q.type === "slider" && {
  //         slider_min: q.slider_min ?? 0,
  //         slider_max: q.slider_max ?? 10,
  //       }),
  //       ...(q.type === "star" && { max_stars: 5 }),
  //     })),
  //   };
  //   setLoading(true);
  //   try {
  //     const res = await apiClient.put(`/admin/poll/${editPoll.id}`, payload);
  //     toast.success("Poll updated successfully!");
  //     setShowModal(false);
  //     fetchPolls();
  //   } catch (err) {
  //     console.error("Error updating poll:", err);
  //     toast.error(err?.response?.data?.message);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const handleUpdatePoll = async () => {
    if (!can("polls-update")) {
      toast.error("You don't have permission to update polls.");
      return;
    }

    if (!formData.title?.trim()) {
      toast.error("Poll title is required!");
      return;
    }

    if (!formData.start_time || !formData.end_time) {
      toast.error("Start and end time are required!");
      return;
    }

    if (!Array.isArray(formData.questions) || formData.questions.length === 0) {
      toast.error("At least one question is required!");
      return;
    }

    // --- Validate each question ---
    for (let i = 0; i < formData.questions.length; i++) {
      const q = formData.questions[i];
      const index = i + 1;

      if (!q.question?.trim()) {
        toast.error(`Question #${index} text is required!`);
        return;
      }

      if (!q.type) {
        toast.error(`Question #${index} type is required!`);
        return;
      }

      if (
        q.type === "emoji" &&
        (!Array.isArray(q.options) || q.options.filter((opt) => opt?.trim()).length < 2)
      ) {
        toast.error(`Question #${index}: at least two emoji options are required!`);
        return;
      }

      if (q.type === "slider") {
        if (
          typeof q.slider_min !== "number" ||
          typeof q.slider_max !== "number" ||
          q.slider_min >= q.slider_max
        ) {
          toast.error(`Question #${index}: slider_min must be less than slider_max!`);
          return;
        }
      }
    }

    // --- Build payload ---
    const payload = {
      ...formData,
      title: formData.title.trim(),
      division_list: formData?.division_list?.map((d) => d.value) || [],
      questions: formData.questions.map((q) => ({
        question: q.question.trim(),
        type: q.type,
        options: q.options?.filter((opt) => opt?.trim()) || [""],
        ...(q.type === "slider" && {
          slider_min: q.slider_min ?? 0,
          slider_max: q.slider_max ?? 10,
        }),
        ...(q.type === "star" && { max_stars: 5 }),
      })),
    };

    // --- API call ---
    setLoading(true);
    try {
      await apiClient.put(`/admin/poll/${editPoll.id}`, payload);
      toast.success("Poll updated successfully!");
      setShowModal(false);
      fetchPolls();
    } catch (err) {
      console.error("Error updating poll:", err);
      toast.error(err?.response?.data?.message || "Failed to update poll");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (pollId) => {
    if (!has("polls-delete")) {
      toast.error("You don't have permission to delete polls.");
      return; // Stop the operation if no permission
    }

    const userConfirmed = await confirm({
      title: "Delete Advertisement",
      message: `Are you sure you want to delete poll? This action cannot be undone.`,
    });

    if (!userConfirmed) return;

    setLoading(true);
    try {
      await apiClient.delete(`/admin/poll/${pollId}`);
      toast.success("Poll deleted successfully!");
      // fetchPolls();

      setPolls((prev) => prev.filter((poll) => poll.id !== pollId));
    } catch (err) {
      console.error("Error deleting poll:", err);
      toast.error("Something went wrong while deleting the poll.");
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (poll) => {
    if (!has("polls-update")) {
      toast.error("You don't have permission to update polls.");
      return; // Stop the operation if no permission
    }

    setEditPoll(poll);
    const start = poll.start_time ? poll.start_time.slice(0, 16) : "";
    const end = poll.end_time ? poll.end_time.slice(0, 16) : "";

    const normalizedQuestions = (poll.questions || []).map((q) => ({
      question: q.question || "",
      type: q.type || "text",
      options: q.options && q.options.length ? q.options : [""],
      slider_min: q.slider_min ?? 0,
      slider_max: q.slider_max ?? 10,
    }));

    setFormData({
      title: poll.title,
      start_time: start,
      end_time: end,
      is_active: poll.is_active,
      division_list: Array.isArray(poll.division_list)
        ? poll.division_list.map((div) => ({
            value: div,
            label: div,
          }))
        : [],
      questions: normalizedQuestions,
    });
    setShowModal(true);
  };

  // ---------------- TOGGLE ACTIVE ----------------
  const toggleActiveStatus = async (poll) => {
    if (!has("polls-update")) {
      toast.error("You don't have permission to update polls.");
      return; // Stop the operation if no permission
    }
    setLoading(true);
    try {
      const updatedStatus = !poll.is_active;

      await apiClient.put(`/admin/poll/${poll.id}`, {
        is_active: updatedStatus,
      });
      setPolls((prev) =>
        prev.map((p) => (p.id === poll.id ? { ...p, is_active: updatedStatus } : p))
      );
    } catch (err) {
      toast.error(err?.response?.data?.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">📊 Poll Management</h1>
        <button
          onClick={() => {
            resetForm();
            setShowModal(true);
          }}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-5 h-5" /> Create Poll
        </button>
      </div>

      {/* Poll List */}
      {loading ? (
        <div className="text-center text-gray-500">Loading polls...</div>
      ) : polls.length === 0 ? (
        <div className="text-center text-gray-400">No polls available</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {polls.map((poll) => (
            <Card key={poll.id}>
              <CardContent>
                <div className="flex justify-between items-center mb-2">
                  <h2 className="font-bold text-lg">{poll.title}</h2>
                  <button
                    // onClick={() => toggleActiveStatus(poll)}
                    className={`flex items-center gap-1 px-2 py-1 rounded-lg text-sm ${
                      poll.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {poll.is_active ? (
                      <>
                        <CheckCircle className="w-4 h-4" /> Active
                      </>
                    ) : (
                      <>
                        <XCircle className="w-4 h-4" /> Inactive
                      </>
                    )}
                  </button>
                </div>

                <div className="text-sm text-gray-600 mb-1">
                  <strong>Start:</strong> {new Date(poll.start_time).toLocaleString()}
                </div>
                <div className="text-sm text-gray-600 mb-1">
                  <strong>End:</strong> {new Date(poll.end_time).toLocaleString()}
                </div>

                {/* Poll Type */}
                <div className="text-sm text-gray-600 mb-1">
                  <strong>Type:</strong>{" "}
                  {poll.poll_type === "division_poll" ? "Division Poll" : "General Poll"}
                </div>

                {/* Divisions (if applicable) */}
                {poll.poll_type === "division_poll" && poll.division_list?.length > 0 && (
                  <div className="text-sm text-gray-600 mb-1">
                    <strong>Divisions:</strong> {poll.division_list.join(", ")}
                  </div>
                )}

                <div className="flex justify-between items-center mt-4 text-sm">
                  <button
                    onClick={() => handleEdit(poll)}
                    className="flex items-center gap-1 text-blue-600 hover:text-blue-800"
                  >
                    <Pencil className="w-4 h-4" /> Edit
                  </button>
                  <button
                    onClick={() => handleDelete(poll.id)}
                    className="flex items-center gap-1 text-red-600 hover:text-red-800"
                  >
                    <Trash2 className="w-4 h-4" /> Delete
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* ---------------- MODAL ---------------- */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-semibold mb-4">{editPoll ? "Edit Poll" : "Create Poll"}</h2>

            <div className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange("title", e.target.value)}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>

              {/* 🧩 Hide Divisions when type = on_chatbot_launch */}

              <label className="block mb-4 text-sm font-medium text-gray-700">
                Divisions
                <Select
                  isMulti
                  options={divisions}
                  value={formData?.division_list}
                  onChange={(value) =>
                    setFormData({
                      ...formData,
                      division_list: value,
                    })
                  }
                  className="mt-1"
                />
              </label>

              {/* Time */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Start Time</label>
                  <input
                    type="datetime-local"
                    value={formData.start_time}
                    onChange={(e) => handleInputChange("start_time", e.target.value)}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">End Time</label>
                  <input
                    type="datetime-local"
                    value={formData.end_time}
                    onChange={(e) => handleInputChange("end_time", e.target.value)}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
              </div>

              {/* Active toggle */}
              <div className="flex items-center gap-3">
                <label className="text-sm font-medium">Active:</label>
                <button
                  onClick={() =>
                    setFormData({
                      ...formData,
                      is_active: !formData.is_active,
                    })
                  }
                  className={`px-4 py-1 rounded-full text-sm ${
                    formData.is_active ? "bg-green-200 text-green-700" : "bg-gray-200 text-gray-700"
                  }`}
                >
                  {formData.is_active ? "Active" : "Inactive"}
                </button>
              </div>

              {/* Questions */}
              <div className="space-y-6">
                {formData.questions.map((q, qIndex) => (
                  <div key={qIndex} className="border rounded-lg p-4 bg-gray-50 shadow-sm relative">
                    <button
                      onClick={() => {
                        if (window.confirm(`Delete Question ${qIndex + 1}?`)) {
                          const updated = [...formData.questions];
                          updated.splice(qIndex, 1);
                          setFormData({ ...formData, questions: updated });
                        }
                      }}
                      className="absolute top-2 right-2 text-red-500 hover:text-red-700"
                    >
                      🗑
                    </button>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                      <div className="md:col-span-2">
                        <label className="block font-medium mb-2">Question {qIndex + 1}</label>
                        <input
                          type="text"
                          value={q.question}
                          onChange={(e) => handleQuestionChange(qIndex, "question", e.target.value)}
                          className="w-full border rounded-lg px-3 py-2"
                          placeholder="Enter question"
                        />
                      </div>

                      <div>
                        <label className="block font-medium mb-2">Type</label>
                        <select
                          value={q.type}
                          onChange={(e) => handleQuestionChange(qIndex, "type", e.target.value)}
                          className="w-full border rounded-lg px-3 py-2"
                        >
                          {QUESTION_TYPES.map((t) => (
                            <option key={t.value} value={t.value}>
                              {t.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {/* Type-specific fields */}
                    {q.type === "emoji" && (
                      <div className="mb-2">
                        <label className="block text-sm font-medium mb-2">Emoji Options</label>
                        {(q.options || []).map((opt, oIndex) => (
                          <div key={oIndex} className="flex gap-2 mb-2">
                            <input
                              type="text"
                              value={opt}
                              onChange={(e) => handleOptionChange(qIndex, oIndex, e.target.value)}
                              className="flex-1 border rounded-lg px-3 py-2"
                              placeholder={`Emoji ${oIndex + 1} (e.g. 😄)`}
                            />
                            {(q.options || []).length > 1 && (
                              <button
                                onClick={() => removeOption(qIndex, oIndex)}
                                className="text-red-500 hover:text-red-700 font-bold"
                              >
                                ✕
                              </button>
                            )}
                          </div>
                        ))}
                        <button onClick={() => addOption(qIndex)} className="text-blue-600 text-sm">
                          + Add Emoji
                        </button>
                      </div>
                    )}

                    {q.type === "slider" && (
                      <div className="flex gap-3 items-center">
                        <div>
                          <label className="block text-sm font-medium">Min</label>
                          <input
                            type="number"
                            value={q.slider_min ?? 0}
                            min={0}
                            onChange={(e) =>
                              handleQuestionChange(qIndex, "slider_min", Number(e.target.value))
                            }
                            className="w-full border rounded-lg px-3 py-2"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium">Max</label>
                          <input
                            type="number"
                            value={q.slider_max ?? 10}
                            max={10}
                            onChange={(e) =>
                              handleQuestionChange(qIndex, "slider_max", Number(e.target.value))
                            }
                            className="w-full border rounded-lg px-3 py-2"
                          />
                        </div>
                        <div className="flex-1 text-sm text-gray-600 mt-6">
                          Range <strong>{q.slider_min}</strong>– <strong>{q.slider_max}</strong>
                        </div>
                      </div>
                    )}

                    {q.type === "star" && (
                      <div className="text-sm text-gray-600">⭐ 5-star rating will be shown.</div>
                    )}

                    {q.type === "yesno" && (
                      <div className="text-sm text-gray-600">Yes / No options are auto-added.</div>
                    )}

                    {q.type === "thumbs" && (
                      <div className="text-sm text-gray-600">👍 / 👎 options are auto-added.</div>
                    )}
                  </div>
                ))}

                <button onClick={addQuestion} className="text-blue-600 text-sm font-medium">
                  + Add Question
                </button>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowModal(false);
                  resetForm();
                }}
                className="px-4 py-2 rounded-lg border"
              >
                Cancel
              </button>
              <button
                onClick={editPoll ? handleUpdatePoll : handleCreatePoll}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                {editPoll ? "Update Poll" : "Create Poll"}
              </button>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog />
    </div>
  );
}
