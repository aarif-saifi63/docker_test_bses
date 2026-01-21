import React, { useEffect, useState } from "react";
import apiClient from "../services/apiClient";
import { Pencil, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { usePermission } from "../hooks/usePermission";

export default function FeedbackQuestions() {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newQuestion, setNewQuestion] = useState("");
  const [newOptions, setNewOptions] = useState("");
  const [language, setLanguage] = useState("English");
  const [statusMessage, setStatusMessage] = useState("");
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editOptionsString, setEditOptionsString] = useState("");
  const {has}= usePermission();

  const [editQuestionData, setEditQuestionData] = useState({
    id: "",
    question: "",
    options: [],
  });

  const detectLanguage = (text) => {
    const hindiRegex = /[\u0900-\u097F]/;
    return hindiRegex.test(text) ? "Hindi" : "English";
  };

  // Fetch questions
  const fetchQuestions = async (lang = "English") => {
    try {
      setLoading(true);
      setStatusMessage("");
      const res = await apiClient.get(`/feedback/get-questions?question_type=${lang}`);
      setQuestions(res?.data || []);
    } catch (err) {
      console.error("Error fetching questions:", err);
      toast.error(err?.response?.data?.message||"Failed to fetch questions ❌");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestions(language);
  }, [language]);

  // Add new question
  const addQuestion = async () => {
    if (!has("feedbacks-create")) {
      toast.error("You don't have permission to create feedback questions.");
      return; // Stop the operation if no permission
    }

    if (!newQuestion.trim()) {
      alert("Please enter a question");
      return;
    }

    const payload = {
      question: newQuestion,
      question_type: detectLanguage(newQuestion),
      options: newOptions ? newOptions.split(",").map((opt) => opt.trim()) : [],
    };

    try {
      setLoading(true);
      const res = await apiClient.post("/feedback/add", payload, {
        headers: { "Content-Type": "application/json" },
      });
      setStatusMessage(res?.message || "Question added successfully ✅");
      setNewQuestion("");
      setNewOptions("");
      fetchQuestions(language);
    } catch (err) {
      console.error("Error adding question:", err);
      toast.error(err?.response?.data?.message||"Failed to add question ❌");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveQuestion = async () => {
    const questionText = editQuestionData?.question?.trim();

    if (!questionText) {
      toast.error("Question text is required!");
      return;
    }

    // Convert options string to array
    const updatedOptions = editOptionsString
      ? editOptionsString
          .split(",")
          .map((opt) => opt.trim())
          .filter((opt) => opt.length > 0)
      : [];

    // Determine question type based on text
    const detectedType = detectLanguage(questionText) || "text";

    // Validation for multiple-choice or similar types
    if (["multiple_choice", "select", "radio"].includes(detectedType)) {
      if (updatedOptions.length < 2) {
        toast.error("At least two options are required for multiple-choice questions!");
        return;
      }
    }

    // Even for other types, validate if user entered comma but no valid options
    if (editOptionsString && updatedOptions.length === 0) {
      toast.error("Please enter valid options (non-empty values).");
      return;
    }

    try {
      setLoading(true);

      const res = await apiClient.put(`/feedback/update/${editQuestionData.id}`, {
        question: questionText,
        question_type: detectedType,
        options: updatedOptions,
      });

      setStatusMessage(res?.message || "Question updated successfully ✅");
      setEditModalOpen(false);
      fetchQuestions(language);
    } catch (err) {
      console.error("Error updating question:", err);
      toast.error(err.response?.data?.message || "Failed to update question ❌");
      setStatusMessage("Failed to update question ❌");
    } finally {
      setLoading(false);
    }
  };

  const deleteQuestion = async (id) => {
    if (!window.confirm("Are you sure you want to delete this question?")) return;

    if (!has("feedbacks-delete")) {
      toast.error("You don't have permission to delete feedback questions.");
      return; // Stop the operation if no permission
    }

    try {
      setLoading(true);
      const res = await apiClient.delete(`/feedback/delete/${id}`);
      toast.success(res?.message || "Question deleted successfully ✅");
      fetchQuestions(language);
    } catch (err) {
      console.error("Error deleting question:", err);
      toast.error(message || "Failed to delete question ❌");
    } finally {
      setLoading(false);
    }
  };

  const openEditModal = (id, question, options) => {
    if (!has("feedbacks-update")) {
      toast.error("You don't have permission to update feedback questions.");
      return; // Stop the operation if no permission
    }

    setEditQuestionData({ id, question, options });
    setEditOptionsString(options.join(", ")); // initialize string
    setEditModalOpen(true);
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Feedback Questions</h2>

      {/* Language toggle */}
      <div className="flex gap-3 mb-4">
        <button
          onClick={() => setLanguage("English")}
          className={`px-4 py-2 rounded ${
            language === "English" ? "bg-blue-600 text-white" : "bg-gray-200"
          }`}
        >
          English
        </button>
        <button
          onClick={() => setLanguage("Hindi")}
          className={`px-4 py-2 rounded ${
            language === "Hindi" ? "bg-blue-600 text-white" : "bg-gray-200"
          }`}
        >
          Hindi
        </button>
      </div>

      {/* Status message */}
      {statusMessage && <p className="mb-4 text-xl font-medium text-gray-700">{statusMessage}</p>}

      {/* Loading */}
      {loading && <p className="mb-4 text-sm text-gray-500">Loading...</p>}

      {/* Questions List */}
      <div className="space-y-4 mb-6">
        {questions.map((q) => (
          <div
            key={q.id}
            className="border p-4 rounded shadow-sm bg-white flex justify-between items-start"
          >
            <div>
              <p className="font-semibold">{q.question}</p>
              {q.options.length > 0 ? (
                <ul className="list-disc list-inside text-sm mt-1">
                  {q.options.map((opt, idx) => (
                    <li key={idx}>{opt}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500 mt-1">No options</p>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex gap-2 ml-4">
              <button
                className="p-2 text-blue-600 hover:bg-blue-100 rounded"
                onClick={() => openEditModal(q.id, q.question, q.options)}
              >
                <Pencil size={18} />
              </button>

              <button
                className="p-2 text-red-600 hover:bg-red-100 rounded"
                onClick={() => deleteQuestion(q.id)}
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Modal - Moved outside the map loop */}
      {editModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex justify-end z-50">
          <div className="bg-white w-96 p-6 h-full shadow-lg overflow-auto">
            <h3 className="text-lg font-bold mb-4">Edit Question</h3>

            <label className="block mb-2">
              Question:
              <input
                type="text"
                value={editQuestionData.question}
                onChange={(e) =>
                  setEditQuestionData({
                    ...editQuestionData,
                    question: e.target.value,
                  })
                }
                className="w-full border p-2 rounded mt-1"
              />
            </label>

            <label className="block mb-4">
              Options (comma separated):
              <input
                type="text"
                value={editOptionsString}
                onChange={(e) => setEditOptionsString(e.target.value)}
                className="w-full border p-2 rounded mt-1"
              />
            </label>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setEditModalOpen(false)}
                className="px-4 py-2 bg-gray-300 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveQuestion}
                className="px-4 py-2 bg-blue-600 text-white rounded"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add New Question */}
      <div className="border p-4 rounded bg-gray-50 shadow">
        <h3 className="font-semibold mb-2">Add New Question</h3>

        <label className="block mb-2">
          Question:
          <input
            type="text"
            value={newQuestion}
            onChange={(e) => setNewQuestion(e.target.value)}
            className="w-full border p-2 rounded mt-1"
            placeholder="Enter question text"
          />
        </label>

        <label className="block mb-2">
          Options (comma separated):
          <input
            type="text"
            value={newOptions}
            onChange={(e) => setNewOptions(e.target.value)}
            className="w-full border p-2 rounded mt-1"
            placeholder="e.g. Yes, No, Maybe"
          />
        </label>

        <button onClick={addQuestion} className="mt-3 px-4 py-2 bg-blue-600 text-white rounded">
          Add Question
        </button>
      </div>
    </div>
  );
}