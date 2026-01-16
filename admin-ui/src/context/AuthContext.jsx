import React, { createContext, useState, useEffect } from "react";
import apiClient, { setLogoutCallback } from "../services/apiClient";
import { encryptCredentials } from "../utils/rsaEncryption";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  // Only store user details (non-sensitive data)
  const getStoredUser = () => {
    try {
      const userStr = localStorage.getItem("user_details");
      return userStr ? JSON.parse(userStr) : null;
    } catch (err) {
      console.error("Failed to parse user_details:", err);
      return null;
    }
  };

  const [user, setUser] = useState(getStoredUser());
  const [loading, setLoading] = useState(true);

  const logout = async () => {
    try {
      // Call backend to clear HTTP-only cookie
      await apiClient.post("/users/logout");
    } catch (err) {
      console.error("Logout API error:", err);
      // Continue with local cleanup even if API fails
    } finally {
      // Clear local state
      setUser(null);
      localStorage.removeItem("user_details");
      window.location.href = "/login";
    }
  };

  useEffect(() => {
    // Set logout callback for apiClient interceptor
    setLogoutCallback(logout);

    const verifyAuth = async () => {
      const storedUser = getStoredUser();

      if (!storedUser) {
        setLoading(false);
        return;
      }

      try {

        const result = await apiClient.get("/get-user-permission");

        if (result.status) {
          const userDetails = result.data?.user_details;
          setUser(userDetails);
          localStorage.setItem("user_details", JSON.stringify(userDetails));
        } else {
          logout();
        }
      } catch (err) {
        console.error("Auth verification failed:", err);
        logout();
      } finally {
        setLoading(false);
      }
    };

    verifyAuth();
  }, []); // Run only once on mount

  const login = async (email_id, password) => {
    try {
      // Step 1: Attempt to encrypt credentials using RSA
      const { payload, isEncrypted } = await encryptCredentials(email_id, password);

      console.log('[LOGIN] Using encryption:', isEncrypted);
      console.log('[LOGIN] Full payload being sent:', payload);
      console.log('[LOGIN] Payload JSON:', JSON.stringify(payload, null, 2));

      // Step 2: Login request
      const loginResult = await apiClient.post("/users/login", payload);

      if (!loginResult.status) {
        return { success: false, message: loginResult.message };
      }

      // Step 3: Check if verification is required
      if (loginResult.data?.verification_required) {
        console.log('[LOGIN] Verification required, proceeding to verify...');

        const verifyResult = await apiClient.post("/users/verify-login", {
          verification_token: loginResult.data.verification_token,
          user_id: loginResult.data.user_details?.id
        });

        if (!verifyResult.status) {
          return { success: false, message: verifyResult.message || "Verification failed" };
        }

        // Step 4: Check if session is active after verification
        console.log('[LOGIN] Verify result:', verifyResult);
        if (verifyResult.data?.session_active) {
          // Use user_details from verify response if available, otherwise use from login response
          const userDetails = verifyResult.data?.user_details || loginResult.data?.user_details;

          if (!userDetails) {
            console.error('[LOGIN] No user_details found in response');
            return { success: false, message: "User details not found" };
          }

          // Store user details only (token is in HTTP-only cookie)
          setUser(userDetails);
          localStorage.setItem("user_details", JSON.stringify(userDetails));

          console.log('[LOGIN] Verification complete, session active');
          console.log('[LOGIN] User details stored:', userDetails);
          return { success: true };
        } else {
          console.log('[LOGIN] Session not active, verify result:', verifyResult);
          return { success: false, message: "Session not activated" };
        }
      } else {
        // No verification required, proceed with normal login
        const userDetails = loginResult.data?.user_details;

        // Store user details only (token is in HTTP-only cookie)
        setUser(userDetails);
        localStorage.setItem("user_details", JSON.stringify(userDetails));

        return { success: true };
      }
    } catch (err) {
      console.error("Login error:", err);
      return {
        success: false,
        message: err.response?.data?.message || "Something went wrong",
      };
    }
  };

  const updateUser = async () => {
    if (!user?.id) {
      return { success: false, message: "No user logged in" };
    }

    try {
      const result = await apiClient.get("/get-user-permission");

      if (result.status) {
        const userDetails = result.data?.user_details;

        setUser(userDetails);
        localStorage.setItem("user_details", JSON.stringify(userDetails));

        return { success: true };
      } else {
        return { success: false, message: result.message };
      }
    } catch (err) {
      console.error("Update user error:", err);
      return {
        success: false,
        message: err.response?.data?.message || "Something went wrong",
      };
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, updateUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
};