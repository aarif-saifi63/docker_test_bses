import { useState } from "react";

export function useConfirm() {
  const [open, setOpen] = useState(false);
  const [resolver, setResolver] = useState(null);
  const [message, setMessage] = useState("Are you sure?");
  const [title, setTitle] = useState("Confirm");

  const confirm = ({ title = "Confirm", message = "Are you sure?" } = {}) =>
    new Promise((resolve) => {
      setTitle(title);
      setMessage(message);
      setOpen(true);
      setResolver(() => resolve);
    });

  const handleClose = (result) => {
    setOpen(false);
    if (resolver) resolver(result);
  };

  const ConfirmDialog = () =>
    open ? (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
        <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">{title}</h2>
          <p className="text-sm text-gray-600 mb-6">{message}</p>
          <div className="flex justify-end gap-3">
            <button
              onClick={() => handleClose(false)}
              className="px-4 py-2 rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={() => handleClose(true)}
              className="px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    ) : null;

  return { confirm, ConfirmDialog };
}
