// import { useState } from "react";
// import { useTrainingStatus } from "../../hooks/useTrainingStatus";
// import apiClient from "../../services/apiClient";
// import { formatDateTime } from "../../utils/time";

// export default function TrainingStatusWidget() {
//   const { status, loading } = useTrainingStatus();
//   const [triggering, setTriggering] = useState(false);

//   //   console.log("Training status:", status);

//   if (!status) return;

//   const handleTrainClick = async () => {
//     setTriggering(true);
//     try {
//       const res = await apiClient.post(
//         `${import.meta.env.VITE_TRAINING_BASE_URL}/rasa-model-training`
//       );
//       //   const data = await res.json();
//       console.log("Training triggered:", res);
//     } catch (err) {
//       console.error("Failed to trigger training", err);
//     } finally {
//       setTriggering(false);
//     }
//   };

//   //   if (loading || !status || status.status !== "success" || !status.end_time) return null;

//   const modelName =
//     status.model_path && status.model_path?.split("/").pop()?.replace(".tar.gz", "");
//   const trainedAt = status.end_time || null;

//   return (
//     <div className="flex items-center">
//       <p className="text-sm text-gray-700">
//         🤖 Last trained bot: <span className="font-semibold text-green-600">{modelName}</span> at{" "}
//         <span className="text-gray-600">{formatDateTime(trainedAt)}</span>
//       </p>
//       <button
//         onClick={handleTrainClick}
//         disabled={triggering}
//         className="ml-4 px-4 py-1 text-sm font-medium bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
//       >
//         {triggering ? "Starting..." : "Train Model"}
//       </button>
//     </div>
//   );
// }

import { useState } from "react";
import { useTrainingStatus } from "../../hooks/useTrainingStatus";
import apiClient from "../../services/apiClient";
import { formatDateTimeIST  } from "../../utils/time";

export default function TrainingStatusWidget() {
  const { status, loading } = useTrainingStatus();
  const [triggering, setTriggering] = useState(false);

  if (!status) return;

  const handleTrainClick = async () => {
    setTriggering(true);
    try {
      const res = await apiClient.post(
        `${import.meta.env.VITE_RASA_TRAINING_BASE_URL}/rasa-model-training`
      );
    } catch (err) {
      console.error("Failed to trigger training", err);
    } finally {
      setTriggering(false);
    }
  };

  const modelName =
    status.model_path && status.model_path?.split("/").pop()?.replace(".tar.gz", "");
  const trainedAt = status.end_time || null;
  const isTraining = status.status === "running";

  return (
    <div className="flex items-center">
      <p className="text-sm text-gray-700">
        {isTraining ? (
          <span className="text-blue-600">🔄 Training in progress...</span>
        ) : (
          <>
            🤖 Last trained bot: <span className="font-semibold text-green-600">{modelName}</span>{" "}
            at <span className="text-gray-600">{formatDateTimeIST(trainedAt)}</span>
          </>
        )}
      </p>
      <button
        onClick={handleTrainClick}
        disabled={triggering || isTraining}
        className="ml-4 px-4 py-1 text-sm font-medium bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {triggering ? "Starting..." : isTraining ? "Training..." : "Train Model"}
      </button>
    </div>
  );
}