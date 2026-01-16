import React, { useState, useEffect, useRef } from "react";
import { MessageCircle } from "lucide-react";
import apiClient, { initSession } from "../services/apiClient";
import { v4 as uuidv4 } from "uuid";
import {
  STATIC_WELCOME,
  SERVICE_PROVIDERS,
  isSpecialMenuResponse,
  groupButtons,
  getMainComplaintButtons,
  getSubComplaintButtons,
} from "../utils/extractors";
import ChatHeader from "../components/Header/ChatHeader";
import ChatMessages from "../components/ChatsUI/ChatMessages";
import SpecialMenuGroups from "../components/SpecialMenus/SpecialMenuGroups";
import GroupedButtons from "../components/SpecialMenus/GroupedButtons";
import ChatButtons from "../components/Buttons/ChatButtons";
import ChatInput from "../components/ChatsUI/ChatInput";
import FaqAccordion from "../components/Faqs/FaqAccordion";
import chatMascotsIcon from "../assets/mascots/e-mitra-F 1.png";
import { IoClose } from "react-icons/io5";
import useBranchAccordion from "../hooks/useBranchAccordion";
import BranchAccordionSection from "../components/Branches/BranchAccordionSection";
import PollQuestion from "../components/Polls/PollQuestion";
import { SyncLoader } from "react-spinners";
// import { data } from "react-router-dom";
import { useLocation } from "react-router-dom";
import { BASE_URL } from "../services/apiClient";
import { X } from "lucide-react";

