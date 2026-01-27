/**
 * Message IDs returned by the webhook in utter_message_id array.
 * These IDs map to specific message types from the backend.
 * IDs are defined by backend team - update as needed.
 */
export const MESSAGE_IDS = {
  // Language Flow
  LANGUAGE_UPDATED_EN: 2,       // English: "Language updated successfully"
  LANGUAGE_UPDATED_HI: 7,       // Hindi: "भाषा सफलतापूर्वक बदल दी गई है"

  // Order ID Flow
  ORDER_ID_PROMPT_EN: 50,       // English: "Please enter your Order ID. The Order ID starts with '008', 'AN', or 'ON'"
  ORDER_ID_PROMPT_HI: 52,       // Hindi: "कृपया अपना ऑर्डर आईडी दर्ज करें। आपका ऑर्डर आईडी '008', '8', 'AN' या 'ON' से शुरू होता है।"

  // Mobile Number Prompt Flow
  MOBILE_PROMPT_EN: 47,         // English: "Please enter your 10-digit valid mobile"
  MOBILE_PROMPT_HI: 45,         // Hindi: "कॉलबैक प्राप्त करने और आगे की सहायता के लिए कृपया अपना वैध 10 अंकों वाला मोबाइल नंबर दर्ज करें।"

  // OTP Prompt Flow
  OTP_PROMPT_EN: 48,            // English: "A 6-digit One-Time Password (OTP) has been sent to the provided mobile number."
  OTP_PROMPT_HI: 46,            // Hindi: "आपके द्वारा दर्ज किए गए मोबाइल नंबर पर एक ओटीपी भेजा गया है।"


    CA_OTP_VALIDATED_EN: 61,      // English: "OTP validated for new CA number successfully"
  CA_OTP_VALIDATED_HI: 63,      // Hindi: "नए सीए नंबर के लिए ओटीपी सफलतापूर्वक सत्यापित किया गया।"

  // Add more IDs here as user provides them
};

/**
 * Helper function to check if any of the given IDs exist in the response IDs array
 * @param {number[]} responseIds - Array of utter_message_id from webhook response
 * @param {...number} idsToCheck - One or more MESSAGE_IDS to check for
 * @returns {boolean}
 */
export function hasMessageId(responseIds, ...idsToCheck) {
  if (!Array.isArray(responseIds)) return false;
  return idsToCheck.some((id) => responseIds.includes(id));
}

/**
 * Helper function to get the last message ID from response
 * @param {number[]} responseIds - Array of utter_message_id from webhook response
 * @returns {number|null}
 */
export function getLastMessageId(responseIds) {
  if (!Array.isArray(responseIds) || responseIds.length === 0) return null;
  return responseIds[responseIds.length - 1];
}
