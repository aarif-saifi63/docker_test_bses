import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/';
//  const BASE_URL= import.meta.env.VITE_ADMIN_BASE_URL;
const apiClientInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, 
});


let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};


const refreshAccessToken = async () => {
  try {
    const response = await axios.post(
      `${BASE_URL}/refresh`,
      {},
      {
        withCredentials: true, // Sends refresh_token cookie
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    return response.data;
  } catch (error) {
    throw error;
  }
};


apiClientInstance.interceptors.request.use(
  (config) => {
    // Cookie sent automatically by browser with withCredentials: true

    // Debug logging for login endpoint
    if (config.url?.includes('/users/login')) {
      console.log('[AXIOS] Login request config:');
      console.log('[AXIOS] URL:', config.baseURL + config.url);
      console.log('[AXIOS] Method:', config.method);
      console.log('[AXIOS] Headers:', config.headers);
      console.log('[AXIOS] Data:', config.data);
      console.log('[AXIOS] Data type:', typeof config.data);
      console.log('[AXIOS] Data JSON:', JSON.stringify(config.data));
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Callback for logout - will be set by AuthContext
let logoutCallback = null;

export const setLogoutCallback = (callback) => {
  logoutCallback = callback;
};

// Response interceptor for handling auth errors and token refresh
apiClientInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 errors - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => {
            return apiClientInstance(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Attempt to refresh the token
        await refreshAccessToken();

        // Process queued requests
        processQueue(null);

        // Retry the original request
        return apiClientInstance(originalRequest);
      } catch (refreshError) {
        // Refresh failed - clear auth and logout
        processQueue(refreshError, null);

        if (logoutCallback) {
          await logoutCallback();
        } else {
          localStorage.removeItem("user_details");
          window.location.href = "/login";
        }

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Handle 403 errors - trigger logout
    if (error.response?.status === 403) {
      console.log('[API] 403 Forbidden - Logging out...');

      if (logoutCallback) {
        await logoutCallback();
      } else {
        localStorage.removeItem("user_details");
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

// const get = async (url, params = {}, config = {}) => {
//   return apiClientInstance
//     .get(url, { params, ...config })
//     .then((res) => res.data);
// };

const get = async (url, params = {}, config = {}) => {
  return apiClientInstance
    .get(url, { ...config, params })
    .then((res) => res.data);
};

const post = async (url, body = {}, config = {}) => {
  return apiClientInstance
    .post(url, body, { ...config })
    .then((res) => res.data);
};

const postFile = async (url, file, body = {}, config = {}) => {
  const formData = new FormData();

  formData.append("file", file);

  for (const key in body) {
    formData.append(key, body[key]);
  }

  return apiClientInstance
    .post(url, formData, {
      ...config,
      headers: {
        ...config.headers,
        "Content-Type": "multipart/form-data",
      },
    })
    .then((res) => res.data);
};

const postFiles = async (url, files, body = {}, config = {}) => {
  const formData = new FormData();

  files.forEach((file, index) => {
    formData.append(`files[${index}]`, file);
  });

  for (const key in body) {
    formData.append(key, body[key]);
  }

  return apiClientInstance
    .post(url, formData, {
      ...config,
      headers: {
        ...config.headers,
        "Content-Type": "multipart/form-data",
      },
    })
    .then((res) => res.data);
};

const put = async (url, body = {}, config = {}) => {
  return apiClientInstance
    .put(url, body, { ...config })
    .then((res) => res.data);
};

const del = async (url, config = {}) => {
  return apiClientInstance
    .request({ method: "delete", url, ...config })
    .then((res) => res.data);
};

const apiClient = {
  get,
  post,
  put,
  delete: del,
  postFile,
  postFiles,
};

export default apiClient;