export default function HomePage() {
  const [openChat, setOpenChat] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [buttons, setButtons] = useState([]);
  const [groupedButtons, setGroupedButtons] = useState(null);
  const [showProviderButton, setShowProviderButton] = useState(true);
  const [specialMenuGroups, setSpecialMenuGroups] = useState([]);
  const [specialMenuActiveIdx, setSpecialMenuActiveIdx] = useState(null);
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("");
  const [selectedUserType, setSelectedUserType] = useState("");
  const [faqGroups, setFaqGroups] = useState([]);
  const [faqActiveIndex, setFaqActiveIndex] = useState(null);
  const [buttonIcons, setButtonIcons] = useState([]);
  const [isLanguageChangeRequested, setIsLanguageChangeRequested] = useState(false);
  const [userId, setUserId] = useState("");
  // const [caNumber, setCaNumber] = useState("");
  const [userType, setUserType] = useState("");
  const [awaitingCaNumber, setAwaitingCaNumber] = useState(false);
  const [awaitingOrderCaNumber, setAwaitingOrderCaNumber] = useState(false);
  const [awaitingOtp, setAwaitingOtp] = useState(false);
  const [awaitingVisuall, setAwaitingVisuall] = useState(false);
  const [awaitingOrderId, setAwaitingOrderId] = useState(false);
  const [awaitingLanguageValidation, setAwaitingLanguageValidation] = useState(false);
  const [awaitingVisuallOtp, setAwaitingVisuallOtp] = useState(false);
  const [emailValidation, setEmailValidation] = useState(false);
  const [pendingLocation, setPendingLocation] = useState(false);
  const [lastSelectedType, setLastSelectedType] = useState("");
  const [lastBotMessage, setLastBotMessage] = useState("");
  const [locationModeKey, setLocationModeKey] = useState("");
  const [locationConfirmationData, setLocationConfirmationData] = useState(null);
  const [mainMenuHeading, setMainMenuHeading] = useState(null);
  const [mainMenuButtons, setMainMenuButtons] = useState(null);
  const [mainMenuHeadingTemp, setMainMenuHeadingTemp] = useState(null);
  const [mainMenuButtonsTemp, setMainMenuButtonsTemp] = useState(null);
  const [isBotLoading, setIsBotLoading] = useState(false);
  const [isLoadingTimeout, setIsLoadingTimeout] = useState(false);
  const [isOrderIdPrefixActive, setIsOrderIdPrefixActive] = useState(false);
  const [specialMenuMainButtons, setSpecialMenuMainButtons] = useState([]);
  const [specialMenuSubButtons, setSpecialMenuSubButtons] = useState([]);
  const [specialMenuParent, setSpecialMenuParent] = useState(null);
  const [lastSpecialMenuButtons, setLastSpecialMenuButtons] = useState([]);
  const [feedbackQuestions, setFeedbackQuestions] = useState([]);
  const [feedbackStep, setFeedbackStep] = useState(0);
  const [feedbackAnswers, setFeedbackAnswers] = useState({});
  const [isFeedbackActive, setIsFeedbackActive] = useState(false);
  const [feedbackAcceptanceStep, setFeedbackAcceptanceStep] = useState(false);
  const [feedbackAcceptanceQuestion, setFeedbackAcceptanceQuestion] = useState(null);
  const [isInputDisabled, setIsInputDisabled] = useState(false);
  const [pollQuestions, setPollQuestions] = useState([]);
  const [currentPollIndex, setCurrentPollIndex] = useState(0);
  const [pollAnswers, setPollAnswers] = useState({});
  const [pollId, setPollId] = useState(null);
  const [pollResponses, setPollResponses] = useState([]);
  const timeoutRef = useRef(null);
  const abortControllerRef = useRef(null);
  const isIntentionalAbortRef = useRef(false);
  const mainMenuHeadingTempRef = useRef(null);
  const mainMenuButtonsTempRef = useRef(null);
  const mainMenuTimeoutRef = useRef(null);
  const MAIN_MENU_DELAY = 2000;
  const [lastSelectedOption, setLastSelectedOption] = useState(null);
  const [pendingMessage, setPendingMessage] = useState(null);
  const inactivityTimerRef = useRef(null);
  const isBotLoadingRef = useRef(false);
  const [inactivityStage, setInactivityStage] = useState(0);
  const [systemMessages, setSystemMessages] = useState([]);
  const [adId, setAdId] = useState(null);
  const [adsId, setAdsID] = useState(null);
  const [adDownloadStates, setAdDownloadStates] = useState({});
  const [showWelcomePopup, setShowWelcomePopup] = useState(true);
  const awaitingOrderIdRef = useRef(false);
  const awaitingLanguageValidationRef = useRef(false);
  const awaitingCaNumberRef = useRef(false);
  const awaitingOtpRef = useRef(false);
  const isInitialMountRef = useRef(true);

  const [otpResendCount, setOtpResendCount] = useState(2);
  const [disableAllInputs, setDisableAllInputs] = useState(false);
  const [emailCountDown, setEmailCountDown] = useState(2);


  const {
    branchData,
    selectedDistance,
    setSelectedDistance,
    getAccordionGroups,
    resetBranchAccordion,
  } = useBranchAccordion();
  const chatRef = useRef(null);

  const storeMenuTemp = (heading, buttons) => {
    setMainMenuHeadingTemp(heading);
    setMainMenuButtonsTemp(buttons);
    mainMenuHeadingTempRef.current = heading;
    mainMenuButtonsTempRef.current = buttons;
  };

  const showMainMenu = (heading, buttons, delay = MAIN_MENU_DELAY) => {
    // clear any pending menu timeout
    if (mainMenuTimeoutRef.current) {
      clearTimeout(mainMenuTimeoutRef.current);
      mainMenuTimeoutRef.current = null;
    }

    // schedule showing main menu after delay
    mainMenuTimeoutRef.current = setTimeout(() => {
      setMainMenuHeading(heading);
      setMainMenuButtons(buttons);
      // clear temp holders (if any)
      setMainMenuHeadingTemp(null);
      setMainMenuButtonsTemp(null);
      mainMenuHeadingTempRef.current = null;
      mainMenuButtonsTempRef.current = null;
      mainMenuTimeoutRef.current = null;
    }, delay);
  };

  // Helper function to get or create abort signal
  const getAbortSignal = () => {
    // Cancel any previous controller
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new controller
    abortControllerRef.current = new AbortController();
    return abortControllerRef.current.signal;
  };

  const resetChat = async () => {
    // Cancel all ongoing API requests
    if (abortControllerRef.current) {
      isIntentionalAbortRef.current = true;
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    try {
      const newUserId = await initSession();
      setUserId(newUserId);
    } catch (error) {
      console.error('Session reset failed:', error);
    }

    setMessages([
      {
        // id: 1,
        sender: "bot",
        text: STATIC_WELCOME,
        timestamp: new Date(),
      },
    ]);
    setButtons(SERVICE_PROVIDERS);
    setGroupedButtons(() => null);
    setInput("");
    setShowProviderButton(true);
    setSpecialMenuGroups([]);
    setSpecialMenuActiveIdx(null);
    setSelectedProvider("");
    setSelectedLanguage("");
    setSelectedUserType("");
    setFaqGroups([]);
    setFaqActiveIndex(null);
    setAwaitingCaNumber(false);
    setAwaitingOtp(false);
    setAwaitingOrderId(false);
    setAwaitingLanguageValidation(false);
    setAwaitingVisuall(false);
    setAwaitingVisuallOtp(false);
    setEmailValidation(false);
    setButtonIcons([]);
    setLastBotMessage("");
    resetBranchAccordion();
    setMainMenuButtons(null);
    setMainMenuHeading(null);
    setOtpResendCount(2);
    setDisableAllInputs(false);
    setEmailCountDown(2);
    setIsBotLoading(false)
    setIsLoadingTimeout(false)
    setIsOrderIdPrefixActive(false)
    setLastSelectedOption(null)
    setPendingMessage(null)
    awaitingOrderIdRef.current = false;
    awaitingLanguageValidationRef.current = false;
    awaitingCaNumberRef.current = false;
    awaitingOtpRef.current = false;

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }
    setSystemMessages([]);
    setInactivityStage(0);

    setFeedbackQuestions([]);
    setFeedbackStep(0);
    setFeedbackAnswers({});
    setIsFeedbackActive(false);
    resetFeedbackState();
    setPollQuestions([]);
    setCurrentPollIndex(0);
    setPollAnswers({});
    setPollId(null);

    (async () => {
      try {
        const res = await apiClient.get("/chatbot-intro-ad", {}, { signal: getAbortSignal() });
        const ad = res?.data?.data || res?.data || res;

        setAdsID(ad?.id);

        if (ad?.ad_image_path && ad?.ad_pdf_path) {
          setMessages((prev) => [
            ...prev,
            {
              id: uuidv4(),
              sender: "bot",
              ad: {
                image_url: `${BASE_URL}/${ad.ad_image_path}`,
                pdf_url: `${BASE_URL}/${ad.ad_pdf_path}`,
                ad_id: ad?.id,
              },
              timestamp: new Date(),
            },
          ]);
        }
      } catch (err) {
        // Ignore cancelled requests
        if (err.name === 'AbortError' || err.name === 'CanceledError') {
          console.log("Chatbot intro ad request cancelled");
          return;
        }
        console.error("Failed to load chatbot intro ad:", err);
        // static welcome + buttons already shown
      }
    })();
  };

  const resetFeedbackState = () => {
    setFeedbackAcceptanceStep(false);
    setFeedbackAcceptanceQuestion(null);
    setIsFeedbackActive(false);
    setFeedbackQuestions([]);
    setFeedbackStep(0);
    setFeedbackAnswers({});
    setIsInputDisabled(false);
  };

  const resetInactivityTimer = () => {

    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
    }


    setInactivityStage(0);
    setSystemMessages([]);


    if (isBotLoading) {
      return;
    }


    if (!selectedUserType) {
      return;
    }


    inactivityTimerRef.current = setTimeout(() => {

      if (isBotLoadingRef.current) {
        return;
      }

      setSystemMessages([
        {
          id: Date.now(),
          sender: "bot",
          text: " We haven't received a response from you in a while. Your session may time out soon.",
          timestamp: new Date(),
        },
      ]);
      setInactivityStage(1);


      const secondWarningTimer = setTimeout(() => {

        if (isBotLoadingRef.current) {
          return;
        }

        setSystemMessages([
          {
            id: Date.now(),
            sender: "bot",
            text: "You seem inactive. The chat will reset soon if there's no response.",
            timestamp: new Date(),
          },
        ]);
        setInactivityStage(2);

        const resetTimer = setTimeout(() => {
          // Don't reset if bot is loading (use ref to get current value)
          if (isBotLoadingRef.current) {
            return;
          }
          resetChat();
        }, 30 * 1000);
        inactivityTimerRef.current = resetTimer;
      }, 30 * 1000);
      inactivityTimerRef.current = secondWarningTimer;
    }, 30 * 1000);
  };


  const getLocationWithGoogle = async () => {
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

    try {
      const response = await fetch(
        `https://www.googleapis.com/geolocation/v1/geolocate?key=${apiKey}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            considerIp: true,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Google Geolocation API failed');
      }

      const data = await response.json();

      return {
        coords: {
          latitude: data.location.lat,
          longitude: data.location.lng,
          accuracy: data.accuracy,
        },
      };
    } catch (error) {
      console.error('Google Geolocation error:', error);
      throw error;
    }
  };

  const reverseGeocode = async (lat, lon) => {
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

    try {
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lon}&key=${apiKey}`
      );

      if (!response.ok) {
        throw new Error('Reverse geocoding failed');
      }

      const data = await response.json();

      if (data.results && data.results.length > 0) {
        return data.results[0].formatted_address;
      } else {
        throw new Error('No address found');
      }
    } catch (error) {
      console.error('Reverse geocoding error:', error);
      throw error;
    }
  };

  const handleAdDownload = async (adId) => {
    setAdDownloadStates((prev) => ({ ...prev, [adId]: true }));
    try {
      const res = await apiClient.post(`/submit-ad-tracker?senderId=${userId}&ad_id=${adId}`, {}, { signal: getAbortSignal() });
      if (res?.data?.status === "success" || res?.status === "success") {
        setAdDownloadStates((prev) => ({ ...prev, [adId]: false }));
      } else {
        setAdDownloadStates((prev) => ({ ...prev, [adId]: false }));
      }
    } catch (err) {
      // Ignore cancelled requests
      if (err.name === 'AbortError' || err.name === 'CanceledError') {
        console.log("Ad download tracker request cancelled");
        return;
      }
      setAdDownloadStates((prev) => ({ ...prev, [adId]: false }));
    }
  };

  useEffect(() => {
    if (systemMessages.length > 0) {
      chatRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [systemMessages]);

  useEffect(() => {
    if (openChat) resetChat();
  }, [openChat]);

  useEffect(() => {
    chatRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [
    messages,
    buttons,
    groupedButtons,
    specialMenuGroups,
    specialMenuActiveIdx,
    faqGroups,
    faqActiveIndex,
    branchData,
    selectedDistance,
    lastBotMessage,
    mainMenuHeading,
    mainMenuButtons,
    isLoadingTimeout,
    systemMessages,
  ]);

  useEffect(() => {
    return () => {
      if (mainMenuTimeoutRef.current) {
        clearTimeout(mainMenuTimeoutRef.current);
        mainMenuTimeoutRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const senderId = await initSession();
        setUserId(senderId);
      } catch (error) {
        console.error('Session init failed:', error);
        // Fallback to frontend UUID if API fails
        const fallbackId = `user_${uuidv4()}`;
        setUserId(fallbackId);
      }
    };
    fetchSession();
  }, []);

  useEffect(() => {
    // Keep ref in sync with state
    isBotLoadingRef.current = isBotLoading;

    let timer;
    if (isBotLoading) {
      timer = setTimeout(() => setIsLoadingTimeout(true), 4000);
    } else {
      setIsLoadingTimeout(false);
    }
    return () => clearTimeout(timer);
  }, [isBotLoading]);


  // Restart inactivity timer when bot finishes loading and user has selected their type
  useEffect(() => {
    if (!isBotLoading && openChat && selectedUserType) {
      resetInactivityTimer();
    }
  }, [isBotLoading, openChat, selectedUserType]);


  useEffect(() => {
    if (
      lastBotMessage?.includes(
        "Please enter your Order ID. The Order ID starts with ‘008’, ‘AN’, or ‘ON’"
      ) ||
      lastBotMessage?.includes(
        "Please enter your Order ID. The Order ID starts with ‘008’, '8', ‘AN’, or ‘ON’"
      ) ||
      lastBotMessage?.includes(
        "कृपया अपना ऑर्डर आईडी दर्ज करें। आपका ऑर्डर आईडी '008', '8', 'AN' या 'ON' से शुरू होता है"
      ) ||
      lastBotMessage?.includes(
        "कृपया अपना ऑर्डर आईडी दर्ज करें। आपका ऑर्डर आईडी '008','AN' या 'ON' से शुरू होता है।"
      )
    ) {
      setIsOrderIdPrefixActive(true);
    } else if (
      lastBotMessage?.includes("New connection request") ||
      lastBotMessage?.includes("आपके नए कनेक्शन अनुरोध की स्थिति है:")
    ) {
      setIsOrderIdPrefixActive(false);
    }
  }, [lastBotMessage]);

  useEffect(() => {
    if (feedbackQuestions.length > 0) {
      const currentQ = feedbackQuestions[feedbackStep];
      if (currentQ.options && currentQ.options.length > 0) {
        setIsInputDisabled(true);
      } else {
        setIsInputDisabled(false);
      }
    }
  }, [feedbackQuestions, feedbackStep]);

  // Auto-select service provider after resetChat
  useEffect(() => {
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      return;
    }

    // This runs when userId changes (from resetChat)
    const timer = setTimeout(async () => {
      setButtons([]);
      setShowProviderButton(false);
      setSelectedProvider("BSES Rajdhani");
      setIsBotLoading(true);
      await sendMessage("BSES Rajdhani", true, null, null, true, userId);
      setIsBotLoading(false);
    }, 100);

    return () => clearTimeout(timer);
  }, [userId]);

  useEffect(() => {
    if (lastSelectedOption && pendingMessage) {
      // ✅ Send message only after React state updates
      sendMessage(pendingMessage, true, null, lastSelectedOption);

      // Reset pending message after sending
      setPendingMessage(null);
    }
  }, [lastSelectedOption, pendingMessage]);

  useEffect(() => {
    if (openChat && selectedUserType) {
      resetInactivityTimer();
    }
    return () => {
      if (inactivityTimerRef.current) {
        clearTimeout(inactivityTimerRef.current);
        inactivityTimerRef.current = null;
      }
    };
  }, [openChat, selectedUserType]);


  const handleLatLngExtracted = async ({ lat, lng }) => {
    const type = lastSelectedType || "BC";
    setButtons([]);
    await sendMessage(`${lat},${lng} ${type}`);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Show fake file upload in chat
    setMessages((prev) => [
      ...prev,
      {
        //id: uuidv4(),
        id: uuidv4(),
        sender: "user",
        text: `📄 Uploaded: ${file.name}`,
      },
    ]);

    // Prepare message based on selected language
    const message = selectedLanguage?.toLowerCase().includes("हिंदी")
      ? "दस्तावेज़ अपलोड करें"
      : "Upload document";
    setIsBotLoading(true);
    try {
      // Send only the message to backend
      const data = await apiClient.post("/webhook", {
        sender_id: userId,
        message,
      }, { signal: getAbortSignal() });

      // Handle bot response
      if (data?.response && data.response.heading?.length > 0) {
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: data.response.heading.join("\n\n"),
            timestamp: new Date(),
          },
        ]);
        setLastBotMessage(data.response.heading.join("\n\n"));
        if (data.response.buttons) {
          setButtons(data.response.buttons);
          setGroupedButtons(null);
          setShowProviderButton(false);
          setSpecialMenuGroups([]);
          setButtonIcons(data.response.icons || []);
          setSpecialMenuActiveIdx(null);
        } else {
          setButtons([]);
        }
      }
    } catch (error) {
      // Ignore cancelled requests
      if (error.name === 'AbortError' || error.name === 'CanceledError') {
        console.log("Location webhook request cancelled");
        return;
      }
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "bot",
          text: "❌ File message failed to send. Please try again.",
        },
      ]);
    } finally {
      setIsBotLoading(false);
    }
  };

  const handleRegisterMenuRunFlow = async (userTypeParam = selectedUserType) => {
    setIsBotLoading(true);
    try {
      // const lang = selectedLanguage.includes("English") ? "english" : "हिंदी";
      const payload = {
        subsidiary: `${getSubsidiary()} BRPL`,
        user: `${userTypeParam} BRPL`,
        language: `${selectedLanguage} BRPL`,
        sender_id: userId,
        ca_number: "CA VALIDATED BRPL",
        otp: "OTP VALIDATED BRPL",
      };
      const res = await apiClient.post("/register_menu_run_flow", payload, { signal: getAbortSignal() });

      // Always use res.response for consistency
      const data = res?.response;

      if (data && Array.isArray(data.buttons) && Array.isArray(data.heading)) {
        const updatedButtons = data.buttons.map((btn) => {
          if (btn === "Virtual Customer Care Centre (BYPL) / Connect Virtually (BRPL)") {
            return "Connect Virtually (BRPL)";
          }
          if (btn === "वर्चुअल कस्टमर केयर सेंटर (BYPL) / वर्चुअली कनेक्ट करें (BRPL)") {
            return "वर्चुअली कनेक्ट करें (BRPL)";
          }
          return btn;
        });

        const groups = groupButtons(updatedButtons);
        setFaqGroups([]);
        setFaqActiveIndex(null);
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: data.heading.join("\n\n"),
            timestamp: new Date(),
          },
        ]);
        setLastBotMessage(data.heading.join("\n\n"));
        setSpecialMenuGroups(groups);
        setButtonIcons(data.icons || []);
        setSpecialMenuActiveIdx(null);
        setButtons([]);
        setUserType("");
        setGroupedButtons(null);
        setShowProviderButton(false);
      } else if (Array.isArray(data)) {
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: "Please choose an option:",
            buttons: groupButtons(data),
            timestamp: new Date(),
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: Array.isArray(data?.heading)
              ? data.heading.join("\n\n")
              : typeof data?.heading === "string"
                ? data.heading
                : "Please choose an option:",
            timestamp: new Date(),
          },
        ]);
      }
    } catch (err) {
      // Ignore cancelled requests
      if (err.name === 'AbortError' || err.name === 'CanceledError') {
        console.log("Register menu flow request cancelled");
        return;
      }
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "bot",
          text: "❌ Failed to trigger menu after OTP validation.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsBotLoading(false);
    }
  };

  const handleFeedbackFlow = async (langType = "English") => {
    setIsBotLoading(true);
    setMainMenuButtons(null);
    setMainMenuHeading(null);
    try {
      const res = await apiClient.get("/get_feedback_acceptance", {}, { signal: getAbortSignal() });
      if (res?.data?.length) {
        // check if any question has options
        const hasOptions = res.data.some((q) => q.options && q.options.length > 0);

        // if options present → disable input, else enable
        setIsInputDisabled(hasOptions);
      }
      const data = res?.data || res;
      const questions = data || [];
      const questionObj = questions.find((q) => q.question_type === langType);
      if (questionObj) {
        setFeedbackAcceptanceStep(true);
        setFeedbackAcceptanceQuestion(questionObj);
        setMessages((prev) => [
          ...prev,
          {
            //id: uuidv4(),
            id: uuidv4(),
            sender: "bot",
            text: questionObj.question,
            options: questionObj.options,
            feedback_acceptance: true,
            questionId: questionObj.id,
            timestamp: new Date(),
          },
        ]);
      }
    } catch (err) {
      // Ignore cancelled requests
      if (err.name === 'AbortError' || err.name === 'CanceledError') {
        console.log("Feedback acceptance request cancelled");
        return;
      }
      setMessages((prev) => [
        ...prev,
        {
          //id: uuidv4(),
          id: uuidv4(),
          sender: "bot",
          text: "Unable to load feedback acceptance question.",
          timestamp: new Date(),
        },
      ]);
    }
    setIsBotLoading(false);
  };

  const fetchFeedbackQuestionsByType = async (questionType) => {
    setIsBotLoading(true);
    try {
      const res = await apiClient.get(`/feedback/get-questions?question_type=${questionType}`, {}, { signal: getAbortSignal() });
      if (res?.data?.length) {
        // check if any question has options
        const hasOptions = res.data.some((q) => q.options && q.options.length > 0);

        // if options present → disable input, else enable
        setIsInputDisabled(hasOptions);
      }
      const data = res?.data || res;
      const questions = data || [];
      if (questions.length > 0) {
        setFeedbackQuestions(questions);
        setFeedbackStep(0);
        setFeedbackAnswers({});
        setIsFeedbackActive(true);
        setFeedbackAcceptanceStep(false);
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: questions[0].question,
            options: questions[0].options,
            feedback: true,
            questionId: questions[0].id,
            timestamp: new Date(),
          },
        ]);
      }
    } catch (err) {
      // Ignore cancelled requests
      if (err.name === 'AbortError' || err.name === 'CanceledError') {
        console.log("Feedback questions request cancelled");
        return;
      }
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "bot",
          text: "❌ Unable to load feedback questions.",
          timestamp: new Date(),
        },
      ]);
    }
    setIsBotLoading(false);
  };

  const handlePollFlow = async () => {
    try {
      // const res = await apiClient.get("/polls/active");
      const res = await apiClient.get("/polls/active", {
        sender_id: userId,
      }, { signal: getAbortSignal() });
      const poll = res?.poll;

      if (poll?.questions?.length) {
        setPollId(poll?.id);
        setPollQuestions(poll.questions);
        setCurrentPollIndex(0);
        setPollAnswers({});

        const firstQ = poll.questions[0];
        // Enable input immediately for text, disable for others until selection
        setIsInputDisabled(firstQ.type !== "text");
      } else {
        setIsInputDisabled(false);
      }
    } catch (err) {
      // Ignore cancelled requests
      if (err.name === 'AbortError' || err.name === 'CanceledError') {
        console.log("Poll initialization request cancelled");
        return;
      }
      if (err?.response?.status === 404 || err?.response?.data?.status === "fail") {
        showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);
        setMainMenuHeadingTemp(null);
        setMainMenuButtonsTemp(null);
        mainMenuHeadingTempRef.current = null;
        mainMenuButtonsTempRef.current = null;
      }

      // Reset poll state
      setPollId(null);
      setPollQuestions([]);
      setCurrentPollIndex(0);
      setPollAnswers({});
      setIsInputDisabled(false);
    }
  };

  const handlePollAnswer = async (questionId, answer) => {
    const currentQuestion = pollQuestions[currentPollIndex];

    // 1. Update pollAnswers for UI
    setPollAnswers((prev) => ({ ...prev, [questionId]: answer }));

    // 2. Add to pollResponses array for ordered payload
    setPollResponses((prev) => [...prev, { question: currentQuestion.question, answer }]);

    // 3. Add to chat history
    let displayAnswer = String(answer);
    if (currentQuestion?.type === "star") {
      displayAnswer = "★".repeat(Number(answer));
    }
    setMessages((prevMsgs) => [
      ...prevMsgs,
      {
        id: prevMsgs.length + 1,
        sender: "bot",
        text: currentQuestion?.question || "",
        timestamp: new Date(),
      },
      {
        id: prevMsgs.length + 2,
        sender: "user",
        text: displayAnswer,
        timestamp: new Date(),
      },
    ]);

    // 4. Go to next question or submit poll
    if (currentPollIndex < pollQuestions.length - 1) {
      // Directly update poll index and input state
      setCurrentPollIndex((prev) => {
        const newIndex = prev + 1;
        const nextQ = pollQuestions[newIndex];
        setIsInputDisabled(nextQ.type !== "text");
        return newIndex;
      });
    } else {
      // Final submission
      const payload = {
        poll_id: pollId,
        user_type: "customer",
        response: [...pollResponses, { question: currentQuestion.question, answer }],
        sender_id: userId,
      };

      try {
        const res = await apiClient.post("/poll/submit", payload, { signal: getAbortSignal() });

        setMessages((prevMsgs) => [
          ...prevMsgs,
          {
            id: prevMsgs.length + 3,
            sender: "bot",
            text: res?.data?.message || "Thank you for completing the poll!",
            timestamp: new Date(),
          },
        ]);

        setIsInputDisabled(false);

        if (res?.status === "success") {
          showMainMenu(mainMenuHeadingTemp, mainMenuButtonsTemp);
          setMainMenuHeadingTemp(null);
          setMainMenuButtonsTemp(null);
        }
      } catch (err) {
        // Ignore cancelled requests
        if (err.name === 'AbortError' || err.name === 'CanceledError') {
          console.log("Poll submit request cancelled");
          return;
        }
        setMessages((prevMsgs) => [
          ...prevMsgs,
          {
            id: prevMsgs.length + 3,
            sender: "bot",
            text: "Failed to submit poll.",
            timestamp: new Date(),
          },
        ]);
        setIsInputDisabled(false);
      }

      // Reset poll state
      setPollQuestions([]);
      setCurrentPollIndex(0);
      setPollAnswers({});
      setPollId(null);
      setPollResponses([]);
    }
  };

  const removeSpecialMenuMessages = () => {
    setMessages((prev) => prev.filter((msg) => msg.type !== "specialMenuMainButtons"));
  };

  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const source = params.get("source");

  const sendMessage = async (msg, isUser = true, langOverride = null, directOption = null, isSilent = false, senderIdOverride = null) => {
    const languageToUse = langOverride || selectedLanguage;
    if (!msg.trim()) return;

    const cleanedMsg = msg.trim().toLowerCase();
    const sender_id = senderIdOverride || userId;

    const effectiveLastOption = directOption || lastSelectedOption || "";

    const lastBotMessage = messages
      .slice()
      .reverse()
      .find((m) => m.sender === "bot")?.text;

    const digitOnly = msg.trim().replace(/\D/g, "");

    // Language validation after language selection
    if (
      lastBotMessage?.includes("Please select your language") ||
      lastBotMessage?.includes("कृपया अपनी भाषा चुनें")
    ) {
      setAwaitingLanguageValidation(true);
      awaitingLanguageValidationRef.current = true;
    }

    // Reset flags when language change is successful
    if (
      lastBotMessage?.includes("Language updated successfully") ||
      lastBotMessage?.includes("भाषा सफलतापूर्वक बदल दी गई है")
    ) {
      setAwaitingLanguageValidation(false);
      awaitingLanguageValidationRef.current = false;
    }

    // Only validate if flag is true (not based on lastBotMessage)
    if (awaitingLanguageValidationRef.current) {

      try {
        let languageText = msg.trim();

        const resp = await apiClient.post("/validate-language", {
          text: languageText,
        }, { signal: getAbortSignal() });

        const isValid = resp?.status === true;
        const message = resp?.message || "";

        if (isValid) {
          // Language is valid, continue with original message
          // Don't change msg, let user's text go to webhook
        } else {
          // Invalid language, show user message + error message
          setMessages((prev) => {
            const lastMsg = prev[prev.length - 1];
            const userMsgExists = lastMsg?.sender === "user" && lastMsg?.text === languageText;

            // Add user message if not already there
            const messagesWithUser = userMsgExists ? prev : [
              ...prev,
              {
                id: uuidv4(),
                sender: "user",
                text: languageText,
                timestamp: new Date(),
              },
            ];

            // Add error message
            return [
              ...messagesWithUser,
              {
                id: messagesWithUser.length + 1,
                sender: "bot",
                text: message,
                timestamp: new Date(),
              },
            ];
          });
          setAwaitingLanguageValidation(true);
          awaitingLanguageValidationRef.current = true;
          return;
        }
      } catch (err) {
        // Ignore cancelled requests
        if (err.name === 'AbortError' || err.name === 'CanceledError') {
          console.log("Language validation request cancelled");
          return;
        }
        console.error("Language validation failed:", err);
        setAwaitingLanguageValidation(true);
        awaitingLanguageValidationRef.current = true;
        return;
      }
    }

    // CA number validation and warning
    if (
      lastBotMessage?.toLowerCase().includes("please enter your ca number") ||
      lastBotMessage?.toLowerCase().includes("please enter new ca number") ||
      lastBotMessage?.includes("कृपया नया CA नंबर दर्ज करें।")
    ) {
      setAwaitingCaNumber(true);
      awaitingCaNumberRef.current = true;
    }

    if (
      awaitingCaNumberRef.current ||
      lastBotMessage?.toLowerCase().includes("please enter your ca number") ||
      lastBotMessage?.toLowerCase().includes("please enter new ca number") ||
      lastBotMessage?.includes("कृपया नया CA नंबर दर्ज करें।")
    ) {
      try {
        let caNumberToSend = msg.trim();

        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "user",
            text: caNumberToSend,
            timestamp: new Date(),
          },
        ]);

        const resp = await apiClient.post("/validate_ca", {
          sender_id: sender_id,
          ca_number: caNumberToSend,
        }, { signal: getAbortSignal() });

        const isValid = resp?.valid === true;
        const message = languageToUse.includes("हिंदी")
          ? "कृपया एक मान्य 9 अंकों का सीए (CA) नंबर दर्ज करें।"
          : resp?.message;

        if (!isValid) {
          // Invalid CA Number: show error and stop flow
          setMessages((prev) => [
            ...prev,
            {
              id: uuidv4(),
              sender: "bot",
              text: message,
              timestamp: new Date(),
            },
          ]);
          return; // stop sending further
        }

        msg = "ca verified";

        setAwaitingCaNumber(false); // reset state
        awaitingCaNumberRef.current = false;
        // return; // stop further default webhook send
      } catch (err) {
        // Ignore cancelled requests
        if (err.name === 'AbortError' || err.name === 'CanceledError') {
          console.log("CA validation request cancelled");
          return;
        }
        console.error("CA validation failed:", err);
        return;
      }
    }

    if (
      lastBotMessage?.includes(
        "Please enter your Order ID. The Order ID starts with ‘008’, ‘AN’, or ‘ON’"
      ) ||
       lastBotMessage?.includes(
        "Please enter your Order ID. The Order ID starts with ‘008’, '8', ‘AN’, or ‘ON’"
      ) ||
      lastBotMessage?.includes(
        "कृपया अपना ऑर्डर आईडी दर्ज करें। आपका ऑर्डर आईडी '008', 'AN' या 'ON' से शुरू होता है।"
      ) ||
        lastBotMessage?.includes("कृपया अपना ऑर्डर आईडी दर्ज करें। आपका ऑर्डर आईडी '008','AN' या 'ON' से शुरू होता है।"
      )
    ) {
      setAwaitingOrderId(true);
      awaitingOrderIdRef.current = true;
    }

    if (
      awaitingOrderIdRef.current ||
      lastBotMessage?.includes(
        "Please enter your Order ID. The Order ID starts with ‘008’, ‘AN’, or ‘ON’"
      ) ||
      lastBotMessage?.includes(
        "Please enter your Order ID. The Order ID starts with ‘008’, '8', ‘AN’, or ‘ON’"
      ) ||
      lastBotMessage?.includes(
        "कृपया अपना ऑर्डर आईडी दर्ज करें। आपका ऑर्डर आईडी '008', '8', 'AN' या 'ON' से शुरू होता है।"
      ) || 
       lastBotMessage?.includes(
        "कृपया अपना ऑर्डर आईडी दर्ज करें। आपका ऑर्डर आईडी '008','AN' या 'ON' से शुरू होता है।"
      )
    ) {
      try {
        const order = msg.trim();

        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "user",
            text: order,
            timestamp: new Date(),
          },
        ]);

        const resp = await apiClient.post("/get_order_status", {
          order_id: order,
          sender_id: sender_id,

        }, { signal: getAbortSignal() });
        const isValid = resp?.valid === true;

        // Determine message based on language
        let message = "";
        if (
          lastBotMessage?.includes(
            "कृपया अपना ऑर्डर आईडी दर्ज करें। आपका ऑर्डर आईडी '008', 'AN' या 'ON' से शुरू होता है।"
          ) ||
          lastBotMessage?.includes(
            "आपने जो ऑर्डर आईडी दर्ज की है वह मान्य नहीं है। कृपया दोबारा जांचें और फिर प्रयास करें।"
          )
        ) {
          message = resp?.message_hindi;
        } else {
          message = resp?.message || "";
        }

        // Check if INVALID - show error and handle accordingly
        if (!isValid) {
          // Invalid Order ID: show error message
          setMessages((prev) => [
            ...prev,
            {
              id: uuidv4(),
              sender: "bot",
              text: message,
              timestamp: new Date(),
            },
          ]);

          // If main menu present, reset flags and exit flow
          if (resp?.response?.main_menu_heading && resp?.response?.main_menu_buttons) {
            showMainMenu(resp.response.main_menu_heading, resp.response.main_menu_buttons);
            setAwaitingOrderId(false);
            awaitingOrderIdRef.current = false;
          }
          // else: flags stay TRUE for unlimited retry

          return; // NO webhook call
        }

        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: message,
            timestamp: new Date(),
          },
        ]);


        msg = "order verified";
        setAwaitingOrderId(false);
        awaitingOrderIdRef.current = false;
        setLastBotMessage("");
      } catch (err) {
        if (err.name === 'AbortError' || err.name === 'CanceledError') {
          console.log("Order status request cancelled");
          return;
        }
        console.error("Order validation failed:", err);
        return;
      }
    }

    // --- Validate CA Number with backend API ---

    if (
      lastBotMessage?.includes("CA number is being processed") ||
      lastBotMessage?.includes("कृपया 6-अंकों का ओटीपी दर्ज करें") ||
      lastBotMessage?.includes("कृपया आगे बढ़ने के लिए इसे दर्ज करें।") ||
      lastBotMessage?.includes(
        "A 6-digit One-Time Password (OTP) has been sent to the provided mobile number."
      )
    ) {
      setAwaitingOtp(true);
      awaitingOtpRef.current = true;
    }

    if (
      awaitingOtpRef.current ||
      lastBotMessage?.includes("CA number is being processed") ||
      lastBotMessage?.includes("कृपया 6-अंकों का ओटीपी दर्ज करें") ||
      lastBotMessage?.includes("कृपया आगे बढ़ने के लिए इसे दर्ज करें।") ||
      lastBotMessage?.includes(
        "A 6-digit One-Time Password (OTP) has been sent to the provided mobile number."
      )
    ) {
      try {
        let otp = msg.trim();

        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "user",
            text: otp,
            timestamp: new Date(),
          },
        ]);

        const resp = await apiClient.post("/validate_otp", {
          sender_id: sender_id,
          otp: otp + " BRPL",
        });

        const isValid = resp?.valid === true;
        const message = isValid
          ? "OTP verified successfully."
          : (languageToUse.includes("हिंदी")
            ? "कृपया एक मान्य 6 अंकों का OTP दर्ज करें। शेष प्रयास: "
            : "Please enter a valid 6-digit OTP. Retries left: ") + otpResendCount;

        if (!isValid) {
          // Invalid Otp: show error and stop flow
          if (otpResendCount >= 1) setOtpResendCount((prev) => (prev > 0 ? prev - 1 : 0));
          else setDisableAllInputs(true);
          setMessages((prev) => [
            ...prev,
            {
              id: uuidv4(),
              sender: "bot",
              text:
                otpResendCount > 0
                  ? message
                  : languageToUse.includes("हिंदी")
                    ? "बहुत अधिक प्रयास हो गए हैं। कृपया होम बटन पर क्लिक करके पुनः शुरू करें।"
                    : "Too many attempts. Let's start over. Click home button to start over",
              timestamp: new Date(),
            },
          ]);
          return; // stop sending further
        }

        msg = "otp verified";

        setAwaitingOtp(false); // reset state
        awaitingOtpRef.current = false;
        setOtpResendCount(2); // reset otp resend count
        // return; // stop further default webhook send
      } catch (err) {
        // Ignore cancelled requests
        if (err.name === 'AbortError' || err.name === 'CanceledError') {
          console.log("OTP validation request cancelled");
          return;
        }
        console.error("CA validation failed:", err);
        return;
      }
    }


    if (
      lastBotMessage?.includes("Please enter your 10-digit valid mobile") ||
      lastBotMessage?.includes(
        "कॉलबैक प्राप्त करने और आगे की सहायता के लिए कृपया अपना वैध 10 अंकों"
      )
    ) {
      setAwaitingVisuall(true);
    }

    if (
      awaitingVisuall ||
      lastBotMessage?.includes("Please enter your 10-digit valid mobile") ||
      lastBotMessage?.includes(
        "कॉलबैक प्राप्त करने और आगे की सहायता के लिए कृपया अपना वैध 10 अंकों"
      )
    ) {
      try {
        let mobileNumberToSend = msg.trim();

        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "user",
            text: mobileNumberToSend,
            timestamp: new Date(),
          },
        ]);

        const resp = await apiClient.post("/validate_mobile", {
          sender_id: sender_id,
          mobile_number: mobileNumberToSend,
        }, { signal: getAbortSignal() });

        const isValid = resp?.valid === true;
        const message = languageToUse.includes("हिंदी")
          ? "कृपया एक मान्य 10 अंकों का मोबाइल नंबर दर्ज करें।"
          : resp?.message;

        if (!isValid) {
          // Invalid CA Number: show error and stop flow
          setMessages((prev) => [
            ...prev,
            {
              id: uuidv4(),
              sender: "bot",
              text: message,
              timestamp: new Date(),
            },
          ]);
          return;
        }

        msg = "mobile verified";

        setAwaitingVisuall(false); // reset state
        // return; // stop further default webhook send
      } catch (err) {
        // Ignore cancelled requests
        if (err.name === 'AbortError' || err.name === 'CanceledError') {
          console.log("Mobile validation request cancelled");
          return;
        }
        console.error("Mobile validation failed:", err);
        return;
      }
    }

    if (
      lastBotMessage?.includes(
        "A 6-digit One-Time Password (OTP) has been sent to the provided mobile number."
      ) ||
      lastBotMessage?.includes("आपके द्वारा दर्ज किए गए मोबाइल नंबर पर एक ओटीपी भेजा गया है।")
    ) {
      setAwaitingVisuallOtp(true);
    }

    // STEP 2: Validate Inputs Based on Flags

    if (
      lastBotMessage?.includes("Please enter your email ID.") ||
      lastBotMessage?.includes("Please enter new email ID.") ||
      lastBotMessage?.includes("कृपया नया ईमेल आईडी दर्ज करें।") ||
      (lastBotMessage?.includes("कृपया अपना ईमेल आईडी दर्ज करें।") && !input.trim().includes("@"))
    ) {
      setEmailValidation(true);
    }

    if (
      emailValidation ||
      lastBotMessage?.includes("Please enter your email ID.") ||
      lastBotMessage?.includes("Please enter new email ID.") ||
      lastBotMessage?.includes("कृपया नया ईमेल आईडी दर्ज करें।") ||
      (lastBotMessage?.includes("कृपया अपना ईमेल आईडी दर्ज करें।") && !input.trim().includes("@"))
    ) {
      try {
        let email = msg.trim();

        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "user",
            text: email,
            timestamp: new Date(),
          },
        ]);

        const resp = await apiClient.post("/validate_email", {
          sender_id: sender_id,
          email: email,
        }, { signal: getAbortSignal() });

        const isValid = resp?.valid === true;
        const message = isValid
          ? "Email verified successfully."
          : (languageToUse.includes("हिंदी")
            ? "कृपया एक मान्य ईमेल दर्ज करें। शेष प्रयास: "
            : "Please Enter Valid Email. Retries left: ") + emailCountDown;

        if (!isValid) {
          // Invalid Email: show error and stop flow
          if (emailCountDown >= 1) setEmailCountDown((prev) => (prev > 0 ? prev - 1 : 0));
          else setDisableAllInputs(true);
          setMessages((prev) => [
            ...prev,
            {
              id: uuidv4(),
              sender: "bot",
              text:
                emailCountDown > 0
                  ? message
                  : languageToUse.includes("हिंदी")
                    ? "बहुत अधिक प्रयास हो गए हैं। कृपया होम बटन पर क्लिक करके पुनः शुरू करें।"
                    : "Too many attempts. Let's start over. Click home button to start over",
              timestamp: new Date(),
            },
          ]);
          return; // stop sending further
        }

        msg = "email verified";

        setEmailValidation(false); // reset state
        setEmailCountDown(2); // reset otp resend count
        // return; // stop further default webhook send
      } catch (err) {
        // Ignore cancelled requests
        if (err.name === 'AbortError' || err.name === 'CanceledError') {
          console.log("Email validation request cancelled");
          return;
        }
        console.error("email validation failed:", err);
        return;
      }
    }

    if (isUser && !isSilent) {
      if (
        msg !== "ca verified" &&
        msg !== "order verified" &&
        msg !== "otp verified" &&
        msg !== "mobile verified" &&
        msg !== "email verified"
      ) {
        if (typeof msg === "string" && msg.match(/^-?\d+(\.\d+)?,-?\d+(\.\d+)?\s+(BC|CC)$/)) {
          setMessages((prev) => [
            ...prev,
            {
              id: uuidv4(),
              sender: "user",
              text: "📍 Location shared",
              timestamp: new Date(),
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              id: uuidv4(),
              sender: "user",
              text: msg,
              timestamp: new Date(),
            },
          ]);
        }
      }
    }

    if (
      cleanedMsg === "menu" ||
      cleanedMsg === "hi" ||
      cleanedMsg === "yes" ||
      cleanedMsg === "हाँ"
    ) {
      if (mainMenuHeading) {
        setMainMenuButtons(null);
        setMainMenuHeading(null);
        await handleMenuRequest();
        return;
      }
    }

    if (cleanedMsg === "no") {
      if (mainMenuHeading) {
        await handleFeedbackFlow("English");
        return;
      }

    }
    if (cleanedMsg === "नहीं") {
      if (mainMenuHeading) {
        await handleFeedbackFlow("Hindi");
        return;
      }

    }

    setInput("");
    setFaqGroups([]);
    let finalMessage = msg;

    if (isOrderIdPrefixActive && typeof msg === "string" && msg.trim().startsWith("8")) {
      finalMessage = "00" + msg.trim();
    }

    setIsBotLoading(true);
    try {
      const data = await apiClient.post("/webhook", {
        sender_id,
        message: `${finalMessage} ${"BRPL"}`,
        lastSelectedOption: effectiveLastOption,
        source: source || "web",

      }, { signal: getAbortSignal() });

      let newBotMessages = [];

      if (data?.response?.change_language) {

        setIsLanguageChangeRequested(true);

      }

      // 1. Store cleaned previous_message into states
      if (data?.response) {
        let { subsidiary, user_type, language } = data.response;

        if (subsidiary) {
          subsidiary = subsidiary.replace(/\bBRPL\b/gi, "").trim();
          setSelectedProvider(subsidiary);
        }

        if (user_type) {
          user_type = user_type.replace(/\bBRPL\b/gi, "").trim();
          setSelectedUserType(user_type);
        }

        if (language) {
          language = language.replace(/\bBRPL\b/gi, "").trim();
          setSelectedLanguage(language);
        }
      }

      if (data.response?.main_menu_heading && data.response?.main_menu_buttons) {
        if (!data.response?.ad_option) {
          // ad_option nahi hai, turant show karo
          showMainMenu(data.response.main_menu_heading, data.response.main_menu_buttons);
        } else {
          // ad_option hai, temp mein store karo
          storeMenuTemp(data.response.main_menu_heading, data.response.main_menu_buttons);
        }
      } else {
        // clear any pending delayed show and hide menu immediately
        if (mainMenuTimeoutRef.current) {
          clearTimeout(mainMenuTimeoutRef.current);
          mainMenuTimeoutRef.current = null;
        }
        setMainMenuHeading(null);
        setMainMenuButtons(null);
        setMainMenuHeadingTemp(null);
        setMainMenuButtonsTemp(null);
      }

      let botText = "";

      if (typeof data.response === "string") {
        botText = data.response;
      } else if (Array.isArray(data.response?.heading)) {
        botText = data.response.heading.join("\n\n");
      }

      // STEP 4: Reset Flags If Validated
      if (
        botText.toLowerCase().includes("ca number successfully validated") ||
        botText.toLowerCase().includes("ca number is being processed") ||
        botText.includes("सीए नंबर सत्यापित किया गया") ||
        botText.includes("ca नंबर संसाधित किया जा रहा है") ||
        botText.includes("Too many attempts. Let's start over. Click home button to start over")
      ) {
        setAwaitingCaNumber(false);
      }

      if (
        botText.toLowerCase().includes("otp validated") ||
        botText.includes("Too many attempts. Let's start over. Click home button to start over") ||
        botText.includes("ओटीपी सत्यापित किया गया") ||
        botText.includes("ओटीपी सफलतापूर्वक")
      ) {
        setAwaitingOtp(false);
      }

      if (
        botText.includes("A 6-digit One-Time Password (OTP)") ||
        botText.includes("Too many attempts. Let's start over. Click home button to start over") ||
        botText.includes("आपके द्वारा दर्ज किए गए मोबाइल नंबर पर एक ओटीपी भेजा गया है।") ||
        botText.includes("ओटीपी सफलतापूर्वक")
      ) {
        setAwaitingVisuall(false);
      }

      if (
        botText.includes("Here is the Status of") ||
        botText.includes("New connection request") ||
        botText.includes("यह रहा आपकी स्थिति रिपोर्ट") ||
        botText.includes("आपके नए कनेक्शन अनुरोध") ||
        botText.includes("कमी देखने के लिए यहाँ क्लिक करें")
      ) {
        setAwaitingOrderId(false);
      }

      if (
        botText.includes("OTP validated successfully") ||
        botText.includes("ओटीपी सफलतापूर्वक सत्यापित हो गया है।")
      ) {
        setAwaitingVisuallOtp(false);
      }

      if (
        botText.includes("New Email ID has been successfully registered") ||
        botText.includes("नई ईमेल आईडी सफलतापूर्वक पंजीकृत हो गई है") ||
        botText.includes("")
      ) {
        setEmailValidation(false);
      }

      if (
        botText?.toLowerCase().includes("please enter your ca number") ||
        botText?.toLowerCase().includes("please enter new ca number") ||
        botText?.includes("कृपया नया CA नंबर दर्ज करें।")
      ) {
        setAwaitingCaNumber(true);
      }

      if (
        botText?.includes("CA number is being processed") ||
        botText?.includes("कृपया 6-अंकों का ओटीपी दर्ज करें") ||
        botText?.includes("कृपया आगे बढ़ने के लिए इसे दर्ज करें।")
      ) {
        setAwaitingOtp(true);
      }

      if (
        botText?.includes("Please enter your email ID.") ||
        botText?.includes("Please enter new email ID.") ||
        botText?.includes("कृपया नया ईमेल आईडी दर्ज करें।") ||
        botText?.includes("कृपया अपना ईमेल आईडी दर्ज करें।")
      ) {
        setEmailValidation(true);
      }

      if (
        botText?.includes("Send OTP service is unavailable. Please try again later.") ||
        botText?.includes("ओटीपी सेवा उपलब्ध नहीं है। कृपया बाद में पुनः प्रयास करें।")
      ) {
        setDisableAllInputs(true);
      }

      const isOtpValidated =
        (typeof data.response === "string" &&
          (data.response
            .trim()
            .toLowerCase()
            .includes("otp validated for new ca number successfully") ||
            data.response
              .trim()
              .includes("नए सीए नंबर के लिए ओटीपी सफलतापूर्वक सत्यापित किया गया।"))) ||
        (Array.isArray(data.response?.heading) &&
          data.response.heading.some(
            (line) =>
              line.toLowerCase().includes("otp validated for new ca number successfully") ||
              line.includes("नए सीए नंबर के लिए ओटीपी सफलतापूर्वक सत्यापित किया गया।")
          ));

      // If user was "New Consumer", change to "Registered Consumer"
      const usertype = "Registered Consumer / पंजीकृत उपभोक्ता";

      if (isOtpValidated && selectedUserType) {
        const otpMessage = selectedLanguage.includes("हिंदी")
          ? "नए सीए नंबर के लिए ओटीपी सफलतापूर्वक सत्यापित किया गया।"
          : "OTP validated for new CA number successfully.";

        newBotMessages.push({
          // id: uuidv4(),
          id: uuidv4(),
          sender: "bot",
          text: otpMessage,
          timestamp: new Date(),
        });
        setLastBotMessage(otpMessage);

        const otpSuccessPhrases = [
          "नए सीए नंबर के लिए ओटीपी सफलतापूर्वक सत्यापित किया गया।",
          "OTP validated for new CA number successfully.",
        ];

        let updatedUserType = selectedUserType;
        if (otpSuccessPhrases.some((msg) => otpMessage.includes(msg))) {
          if (selectedUserType) {
            updatedUserType = "Registered Consumer / पंजीकृत उपभोक्ता";
            setUserType(updatedUserType);
            setSelectedUserType(updatedUserType);
          }
        }

        // --- AD MESSAGE: Always push at the end ---
        if (
          data.response?.ad_option &&
          data.response?.ad_option_submenu_name &&
          data.response?.ad_option_type
        ) {
          try {
            const submenu = encodeURIComponent(data.response.ad_option_submenu_name);
            const adType = encodeURIComponent(data.response.ad_option_type);

            const adRes = await apiClient.get(
              `/get_ad?ad_type=${adType}&chat_option=${submenu}&senderId=${encodeURIComponent(
                userId
              )}`,
              {},
              { signal: getAbortSignal() }
            );

            const ad = adRes?.data?.data || adRes?.data || adRes;
            setAdId(ad?.id);

            if (ad?.ad_image_path && ad?.ad_pdf_path) {
              newBotMessages.push({
                id: uuidv4(),
                sender: "bot",
                ad: {
                  image_url: `${BASE_URL}/${ad.ad_image_path}`,
                  pdf_url: `${BASE_URL}/${ad.ad_pdf_path}`,
                  ad_id: ad.id,
                },
                timestamp: new Date(),
              });
            }

            if (adRes?.status === false) {
              showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

              // clear temp holders
              setMainMenuHeadingTemp(null);
              setMainMenuButtonsTemp(null);
              mainMenuHeadingTempRef.current = null;
              mainMenuButtonsTempRef.current = null;
            }

            // if poll key is present in ad
            if (ad?.poll === "show_poll") {
              try {
                await handlePollFlow();
              } catch { }
            }
          } catch (err) {
            // Ignore cancelled requests
            if (err.name === 'AbortError' || err.name === 'CanceledError') {
              console.log("Ad fetch request cancelled");
              return;
            }
            console.error("Failed to load ad:", err);

            // If the ad fetch API fails or returns status:false, restore main menu
            if (err?.response?.status === 404 || err?.response?.data?.status === "fail") {
              showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

              // clear temp holders
              setMainMenuHeadingTemp(null);
              setMainMenuButtonsTemp(null);
              mainMenuHeadingTempRef.current = null;
              mainMenuButtonsTempRef.current = null;
            }
          }
        }

        setMessages((prev) => [...prev, ...newBotMessages]);

        setTimeout(async () => {
          await handleRegisterMenuRunFlow(updatedUserType);
        }, 300);

        setIsBotLoading(false);
        return;
      }

      if (
        data.response &&
        Array.isArray(data.response.buttons) &&
        Array.isArray(data.response.heading) &&
        data.response.heading.length === 0 &&
        data.response.buttons.some((btn) => /^\d+\.\s?/.test(btn))
      ) {
        const mainBtns = getMainComplaintButtons(data.response.buttons);
        setSpecialMenuMainButtons(mainBtns);
        setSpecialMenuSubButtons([]);
        setSpecialMenuParent(null);
        setLastSpecialMenuButtons(data.response.buttons);

        newBotMessages.push({
          id: uuidv4(),
          sender: "bot",
          type: "specialMenuMainButtons",
          specialMenuMainButtons: mainBtns,
          lastSpecialMenuButtons: data.response.buttons,
        });

        setButtons([]);
        setGroupedButtons(null);
        setSpecialMenuGroups([]);
        setSpecialMenuActiveIdx(null);
        setFaqGroups([]);
        setFaqActiveIndex(null);
        setShowProviderButton(false);
        setButtonIcons(data.response.icons || []);

        // --- AD MESSAGE: Always push at the end ---
        if (
          data.response?.ad_option &&
          data.response?.ad_option_submenu_name &&
          data.response?.ad_option_type
        ) {
          try {
            const submenu = encodeURIComponent(data.response.ad_option_submenu_name);
            const adType = encodeURIComponent(data.response.ad_option_type);

            const adRes = await apiClient.get(
              `/get_ad?ad_type=${adType}&chat_option=${submenu}&senderId=${encodeURIComponent(
                userId
              )}`,
              {},
              { signal: getAbortSignal() }
            );

            const ad = adRes?.data?.data || adRes?.data || adRes;
            setAdId(ad?.id);

            if (ad?.ad_image_path && ad?.ad_pdf_path) {
              newBotMessages.push({
                id: uuidv4(),
                sender: "bot",
                ad: {
                  image_url: `${BASE_URL}/${ad.ad_image_path}`,
                  pdf_url: `${BASE_URL}/${ad.ad_pdf_path}`,
                  ad_id: ad.id,
                },
                timestamp: new Date(),
              });
            }

            if (adRes?.status === false) {
              showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

              // clear temp holders
              setMainMenuHeadingTemp(null);
              setMainMenuButtonsTemp(null);
              mainMenuHeadingTempRef.current = null;
              mainMenuButtonsTempRef.current = null;
            }

            // if poll key is present in ad
            if (ad?.poll === "show_poll") {
              try {
                await handlePollFlow();
              } catch { }
            }
          } catch (err) {
            // Ignore cancelled requests
            if (err.name === 'AbortError' || err.name === 'CanceledError') {
              console.log("Ad fetch request cancelled");
              return;
            }
            console.error("Failed to load ad:", err);

            // If the ad fetch API fails or returns status:false, restore main menu
            if (err?.response?.status === 404 || err?.response?.data?.status === "fail") {
              showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

              // clear temp holders
              setMainMenuHeadingTemp(null);
              setMainMenuButtonsTemp(null);
              mainMenuHeadingTempRef.current = null;
              mainMenuButtonsTempRef.current = null;
            }
          }
        }

        setMessages((prev) => [...prev, ...newBotMessages]);
        setIsBotLoading(false);
        return;
      }

      if (isSpecialMenuResponse(data.response)) {
        if (Array.isArray(data.response.heading) && data.response.heading.length > 0) {
          newBotMessages.push({
            id: uuidv4(),
            sender: "bot",
            text: data.response.heading.join("\n\n"),
            timestamp: new Date(),
          });
          setLastBotMessage(data.response.heading.join("\n\n"));
        }

        const updatedButtons = data.response.buttons.map((btn) => {
          if (
            btn === "Virtual Customer Care Centre (BYPL) / Connect Virtually (BRPL)" ||
            btn === "वर्चुअल कस्टमर केयर सेंटर (BYPL) / वर्चुअली कनेक्ट करें (BRPL)"
          ) {
            return languageToUse.includes("हिंदी")
              ? "वर्चुअली कनेक्ट करें (BRPL)"
              : " Connect Virtually (BRPL)";
          }
          return btn;
        });

        const groups = groupButtons(updatedButtons);
        setFaqGroups([]);
        setFaqActiveIndex(null);
        setSpecialMenuGroups(groups);
        setButtonIcons(data.response.icons || []);
        setSpecialMenuActiveIdx(null);
        setButtons([]);
        setGroupedButtons(null);
        setShowProviderButton(false);

        // --- AD MESSAGE: Always push at the end ---
        if (
          data.response?.ad_option &&
          data.response?.ad_option_submenu_name &&
          data.response?.ad_option_type
        ) {
          try {
            const submenu = encodeURIComponent(data.response.ad_option_submenu_name);
            const adType = encodeURIComponent(data.response.ad_option_type);

            const adRes = await apiClient.get(
              `/get_ad?ad_type=${adType}&chat_option=${submenu}&senderId=${encodeURIComponent(
                userId
              )}`,
              {},
              { signal: getAbortSignal() }
            );

            const ad = adRes?.data?.data || adRes?.data || adRes;
            setAdId(ad?.id);

            if (ad?.ad_image_path && ad?.ad_pdf_path) {
              newBotMessages.push({
                id: uuidv4(),
                sender: "bot",
                ad: {
                  image_url: `${BASE_URL}/${ad.ad_image_path}`,
                  pdf_url: `${BASE_URL}/${ad.ad_pdf_path}`,
                  ad_id: ad.id,
                },
                timestamp: new Date(),
              });
            }

            if (adRes?.status === false) {
              showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

              // clear temp holders
              setMainMenuHeadingTemp(null);
              setMainMenuButtonsTemp(null);
              mainMenuHeadingTempRef.current = null;
              mainMenuButtonsTempRef.current = null;
            }

            // if poll key is present in ad
            if (ad?.poll === "show_poll") {
              try {
                await handlePollFlow();
              } catch { }
            }
          } catch (err) {
            // Ignore cancelled requests
            if (err.name === 'AbortError' || err.name === 'CanceledError') {
              console.log("Ad fetch request cancelled");
              return;
            }
            console.error("Failed to load ad:", err);

            // If the ad fetch API fails or returns status:false, restore main menu
            if (err?.response?.status === 404 || err?.response?.data?.status === "fail") {
              showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

              // clear temp holders
              setMainMenuHeadingTemp(null);
              setMainMenuButtonsTemp(null);
              mainMenuHeadingTempRef.current = null;
              mainMenuButtonsTempRef.current = null;
            }
          }
        }

        setMessages((prev) => [...prev, ...newBotMessages]);
        setIsBotLoading(false);
        return;
      }

      const isFaqStyle =
        data.response.buttons?.every((btn) => /^\d+\./.test(btn)) &&
        data.response.heading?.some((line) => /^\d+\./.test(line));

      if (data.response && data.response.heading?.length > 0) {
        const branchKeywords = ["Branches within", "भीतर शाखाएँ"];

        const isBranchDistanceResponse =
          data.response.buttons?.some((btn) => branchKeywords.some((km) => btn.includes(km))) &&
          data.response.heading?.some((line) => branchKeywords.some((km) => line.includes(km)));

        if (isBranchDistanceResponse) {
          newBotMessages.push({
            id: uuidv4(),
            sender: "bot",
            branchData: {
              buttons: data.response.buttons,
              rawHeadings: data.response.heading,
            },
            timestamp: new Date(),
          });
          setButtons([]);
          setGroupedButtons(null);
          setSpecialMenuGroups([]);
          setSpecialMenuActiveIdx(null);
          setFaqGroups([]);

          // --- AD MESSAGE: Always push at the end ---
          if (
            data.response?.ad_option &&
            data.response?.ad_option_submenu_name &&
            data.response?.ad_option_type
          ) {
            try {
              const submenu = encodeURIComponent(data.response.ad_option_submenu_name);
              const adType = encodeURIComponent(data.response.ad_option_type);

              const adRes = await apiClient.get(
                `/get_ad?ad_type=${adType}&chat_option=${submenu}&senderId=${encodeURIComponent(
                  userId
                )}`,
                {},
                { signal: getAbortSignal() }
              );

              const ad = adRes?.data?.data || adRes?.data || adRes;
              setAdId(ad?.id);

              if (ad?.ad_image_path && ad?.ad_pdf_path) {
                newBotMessages.push({
                  id: uuidv4(),
                  sender: "bot",
                  ad: {
                    image_url: `${BASE_URL}/${ad.ad_image_path}`,
                    pdf_url: `${BASE_URL}/${ad.ad_pdf_path}`,
                    ad_id: ad.id,
                  },
                  timestamp: new Date(),
                });
              }

              if (adRes?.status === false) {
                showMainMenu(
                  mainMenuHeadingTempRef.current,
                  mainMenuButtonsTempRef.current
                );

                // Clear temp holders
                setMainMenuHeadingTemp(null);
                setMainMenuButtonsTemp(null);
                mainMenuHeadingTempRef.current = null;
                mainMenuButtonsTempRef.current = null;
              }

              // if poll key is present in ad
              if (ad?.poll === "show_poll") {
                try {
                  await handlePollFlow();
                } catch { }
              }
            } catch (err) {
              console.error("Failed to load ad:", err);

              // If the ad fetch API fails or returns status:false, restore main menu
              if (err?.response?.status === 404 || err?.response?.data?.status === "fail") {
                showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

                // clear temp holders
                setMainMenuHeadingTemp(null);
                setMainMenuButtonsTemp(null);
                mainMenuHeadingTempRef.current = null;
                mainMenuButtonsTempRef.current = null;
              }
            }
          }

          setMessages((prev) => [...prev, ...newBotMessages]);
          setLastBotMessage(data.response.heading.join("\n\n"));
          setIsBotLoading(false);
          return;
        }

        if (!isFaqStyle) {
          setFaqGroups([]);
          setFaqActiveIndex(null);
          newBotMessages.push({
            id: uuidv4(),
            sender: "bot",
            text: data.response.heading.join("\n\n"),
            timestamp: new Date(),
          });
          setLastBotMessage(data.response.heading.join("\n\n"));
        }

        if (
          data.response.buttons?.every((btn) => /^\d+\./.test(btn)) &&
          data.response.heading.some((line) => /^\d+\./.test(line))
        ) {
          const grouped = data.response?.buttons.map((btn) => {
            const number = btn.split(".")[0];
            const allLines = [];
            const headingLines = data.response.heading;
            for (let i = 0; i < headingLines.length; i++) {
              const line = headingLines[i];
              if (line.startsWith(`${number}.`)) {
                allLines.push(line);
                let j = i + 1;
                while (j < headingLines.length && !/^\d+\./.test(headingLines[j])) {
                  allLines.push(headingLines[j]);
                  j++;
                }
                break;
              }
            }
            return {
              title: btn,
              content: allLines,
            };
          });
          newBotMessages.push({
            id: uuidv4(),
            sender: "bot",
            faqGroups: grouped,
            timestamp: new Date(),
          });

          setFaqGroups([]);
          setButtons([]);
          setGroupedButtons(null);
          setSpecialMenuGroups([]);
          setSpecialMenuActiveIdx(null);

          // --- AD MESSAGE: Always push at the end ---

          if (
            data.response?.ad_option &&
            data.response?.ad_option_submenu_name &&
            data.response?.ad_option_type
          ) {
            try {
              const submenu = encodeURIComponent(data.response.ad_option_submenu_name);
              const adType = encodeURIComponent(data.response.ad_option_type);

              const adRes = await apiClient.get(
                `/get_ad?ad_type=${adType}&chat_option=${submenu}&senderId=${encodeURIComponent(
                  userId
                )}`,
                {},
                { signal: getAbortSignal() }
              );

              const ad = adRes?.data?.data || adRes?.data || adRes;
              setAdId(ad?.id);

              if (ad?.ad_image_path && ad?.ad_pdf_path) {
                newBotMessages.push({
                  id: uuidv4(),
                  sender: "bot",
                  ad: {
                    image_url: `${BASE_URL}/${ad.ad_image_path}`,
                    pdf_url: `${BASE_URL}/${ad.ad_pdf_path}`,
                    ad_id: ad.id,
                  },
                  timestamp: new Date(),
                });
              }


              if (adRes?.status === false) {
                showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

                // clear temp holders
                setMainMenuHeadingTemp(null);
                setMainMenuButtonsTemp(null);
                mainMenuHeadingTempRef.current = null;
                mainMenuButtonsTempRef.current = null;
              }

              // if poll key is present in ad
              if (ad?.poll === "show_poll") {
                try {
                  await handlePollFlow();
                } catch { }
              }
            } catch (err) {
              console.error("Failed to load ad:", err);

              // If the ad fetch API fails or returns status:false, restore main menu
              if (err?.response?.status === 404 || err?.response?.data?.status === "fail") {
                showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

                // clear temp holders
                setMainMenuHeadingTemp(null);
                setMainMenuButtonsTemp(null);
                mainMenuHeadingTempRef.current = null;
                mainMenuButtonsTempRef.current = null;
              }
            }
          }

          setMessages((prev) => [...prev, ...newBotMessages]);
          setLastBotMessage(data.response.heading.join("\n\n"));
          setIsBotLoading(false);
          return;
        }

        if (data.response?.buttons) {
          setButtons(data.response.buttons);
          setButtonIcons(data.response.icons || []);
          setGroupedButtons(null);
          setShowProviderButton(false);
          setSpecialMenuGroups([]);
          setSpecialMenuActiveIdx(null);
        } else {
          setButtons([]);
        }
      }

      // --- AD MESSAGE: Always push at the end if not already pushed ---
      if (
        data.response?.ad_option &&
        data.response?.ad_option_submenu_name &&
        data.response?.ad_option_type
      ) {
        try {
          const submenu = encodeURIComponent(data.response.ad_option_submenu_name);
          const adType = encodeURIComponent(data.response.ad_option_type);

          const adRes = await apiClient.get(
            `/get_ad?ad_type=${adType}&chat_option=${submenu}&senderId=${encodeURIComponent(
              userId
            )}`,
            {},
            { signal: getAbortSignal() }
          );

          const ad = adRes?.data?.data || adRes?.data || adRes;
          setAdId(ad?.id);

          if (ad?.ad_image_path && ad?.ad_pdf_path) {
            newBotMessages.push({
              id: uuidv4(),
              sender: "bot",
              ad: {
                image_url: `${BASE_URL}/${ad.ad_image_path}`,
                pdf_url: `${BASE_URL}/${ad.ad_pdf_path}`,
                ad_id: ad.id,
              },
              timestamp: new Date(),
            });
          }

          if (adRes?.status === false) {
            showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

            // clear temp holders
            setMainMenuHeadingTemp(null);
            setMainMenuButtonsTemp(null);
            mainMenuHeadingTempRef.current = null;
            mainMenuButtonsTempRef.current = null;
          }

          // if poll key is present in ad
          if (ad?.poll === "show_poll") {
            try {
              await handlePollFlow();
            } catch { }
          }
        } catch (err) {
          console.error("Failed to load ad:", err);
          // If the ad fetch API fails or returns status:false, restore main menu
          if (err?.response?.status === 404 || err?.response?.data?.status === "fail") {
            showMainMenu(mainMenuHeadingTempRef.current, mainMenuButtonsTempRef.current);

            // clear temp holders
            setMainMenuHeadingTemp(null);
            setMainMenuButtonsTemp(null);
            mainMenuHeadingTempRef.current = null;
            mainMenuButtonsTempRef.current = null;
          }
        }
      }

      if (newBotMessages.length > 0) {
        setMessages((prev) => [...prev, ...newBotMessages]);
      }
    } catch {
      // Only show error if this wasn't an intentional abort (e.g., from resetChat)
      if (!isIntentionalAbortRef.current) {
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: "We are unable to connect you with BSES services. Please check your network connection",
            timestamp: new Date(),
          },
        ]);
      }
      // Reset the flag
      isIntentionalAbortRef.current = false;
    } finally {
      setIsBotLoading(false);
    }
  };

  const getSubsidiary = () => selectedProvider;

  const handleButton = async (btn) => {
    resetInactivityTimer();

    setButtons([]);
    setGroupedButtons(null);
    setSpecialMenuGroups([]);
    setSpecialMenuActiveIdx(null);
    setMainMenuButtons(null);
    setMainMenuHeading(null);

    setShowProviderButton(false);

    setIsBotLoading(true);

    if (btn === "Payment Centres") {
      setLastSelectedType("BC");
      setLocationModeKey("BC");
    } else if (btn === "Complaint Centres") {
      setLastSelectedType("CC");
      setLocationModeKey("CC");
    }

    if (btn.toLowerCase() === "share live location" || btn === "लाइव लोकेशन साझा करें") {
      setPendingLocation(true);
      setButtons([]);
      try {
        console.log('Getting location with Google Geolocation API...');
        const position = await getLocationWithGoogle();
        console.log('Google Geolocation successful:', position);

        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const type = lastSelectedType || "BC";

        // Get address from lat/lon
        console.log('Converting coordinates to address...');
        const address = await reverseGeocode(lat, lon);
        console.log('Address found:', address);

        // Store location data for confirmation
        setLocationConfirmationData({ lat, lon, type, address });

        // Check if language is Hindi
        const isHindi = selectedLanguage?.toLowerCase()?.includes("हिंदी") ||
          selectedLanguage?.toLowerCase()?.includes("hindi");

        // Show address to user with confirmation buttons
        const confirmationMessage = isHindi
          ? `आपका स्थान: ${address}\n\nक्या आप इस स्थान को साझा करना चाहते हैं?`
          : `Your location: ${address}\n\nDo you want to share this location?`;

        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: confirmationMessage,
            timestamp: new Date(),
          },
        ]);

        // Show Yes/No buttons based on language
        const confirmButtons = isHindi ? ["हाँ", "नहीं"] : ["Yes", "No"];
        setButtons(confirmButtons);

        setPendingLocation(false);
        setIsBotLoading(false);

      } catch (error) {

        if (error.name === 'AbortError' || error.name === 'CanceledError') {
          console.log("Location processing cancelled");
          return;
        }
        console.error('Google Geolocation error:', error);

        setLastBotMessage(locationTriggerMessage);
        setPendingLocation(false);
        setIsBotLoading(false);
      }
      return;
    }

    if (isLanguageChangeRequested && (btn === "English" || btn === "हिंदी")) {
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "user",
          text: btn,
          timestamp: new Date(),
        },
      ]);
      setSelectedLanguage(btn);
      setIsLanguageChangeRequested(false);

      await handleMenuRequestWithLanguage(btn);
      setIsBotLoading(false);
      return;
    }

    if (btn.toLowerCase() === "english" || btn.includes("हिंदी")) {
      setSelectedLanguage(btn);
      await sendMessage(btn, true, btn);
      setIsBotLoading(false);
      return;
    }

    if (btn.includes("New Consumer / नया उपभोक्ता") || btn.includes("नया एप्लिकेशन उपयोगकर्ता")) {
      setSelectedUserType("New Consumer / नया उपभोक्ता");
    } else if (
      btn.includes("Registered Consumer / पंजीकृत उपभोक्ता") ||
      btn.includes("पंजीकृत उपभोक्ता")
    ) {
      setSelectedUserType("Registered Consumer / पंजीकृत उपभोक्ता");
    }

    if (btn === "BSES Rajdhani") {
      setSelectedProvider("BSES Rajdhani");
      await sendMessage(btn);
      setIsBotLoading(false);
      return;
    }

    // Handle location confirmation Yes/No
    if (locationConfirmationData) {
      if (btn.toLowerCase() === "yes" || btn === "हाँ") {
        // User confirmed - send location to backend
        const { lat, lon, type } = locationConfirmationData;
        setLocationConfirmationData(null);
        setButtons([]);

        await sendMessage(`${lat},${lon} ${type}`);
        setIsBotLoading(false);
        return;
      } else if (btn.toLowerCase() === "no" || btn === "नहीं") {
        // User declined - allow manual location input
        const isHindi = selectedLanguage?.toLowerCase()?.includes("हिंदी") ||
          selectedLanguage?.toLowerCase()?.includes("hindi");

        const manualInputMessage = isHindi
          ? "कृपया अपना स्थान टाइप करें या खोजें"
          : "Please type or search your location";

        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: manualInputMessage,
            timestamp: new Date(),
          },
        ]);

        setLocationConfirmationData(null);
        setButtons([]);
        setIsBotLoading(false);
        return;
      }
    }

    if (btn.toLowerCase() === "no") {

      await handleFeedbackFlow("English");
      return;
    }

    if (btn.toLowerCase() === "नहीं") {
      await handleFeedbackFlow("Hindi");
      return;
    }

    // Default: send message
    await sendMessage(btn);

    // Hide loader after response received
    setIsBotLoading(false);
  };

  const handleFeedbackAnswer = async (answer) => {
    if (feedbackAcceptanceStep && feedbackAcceptanceQuestion) {
      setMessages((prev) => [
        ...prev,
        {
          //id: uuidv4(),
          id: uuidv4(),
          sender: "user",
          text: answer,
          timestamp: new Date(),
        },
      ]);

      if (answer === "Yes, sure" || answer === "हाँ, ज़रूर") {
        await fetchFeedbackQuestionsByType(feedbackAcceptanceQuestion.question_type);
      }

      else if (answer === "No, maybe later" || answer === "नहीं, शायद बाद में") {
        resetFeedbackState();
        setIsInputDisabled(true); // Disable input during redirect wait
        setButtons([]); // Hide all buttons
        setMainMenuButtons(null); // Clear main menu buttons
        setSpecialMenuGroups([]); // Clear special menu accordions (New Connection, Change Request, etc.)
        setGroupedButtons(null); // Clear grouped buttons
        setFaqGroups([]); // Clear FAQ accordions


        try {
          const submenu = lastSelectedOption;
          const adType = encodeURIComponent("after_feedback_ad");

          const adRes = await apiClient.get(
            `/get_ad?ad_type=${adType}&chat_option=${submenu}&senderId=${encodeURIComponent(
              userId
            )}`,
            {},
            { signal: getAbortSignal() }
          );

          const ad = adRes?.data?.data || adRes?.data || adRes;
          setAdId(ad?.id);

          if (ad?.ad_image_path && ad?.ad_pdf_path) {
            const isHindi =
              selectedLanguage?.toLowerCase()?.includes("हिंदी") ||
              selectedLanguage?.toLowerCase()?.includes("hindi");
            const thankYouMessage = isHindi
              ? "धन्यवाद! आप बाद में फीडबैक साझा कर सकते हैं।"
              : "Thank you! You can share feedback later.";

            setMessages((prev) => [
              ...prev,
              {
                id: uuidv4(),
                sender: "bot",
                ad: {
                  image_url: `${BASE_URL}/${ad.ad_image_path}`,
                  pdf_url: `${BASE_URL}/${ad.ad_pdf_path}`,
                  ad_id: ad.id,
                },
                timestamp: new Date(),
              },
            ]);

            setMessages((prev) => [
              ...prev,
              {
                id: uuidv4(),
                sender: "bot",
                text: thankYouMessage,
                timestamp: new Date(),
              },
            ]);
          }


          if (adRes?.status === false) {
            const isHindi =
              selectedLanguage?.toLowerCase()?.includes("हिंदी") ||
              selectedLanguage?.toLowerCase()?.includes("hindi");

            const thankYouMessage = isHindi
              ? "धन्यवाद! आप बाद में फीडबैक साझा कर सकते हैं। 5 सेकंड में आप मुख्य मेनू पर वापस भेज दिए जाएंगे।"
              : "Thank you! You can share feedback later. You will be redirected to the main menu in 5 seconds.";

            setMessages((prev) => [
              ...prev,
              {
                id: uuidv4(),
                sender: "bot",
                text: thankYouMessage,
                timestamp: new Date(),
              },
            ]);
          }
        } catch (err) {
          // Ignore cancelled requests
          if (err.name === 'AbortError' || err.name === 'CanceledError') {
            console.log("Feedback submit ad fetch request cancelled");
            return;
          }
          console.error("Failed to load ad for No, maybe later:", err);

          if (err?.response?.status === 404 || err?.response?.data?.status === "fail") {
            const isHindi =
              selectedLanguage?.toLowerCase()?.includes("हिंदी") ||
              selectedLanguage?.toLowerCase()?.includes("hindi");

            const thankYouMessage = isHindi
              ? "धन्यवाद! आप बाद में फीडबैक साझा कर सकते हैं।"
              : "Thank you! You can share feedback later.";

            setMessages((prev) => [
              ...prev,
              {
                id: uuidv4(),
                sender: "bot",
                text: thankYouMessage,
                timestamp: new Date(),
              },
            ]);
          }
        }

        // Redirect after 5 seconds and call menu option API
        setTimeout(async () => {
          await handleMenuRequest();
        }, 5000);
      }
      return;
    }

    const currentQ = feedbackQuestions[feedbackStep];
    setMessages((prev) => [
      ...prev,
      {
        //id: uuidv4(),
        id: uuidv4(),
        sender: "user",
        text: answer,
        timestamp: new Date(),
      },
    ]);
    const newAnswers = { ...feedbackAnswers, [currentQ.id]: answer };
    setFeedbackAnswers(newAnswers);

    if (feedbackStep < feedbackQuestions.length - 1) {
      const nextQ = feedbackQuestions[feedbackStep + 1];
      setFeedbackStep(feedbackStep + 1);
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "bot",
          text: nextQ.question,
          options: nextQ.options,
          feedback: true,
          questionId: nextQ.id,
          timestamp: new Date(),
        },
      ]);
    } else {
      const payload = {
        response: feedbackQuestions.map((q) => ({
          question: q.question,
          answer: newAnswers[q.id] || "",
        })),
        lastMessage: lastBotMessage,
        lastSelectedOption: lastSelectedOption,
        user_id: userId,
      };

      try {
        const res = await apiClient.post("/feedback/submit", payload, { signal: getAbortSignal() });
        const data = res?.data || res;

        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text:
              selectedLanguage === "हिंदी"
                ? data?.message_hindi || "आपकी बहुमूल्य प्रतिक्रिया देने के लिए धन्यवाद!"
                : data?.message || "Thank you for your valuable feedback!",
            timestamp: new Date(),
          },
        ]);

        // Show redirect message after feedback submission
        setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              id: uuidv4(),
              sender: "bot",
              text:
                selectedLanguage === "हिंदी"
                  ? "आपका सत्र समाप्त हो चुका है। आपको 5 सेकंड में होम पेज पर भेज दिया जाएगा।"
                  : "You session has been expired.You will be redirected to home in 5 seconds...",
              timestamp: new Date(),
            },
          ]);

          // Disable input and all menu buttons
          setIsInputDisabled(true);
          setButtons([]);
          setGroupedButtons(null);
          setMainMenuButtons(null);
          setSpecialMenuGroups([]);

          // Reset chat after 5 seconds
          setTimeout(() => {
            resetChat();
          }, 5000);
        }, 500);

        setIsInputDisabled(false);

        if (res?.status === "success") {
          showMainMenu(mainMenuHeadingTemp, mainMenuButtonsTemp);
          setMainMenuHeadingTemp(null);
          setMainMenuButtonsTemp(null);
        }

        if (data?.ad_option && data?.ad_option_submenu_name && data?.ad_option_type) {
          try {
            const submenu = encodeURIComponent(data.ad_option_submenu_name);
            const adType = encodeURIComponent(data.ad_option_type);

            const adRes = await apiClient.get(
              `/get_ad?ad_type=${adType}&chat_option=${submenu}&senderId=${encodeURIComponent(
                userId
              )}`,
              {},
              { signal: getAbortSignal() }
            );

            const ad = adRes?.data?.data || adRes?.data || adRes;
            setAdId(ad?.id);

            if (ad?.ad_image_path && ad?.ad_pdf_path) {
              setMessages((prev) => [
                ...prev,
                {
                  id: uuidv4(),
                  sender: "bot",
                  ad: {
                    image_url: `${BASE_URL}/${ad.ad_image_path}`,
                    pdf_url: `${BASE_URL}/${ad.ad_pdf_path}`,
                    ad_id: ad.id,
                  },
                  timestamp: new Date(),
                },
              ]);
            }

            if (ad?.poll === "show_poll") {
              try {
                await handlePollFlow();
              } catch { }
            }
          } catch (err) {
            console.error("Failed to load feedback ad:", err);

            if (err?.response?.status === 404 || err?.response?.data?.status === "fail") {
              setMainMenuHeading(mainMenuHeadingTempRef.current);
              setMainMenuButtons(mainMenuButtonsTempRef.current);

              // Clear temp menus
              setMainMenuHeadingTemp(null);
              setMainMenuButtonsTemp(null);
              mainMenuHeadingTempRef.current = null;
              mainMenuButtonsTempRef.current = null;
            }
          }
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            sender: "bot",
            text: "❌ Failed to submit feedback.",
            timestamp: new Date(),
          },
        ]);

        setIsInputDisabled(false);
      }

      setIsFeedbackActive(false);
      setFeedbackQuestions([]);
      setFeedbackStep(0);
      setFeedbackAnswers({});
    }
  };

  const handleMenuRequestWithLanguage = async (lang) => {
    if (!(lang && selectedUserType && selectedProvider)) {
      // Show validation message if required selections are missing
      const missingItems = [];
      if (!lang) missingItems.push("Language / भाषा");
      if (!selectedUserType) missingItems.push("User Type / उपयोगकर्ता प्रकार");
      if (!selectedProvider) missingItems.push("Provider / प्रदाता");

      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "bot",
          text: `Please select the following first:\nकृपया पहले निम्नलिखित का चयन करें:\n\n${missingItems.join("\n")}`,
          timestamp: new Date(),
        },
      ]);
      return;
    }

    const registeredKeywords = [
      "Registered Consumer / पंजीकृत उपभोक्ता",
      "registered",
      "reg",
      "पंजीकृत",
    ];

    // Check if selectedUserType contains any of the registered keywords
    const isRegistered = selectedUserType
      ? registeredKeywords.some((kw) => selectedUserType.toLowerCase().includes(kw.toLowerCase()))
      : false;

    const payload = {
      subsidiary: `${getSubsidiary()} BRPL`,
      user: `${selectedUserType} BRPL`,
      language: `${lang} BRPL`,
      sender_id: userId,
    };

    if (isRegistered) {
      payload.ca_number = "CA VALIDATED BRPL";
      payload.otp = "OTP VALIDATED BRPL";
    }

    const endpoint = isRegistered ? "/register_menu_run_flow" : "/menu_run_flow";
    setIsBotLoading(true);
    try {
      const res = await apiClient.post(endpoint, payload, { signal: getAbortSignal() });

      const originalButtons = res.response.buttons;

      const updatedButtons = originalButtons.map((btn) => {
        const isComboEnglish =
          btn === "Virtual Customer Care Centre (BYPL) / Connect Virtually (BRPL)";
        const isComboHindi =
          btn === "वर्चुअल कस्टमर केयर सेंटर (BYPL) / वर्चुअली कनेक्ट करें (BRPL)";

        if (isComboEnglish) {
          return "Connect Virtually (BRPL)";
        } else if (isComboHindi) {
          return "वर्चुअली कनेक्ट करें (BRPL)";
        }

        return btn;
      });

      const groups = groupButtons(updatedButtons);

      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "bot",
          text: res.response.heading.join("\n\n"),
          timestamp: new Date(),
        },
      ]);
      setLastBotMessage(res.response.heading.join("\n\n"));
      setSpecialMenuGroups(groups);
      setButtonIcons(res.response.icons || []);
      setSpecialMenuActiveIdx(null);
      setButtons([]);
      setGroupedButtons(null);
      setShowProviderButton(false);
    } catch (error) {
      // Ignore cancelled requests
      if (error.name === 'AbortError' || error.name === 'CanceledError') {
        console.log("Menu language request cancelled");
        return;
      }
      // console.error("Menu Language API error:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "bot",
          text: "Failed to load menu. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsBotLoading(false);
    }
  };

  const handleGroupedButton = (opt) => {
    setGroupedButtons(null);
    sendMessage(opt);
  };

  const handleSpecialMenuHeading = (idx) => {
    setSpecialMenuActiveIdx(idx === specialMenuActiveIdx ? null : idx);
  };


  const handleSpecialMenuOption = async (opt) => {
    resetInactivityTimer();
    setSpecialMenuActiveIdx(null);
    setSpecialMenuGroups([]);
    setLastSelectedOption(opt);
    setPendingMessage(opt);
    // setIsBotLoading(true);
    // Create a dedicated abort controller for this function
    const adAbortController = new AbortController();

    try {
      const adTriggerRes = await apiClient.post("/ad-on-menu-click", {
        lastSelectedOption: opt,
      }, { signal: adAbortController.signal });

      const adTriggerData = adTriggerRes?.data?.data || adTriggerRes?.data;

      if (
        adTriggerData?.ad_option &&
        adTriggerData?.ad_option_submenu_name &&
        adTriggerData?.ad_option_type
      ) {


        const submenu = encodeURIComponent(adTriggerData.ad_option_submenu_name);
        const adType = encodeURIComponent(adTriggerData.ad_option_type);

        const adRes = await apiClient.get(
          `/get_ad?ad_type=${adType}&chat_option=${submenu}&senderId=${encodeURIComponent(userId)}`,
          {},
          { signal: adAbortController.signal }
        );

        const ad = adRes?.data;
        setAdId(ad?.id);

        if (ad?.ad_image_path || ad?.ad_pdf_path) {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now(),
              sender: "bot",
              ad: {
                image_url: ad.ad_image_path ? `${BASE_URL}/${ad.ad_image_path}` : null,
                pdf_url: ad.ad_pdf_path ? `${BASE_URL}/${ad.ad_pdf_path}` : null,
                ad_id: ad.id,
              },
              timestamp: new Date(),
            },
          ]);
        }

      } else {
        console.log("No ad data returned from API");
      }
    } catch (err) {
      // Ignore cancelled requests
      if (err.name === 'AbortError' || err.name === 'CanceledError') {
        console.log("Ad tracking request cancelled");
        setIsBotLoading(false);
        return;
      }
      console.error("Error in ad-on-menu-click flow:", err);
    }
  };

  const handleMenuRequest = async () => {
    if (!(selectedLanguage && selectedUserType && selectedProvider)) {
      // Show validation message if required selections are missing
      const missingItems = [];
      if (!selectedLanguage) missingItems.push("Language / भाषा");
      if (!selectedUserType) missingItems.push("User Type / उपयोगकर्ता प्रकार");
      if (!selectedProvider) missingItems.push("Provider / प्रदाता");

      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "bot",
          text: `Please select the following first:\nकृपया पहले निम्नलिखित का चयन करें:\n\n${missingItems.join("\n")}`,
          timestamp: new Date(),
        },
      ]);
      return;
    }
    setMainMenuButtons(null);
    setMainMenuHeading(null);
    resetBranchAccordion();

    setGroupedButtons(null);
    setInput("");
    setShowProviderButton(true);
    setSpecialMenuGroups([]);
    setSpecialMenuActiveIdx(null);
    setFaqGroups([]);
    setFaqActiveIndex(null);
    setAwaitingCaNumber(false);
    setAwaitingOtp(false);
    setAwaitingOrderId(false);
    setAwaitingLanguageValidation(false);
    setAwaitingVisuall(false);
    setAwaitingVisuallOtp(false);
    setEmailValidation(false);
    setButtonIcons([]);
    setLastBotMessage("");
    resetBranchAccordion();
    setMainMenuButtons(null);
    setMainMenuHeading(null);
    setOtpResendCount(2);
    setDisableAllInputs(false);
    setEmailCountDown(2);
    awaitingOrderIdRef.current = false;
    awaitingLanguageValidationRef.current = false;

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }
    setSystemMessages([]);
    setInactivityStage(0);

    setFeedbackQuestions([]);
    setFeedbackStep(0);
    setFeedbackAnswers({});
    setIsFeedbackActive(false);
    resetFeedbackState();
    setCurrentPollIndex(0);
    setPollId(null);

    setPollQuestions([]);
    setPollAnswers({});



    const registeredKeywords = ["Registered Consumer / पंजीकृत उपभोक्ता", "registered", "reg"];

    // Check if selectedUserType contains any of the registered keywords
    const isRegistered = selectedUserType
      ? registeredKeywords.some((kw) => selectedUserType.toLowerCase().includes(kw.toLowerCase()))
      : false;

    // Build payload
    const payload = {
      subsidiary: `${getSubsidiary()} BRPL`,
      user: `${selectedUserType} BRPL`,
      language: `${selectedLanguage} BRPL`,
      sender_id: userId,
    };

    if (isRegistered) {
      payload.ca_number = "CA VALIDATED BRPL";
      payload.otp = "OTP VALIDATED BRPL";
    }

    const endpoint = isRegistered ? "/register_menu_run_flow" : "/menu_run_flow";

    setIsBotLoading(true);
    try {
      const res = await apiClient.post(endpoint, payload, { signal: getAbortSignal() });

      setAwaitingOrderId(false);

      const updatedButtons = res.response.buttons.map((btn) => {
        if (btn === "Virtual Customer Care Centre (BYPL) / Connect Virtually (BRPL)") {
          return "Connect Virtually (BRPL)";
        }
        if (btn === "वर्चुअल कस्टमर केयर सेंटर (BYPL) / वर्चुअली कनेक्ट करें (BRPL)") {
          return "वर्चुअली कनेक्ट करें (BRPL)";
        }
        return btn;
      });

      const groups = groupButtons(updatedButtons);

      setFaqGroups([]);
      setFaqActiveIndex(null);

      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "bot",
          text: res.response.heading.join("\n\n"),
          timestamp: new Date(),
        },
      ]);
      setLastBotMessage(res.response.heading.join("\n\n"));
      setSpecialMenuGroups(groups);
      setButtonIcons(res.response.icons || []);
      setSpecialMenuActiveIdx(null);
      setButtons([]);
      setGroupedButtons(null);
      setShowProviderButton(false);
    } catch (error) {
      // Ignore cancelled requests
      if (error.name === 'AbortError' || error.name === 'CanceledError') {
        console.log("Menu request cancelled");
        return;
      }

      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "bot",
          text: "Failed to load menu. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsBotLoading(false);
    }
  };

  const handleSend = async () => {
    resetInactivityTimer();
    if (!input.trim()) return;
    const userMsg = input.trim().toLowerCase();
    setMainMenuHeading(null);
    setMainMenuButtons(null);
    setSpecialMenuGroups([]);
    setSpecialMenuActiveIdx(null);
    setButtons([]);
    setGroupedButtons(null);
    if (userMsg === "home") {
      resetChat();
      setInput("");
      return;
    }
    if (userMsg === "hi" || userMsg === "menu" || userMsg === "हाँ" || userMsg === "yes") {
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          sender: "user",
          text: input.trim(),
          timestamp: new Date(),
        },
      ]);
      handleMenuRequest();
    } else {
      await sendMessage(input.trim());
    }
    setInput("");
  };


  const handleFeedbackTextInput = async () => {
    if (!input.trim()) return;
    await handleFeedbackAnswer(input.trim());
    setInput("");
  };

  return (
    <>
      {/* <div className="h-screen flex items-center justify-center bg-gray-100 relative font-sans"> */}
      {/* <h2 className="text-red-800 text-center font-bold text-3xl">BSES CHAT</h2> */}
      {openChat ? (
        <button
          onClick={() => {
            setOpenChat(!openChat);
            if (!openChat) setShowWelcomePopup(false);
          }}
          className="fixed bottom-6 right-6 bg-red-600 text-white h-[50px] w-[50px] rounded-full shadow-xl flex items-center justify-center transition cursor-pointer"
          title="welcome to bses rajdhani chatbot"
        >
          <IoClose size={30} />
        </button>
      ) : (
        <div
          className="relative group"
          onMouseEnter={() => setShowWelcomePopup(true)}
          onMouseLeave={() => setShowWelcomePopup(false)}
        >
          {showWelcomePopup && (
            <div className="fixed bottom-28 right-6 bg-white border border-gray-300 shadow-lg rounded-xl p-3 w-72 text-gray-800 z-50 transition-all duration-300">
              {/* X icon stays on the right */}
              <div className="flex justify-end">
                <button
                  onClick={() => setShowWelcomePopup(false)}
                  className="text-gray-400 hover:text-gray-600 transition"
                >
                  <X size={14} />
                </button>
              </div>

              {/* Text aligned left */}
              <div className="text-left">
                {/* <span className="text-lg">BSES Rajdhani</span> */}
                <p className="text-sm leading-tight mt-1">
                  Hi, I’m e-Mitra, your virtual assistant! How can I help you today?

                </p>
              </div>

              {/* Small triangle arrow */}
              <div className="absolute bottom-[-6px] right-10 w-3 h-3 bg-white border-r border-b border-gray-300 rotate-45"></div>
            </div>
          )}

          <button
            onClick={() => {
              setOpenChat(!openChat);
              if (!openChat) setShowWelcomePopup(false);
            }}
            className="chatBtnMascots fixed bottom-6 right-6 h-[100px] w-[100px] rounded-full border-4 border-white shadow-xl flex items-center justify-center cursor-pointer"
            title="Open BSES Chatbot"
          >
            <img src={chatMascotsIcon} alt="Mascots" className="chatIconMascots" />
          </button>
        </div>
      )}

      {openChat && (
        <div className="fixed bottom-20 right-6 w-[380px] bg-gradient-to-br from-[#d60000] to-[#9e0e0e] p-1 rounded-2xl shadow-2xl/30 flex flex-col min-h-[calc(80vh_-_100px)] max-h-[80vh]">
          <ChatHeader resetChat={resetChat} />

          <div className="flex-1 overflow-y-auto p-3 bg-white space-y-3 rounded-t-2xl">
            <ChatMessages
              messages={messages}
              chatRef={chatRef}
              onSend={sendMessage}
              onRemoveMenu={removeSpecialMenuMessages}
              sender_id={userId}
              adDownloadStates={adDownloadStates}
              handleAdDownload={handleAdDownload}
            />

            <BranchAccordionSection
              branchData={branchData}
              selectedDistance={selectedDistance}
              setSelectedDistance={setSelectedDistance}
              faqActiveIndex={faqActiveIndex}
              setFaqActiveIndex={setFaqActiveIndex}
              getAccordionGroups={getAccordionGroups}
            />

            <FaqAccordion
              faqGroups={faqGroups}
              activeIndex={faqActiveIndex}
              onHeadingClick={(idx) => setFaqActiveIndex((prev) => (prev === idx ? null : idx))}
            />

            <SpecialMenuGroups
              specialMenuGroups={specialMenuGroups}
              specialMenuActiveIdx={specialMenuActiveIdx}
              handleSpecialMenuHeading={handleSpecialMenuHeading}
              handleSpecialMenuOption={handleSpecialMenuOption}
              icons={buttonIcons}
            />

            <GroupedButtons
              groupedButtons={groupedButtons}
              handleGroupedButton={handleGroupedButton}
            />

            <ChatButtons
              lastMessage={messages}
              buttons={
                feedbackAcceptanceStep
                  ? feedbackAcceptanceQuestion?.options || []
                  : isFeedbackActive
                    ? feedbackQuestions[feedbackStep]?.options || []
                    : buttons
              }
              handleButton={
                feedbackAcceptanceStep
                  ? handleFeedbackAnswer
                  : isFeedbackActive
                    ? handleFeedbackAnswer
                    : handleButton
              }
              icons={buttonIcons}
              isBotLoading={isBotLoading}
              disableIcons={isFeedbackActive || feedbackAcceptanceStep}
            />

            {pollQuestions.length > 0 && currentPollIndex < pollQuestions.length && (
              <div className="mt-4 p-3 border-t border-gray-300">
                <p className="text-start latoFont font-medium px-4 py-2 rounded-xl text-[15px] border border-[#7D7878] whitespace-pre-line break-words bg-white text-gray-800 shadow max-w-[calc(100%-50px)]">
                  {pollQuestions[currentPollIndex]?.question}
                </p>

                <PollQuestion
                  question={pollQuestions[currentPollIndex]}
                  pollAnswers={pollAnswers}
                  setPollAnswers={setPollAnswers}
                  handlePollAnswer={handlePollAnswer}
                />
              </div>
            )}

            {mainMenuHeading && (
              <div className="mt-4 p-3 border-t border-gray-300">
                <p className="text-start latoFont font-medium px-4 py-2 rounded-xl text-[15px] border border-[#7D7878] whitespace-pre-line break-words  bg-white text-gray-800 shadow max-w-[calc(100%-50px)]">
                  {mainMenuHeading}
                </p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {mainMenuButtons?.map((btn, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleButton(btn)}
                      className="text-white rounded gradientBtn transition-all duration-200 px-3 py-1  font-medium  text-[15px]"
                    >
                      {btn}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {systemMessages.length > 0 && (
              <div className="mt-4 p-3 border-t border-gray-300">
                {systemMessages.map((msg, idx) => (
                  <p
                    key={idx}
                    className="text-start latoFont font-medium px-4 py-2 rounded-xl text-[15px] border border-[#7D7878]
                   whitespace-pre-line break-words bg-white text-gray-800 shadow max-w-[calc(100%-50px)]"
                  >
                    {msg.text}
                  </p>
                ))}
              </div>
            )}

            {isBotLoading && (
              <div className="flex flex-col items-center mt-3">
                <SyncLoader size={8} color="#9e0e0e" />
                {isLoadingTimeout && (
                  <p className="text-sm text-gray-600 mt-2">
                    Taking longer than usual… please wait or check your connection.
                  </p>
                )}
              </div>
            )}
          </div>

          <ChatInput
            input={input}
            setInput={setInput}
            handleSend={
              pollQuestions.length > 0 &&
                currentPollIndex < pollQuestions.length &&
                pollQuestions[currentPollIndex]?.type === "text"
                ? async () => {
                  if (!input.trim()) return;
                  await handlePollAnswer(pollQuestions[currentPollIndex].id, input.trim());
                  setInput("");
                }
                : isFeedbackActive && feedbackQuestions[feedbackStep]?.options?.length === 0
                  ? handleFeedbackTextInput
                  : handleSend
            }
            onMenuClick={handleMenuRequest}
            menuEnabled={selectedLanguage && selectedUserType && selectedProvider}
            handleFileUpload={handleFileUpload}
            lastBotMessage={lastBotMessage}
            setLastBotMessage={setLastBotMessage}
            handleLatLngExtracted={handleLatLngExtracted}
            locationModeKey={locationModeKey}
            isInputDisabled={isInputDisabled}
            resetInactivityTimer={resetInactivityTimer}
            awaitingCaNumber={awaitingCaNumber}
            awaitingOtp={awaitingOtp}
            awaitingVisuallOtp={awaitingVisuallOtp}
            awaitingVisuall={awaitingVisuall}
            awaitingOrderId={awaitingOrderId}
            emailValidation={emailValidation}
            disableAllInputs={disableAllInputs}
            selectedLanguage={selectedLanguage}
          />
        </div>
      )}
    </>
  );
}
