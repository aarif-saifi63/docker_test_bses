import { useEffect, useRef, useState } from "react";
import { Send, Mic, MicOff } from "lucide-react";
import { IoMenu } from "react-icons/io5";
import apiClient from "../../services/apiClient";
import { Loader } from "@googlemaps/js-api-loader";
const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
const LOCATION_TRIGGERS = ["type your address manually", "अपना पता मैन्युअली टाइप करें"];

export default function ChatInput({
  input,
  setInput,
  handleSend,
  handleFileUpload,
  lastBotMessage,
  handleLatLngExtracted,
  setLastBotMessage,
  locationModeKey,
  onMenuClick,
  menuEnabled,
  isInputDisabled,
  resetInactivityTimer,
  awaitingCaNumber,
  awaitingOtp,
  awaitingVisuallOtp,
  awaitingVisuall,
  awaitingOrderId,
  emailValidation,
  disableAllInputs,
  selectedLanguage
}) {
  const inputRef = useRef(null);
  const autocompleteRef = useRef(null);
  const [forceRenderKey, setForceRenderKey] = useState("text");
  const [isRecording, setIsRecording] = useState(false);
  const [recorder, setRecorder] = useState(null);
  const [menuLoading, setMenuLoading] = useState(false);
  const mediaStreamRef = useRef(null);

  // ---- OpenStreetMap (Nominatim) Autocomplete ----
  const [suggestions, setSuggestions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const searchTimeoutRef = useRef(null);

  const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  // Location mode detection
  const isLocationMode = LOCATION_TRIGGERS.some((trigger) =>
    lastBotMessage?.trim().toLowerCase().includes(trigger)
  );

  const lowerMsg = lastBotMessage?.toLowerCase() || "";



  // Block triggers: add "please select your preferred language" (and Hindi) here
  const BLOCK_TRIGGERS = [
    "too many attempts. let's start over",
    "बहुत अधिक प्रयास हो गए हैं",
    // "thanks for reaching out! i’m having trouble understanding your request",
    "please select your preferred language",
    "कृपया अपनी पसंदीदा भाषा चुनें"
  ];

  const isBlocked = disableAllInputs || BLOCK_TRIGGERS.some((t) => lowerMsg.includes(t));



  const botMsg = lastBotMessage?.trim() || "";

  const isCARequest =
    botMsg.includes("Please enter your CA number.") ||
    botMsg.includes("कृपया अपना सीए नंबर दर्ज करें।");

  const isOTPRequest =
    botMsg.includes("CA number is being processed") ||
    botMsg.includes("कृपया 6 अंकों का ओटीपी दर्ज करें।");

  const isOrderIDRequest =
    botMsg.includes("Please enter your Order ID") ||
    botMsg.includes("कृपया अपना ऑर्डर आईडी दर्ज करें।");

  const isOrderVisuall =
    botMsg.includes("Please enter your 10-digit valid mobile number") ||
    botMsg.includes("कॉलबैक प्राप्त करने और आगे की सहायता के लिए कृपया अपना वैध 10 अंकों");

  const isOTPVisuall =
    botMsg.includes("A 6-digit One-Time Password (OTP)") ||
    botMsg.includes("आपके द्वारा दर्ज किए गए मोबाइल नंबर पर एक ओटीपी भेजा गया है।");

  // Email validation
  const isEmailRequest =
    botMsg.includes("Please enter your email ID.") ||
    botMsg.includes("Please enter new email ID.") ||
    botMsg.includes("कृपया अपना ईमेल आईडी दर्ज करें") ||
    botMsg.includes("कृपया नया ईमेल आईडी दर्ज करें।");

  // ---- Input change handler ----
  const handleInputChange = (e) => {
    resetInactivityTimer?.();
    const val = e.target.value;

    if (isEmailRequest || emailValidation) {
      setInput(val);
      if (val.trim().length > 0 && !EMAIL_REGEX.test(val.trim())) {
        inputRef.current.setCustomValidity(
          "⚠️ Please enter a valid email address (e.g. user@example.com)."
        );
        inputRef.current.reportValidity();
      } else {
        inputRef.current.setCustomValidity("");
      }
      return;
    }

    if (isLocationMode) {
      setInput(val);
      return;
    }
    if (isCARequest && (!/^\d*$/.test(val) || val.length > 9)) return;
    if (isOTPRequest && (!/^\d*$/.test(val) || val.length > 6)) return;
    if (isOrderIDRequest && (!/^[A-Za-z0-9]*$/.test(val) || val.length > 15)) return;
    if (isOrderVisuall && (!/^\d*$/.test(val) || val.length > 10)) return;
    if (isOTPVisuall && (!/^\d*$/.test(val) || val.length > 6)) return;

    if (
      (awaitingCaNumber || awaitingOtp || awaitingVisuallOtp || awaitingVisuall) &&
      !/^\d*$/.test(val)
    ) {
      return;
    }

    if (awaitingOrderId && !/^[A-Za-z0-9]*$/.test(val)) {
      return; // alphanumeric only
    }

    // Length constraints
    if (awaitingCaNumber && val.length > 9) return;
    if (awaitingOtp && val.length > 6) return;
    if (awaitingVisuallOtp && val.length > 6) return;
    if (awaitingVisuall && val.length > 10) return;
    if (awaitingOrderId) {
      if (!/^[A-Za-z0-9]*$/.test(val)) return; // only alphanumeric allowed
      if (val.length > 15) return; // prevent more than 15 chars
    }

    setInput(val);
  };



  const isInvalidEmail =
    (isEmailRequest || emailValidation) &&
    input.trim().length > 0 &&
    !EMAIL_REGEX.test(input.trim());

  // ---- Button disabling logic ----
  const isSendDisabled =
    isBlocked ||
    !input.trim() ||
    isLocationMode ||
    isInvalidEmail ||
    isInputDisabled ||
    (isCARequest && input.trim().length !== 9) ||
    (isOTPRequest && input.trim().length !== 6) ||
  (isOrderIDRequest && !(input.trim().length === 12 || input.trim().length === 10 || input.trim().length === 15)) ||
    (awaitingOrderId && !(input.trim().length === 12 || input.trim().length === 10 || input.trim().length === 15)) ||
    (isOrderVisuall && input.trim().length !== 10) ||
    (isOTPVisuall && input.trim().length !== 6) ||
    (awaitingCaNumber && input.trim().length !== 9) ||
    (awaitingOtp && input.trim().length !== 6) ||
    (awaitingVisuallOtp && input.trim().length !== 6) ||
    (awaitingVisuall && input.trim().length !== 10);

  // useEffect(() => {
  //   if (isLocationMode) setForceRenderKey("location");
  // }, [lastBotMessage]);

  // useEffect(() => {
  //   if (!isLocationMode) {
  //     setSuggestions([]);
  //     return;
  //   }
  // }, [isLocationMode, lastBotMessage]);

  // When input changes in location mode — fetch from OpenStreetMap
  // useEffect(() => {
  //   if (!isLocationMode) return;
  //   const query = input.trim();
  //   if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);

  //   if (query.length < 2) {
  //     setSuggestions([]);
  //     return;
  //   }

  //   searchTimeoutRef.current = setTimeout(async () => {
  //     setIsSearching(true);
  //     try {
  //       const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&countrycodes=in&limit=10&q=${encodeURIComponent(
  //         query
  //       )}`;
  //       const res = await fetch(url);
  //       const data = await res.json();

  //       const results = Array.isArray(data) ? data.filter((d) => d.display_name) : [];
  //       setSuggestions(results);
  //     } catch (err) {
  //       console.error("Location search failed:", err);
  //     } finally {
  //       setIsSearching(false);
  //     }
  //   }, 400);

  //   return () => clearTimeout(searchTimeoutRef.current);
  // }, [input, isLocationMode]);



  useEffect(() => {
    if (!isLocationMode || !inputRef.current) return;
    if (autocompleteRef.current) {
      autocompleteRef.current.unbindAll();
      autocompleteRef.current = null;
    }
    const loader = new Loader({
      apiKey: GOOGLE_MAPS_API_KEY,
      version: "weekly",
      libraries: ["places"],
    });
    loader.load().then(() => {
      if (!inputRef.current) return;
      autocompleteRef.current = new window.google.maps.places.Autocomplete(
        inputRef.current,
        { componentRestrictions: { country: "in" } }
      );
      autocompleteRef.current.setFields([
        "formatted_address",
        "geometry",
        "name",
        "place_id",
        "address_components",
      ]);
      autocompleteRef.current.addListener("place_changed", () => {
        const place = autocompleteRef.current.getPlace();
        if (place.geometry) {
          const lat = place.geometry.location.lat();
          const lng = place.geometry.location.lng();
          if (handleLatLngExtracted) {
            handleLatLngExtracted({ lat, lng });
            setInput("");
          }
          if (autocompleteRef.current) {
            autocompleteRef.current.unbindAll();
            autocompleteRef.current = null;
          }
          setLastBotMessage("");
        }
      });
    });
    return () => {
      if (autocompleteRef.current) {
        autocompleteRef.current.unbindAll();
        autocompleteRef.current = null;
      }
    };
  }, [isLocationMode, locationModeKey, lastBotMessage]);

  useEffect(() => {
    if (isLocationMode) setForceRenderKey("location");
  }, [lastBotMessage]);
  // Handle click on suggestion
  const handleSelectPlace = (place) => {
    const lat = parseFloat(place.lat);
    const lng = parseFloat(place.lon);
    setInput(place.display_name);
    setSuggestions([]);
    setLastBotMessage("");
    handleLatLngExtracted?.({ lat, lng });
  };

  const startRecording = async () => {
    try {
      // Request mic permission and start recording
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      let chunks = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });

        const formData = new FormData();
        formData.append("audio", blob, "recording.webm");
        try {
          const resp = await apiClient.post("/speech-to-text", formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });

          const data = resp;
          let transcript = data?.text?.trim() || "";

          // Sanitize based on input context
          if (isCARequest || awaitingCaNumber) {

            transcript = transcript.replace(/\D/g, "").slice(0, 9);
          } else if (isOTPRequest || awaitingOtp || isOTPVisuall || awaitingVisuallOtp) {

            transcript = transcript.replace(/\D/g, "").slice(0, 6);
          } else if (isOrderIDRequest || awaitingOrderId) {

            transcript = transcript.replace(/[^A-Za-z0-9]/g, "").slice(0, 15);
          } else if (isOrderVisuall || awaitingVisuall) {

            transcript = transcript.replace(/\D/g, "").slice(0, 10);
          }

          setInput(transcript);
          setTimeout(() => inputRef.current?.focus(), 0)
        } catch (err) {
          console.error("Speech-to-text API error:", err);
          toast.error(err.response.data.error || "Failed to reach backend for speech-to-text.");
        }

        // cleanup
        stream.getTracks().forEach((track) => track.stop());
        mediaStreamRef.current = null;
        setRecorder(null);
      };

      setRecorder(recorder);
      recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Microphone error:", error);
      alert("Microphone access denied or error.");
    }
  };

  const stopRecording = () => {
    if (recorder) recorder.stop();
    setIsRecording(false);
  };

  const handleMenu = async () => {
    resetInactivityTimer();
    if (menuLoading) return;
    setMenuLoading(true);
    try {
      await onMenuClick?.();
    } finally {
      setMenuLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2 px-3 py-2 border-t border-[#DFDFDF] bg-white rounded-b-2xl">
      {/* Mic Button now records audio */}
      <label
        className={`cursor-pointer ml-1 ${isBlocked || isInputDisabled ? "opacity-50 cursor-not-allowed" : "hover:text-red-500"
          }`}
        title={
          isBlocked || isInputDisabled
            ? "Mic disabled while input/menu are inactive."
            : isRecording
              ? "Stop Recording"
              : "Start Recording"
        }
        aria-label="Toggle Audio Recording"
      >
        {/* {isRecording ? (
          <Mic
            className={`${isBlocked || isInputDisabled ? "text-gray-400" : "text-red-500"}`}
            size={24}
            onClick={!(isBlocked || isInputDisabled) ? stopRecording : undefined}
          />
        ) : (
          <MicOff
            className={`${isBlocked || isInputDisabled ? "text-gray-400" : "text-gray-500"}`}
            size={24}
            onClick={!(isBlocked || isInputDisabled) ? startRecording : undefined}
          />
        )} */}
      </label>

      {/* File upload input */}
      <input
        id="file-upload"
        type="file"
        accept=".pdf,.doc,.docx,.jpg,.png"
        onChange={handleFileUpload}
        className="hidden"
      />

      <input
        id="chat-input"
        key={`${isLocationMode}-${locationModeKey}-${lastBotMessage}`}
        // key={`${isLocationMode}-${locationModeKey}`}
        ref={inputRef}
        value={input}
        onChange={handleInputChange}
        onKeyDown={(e) => {
          if (
            e.key === "Enter" &&
            // !isLocationMode &&
            // !isBlocked &&
            // !isInputDisabled

            !isSendDisabled
          ) {
            resetInactivityTimer?.();
            handleSend();
          }
        }}
        placeholder={
          isBlocked
            ? "Please click Home to start over"
            : isLocationMode
              ? "Search location here..."
              : isInputDisabled
                ? "Please choose any option"
                : "Type your message here..."
        }
        autoComplete="off"
        spellCheck={false}
        disabled={isBlocked || isInputDisabled}
        className="flex-1 border-0 text-sm h-[50px] focus:outline-0 disabled:cursor-not-allowed"
      />

      {/* Location Suggestions (OpenStreetMap) */}
      {isLocationMode && suggestions.length > 0 && (
        <div className="absolute bottom-16 left-3 right-3 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto z-50">
          {isSearching ? (
            <div className="p-2 text-sm text-gray-500 text-center">Searching...</div>
          ) : (
            suggestions.map((sug, i) => (
              <div
                key={i}
                onClick={() => handleSelectPlace(sug)}
                className="p-2 text-sm cursor-pointer hover:bg-blue-50"
              >
                {sug.display_name}
              </div>
            ))
          )}
        </div>
      )}

      <button
        onClick={() => {
          if (!isSendDisabled) {
            resetInactivityTimer?.();
            handleSend();
          }
        }}
        disabled={isSendDisabled}
        className={`h-[38px] w-[38px] flex items-center justify-center rounded-full transition
    ${!isSendDisabled
            ? "bg-[#356CDE] text-white hover:bg-[#274fb5]"
            : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }`}
      >
        <Send size={20} />
      </button>

      <button
        onClick={
          menuEnabled && !menuLoading && !isBlocked && !isInputDisabled ? handleMenu : undefined
        }
        disabled={!menuEnabled || menuLoading || isBlocked || isInputDisabled}
        title="Chat Menu"
        className={`homeBtn text-white right-0.5 h-[40px] w-[40px] flex items-center justify-center rounded-full transition
      ${menuEnabled && !menuLoading && !isBlocked
            ? "bg-[#DE4247] cursor-pointer"
            : "bg-gray-400 cursor-not-allowed"
          }`}
      >
        {menuLoading ? (
          <span className="loader h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : (
          <IoMenu size={26} />
        )}
      </button>
    </div>
  );
}
