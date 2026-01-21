import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/';
  // const BASE_URL= import.meta.env.VITE_BASE_URL;
// Create axios instance with cookie support
const apiClientInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, 
});

// Flag to prevent multiple simultaneous refresh attempts
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

// Refresh access token when it expires
const refreshAccessToken = async () => {
  try {
    const response = await axios.post(
      `${BASE_URL}/chatbot/refresh-session`,
      {},
      {
        withCredentials: true, // Sends chatbot_refresh_token cookie
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

// Request interceptor - cookies are sent automatically
apiClientInstance.interceptors.request.use(
  (config) => {
    // Cookies (chatbot_access_token, chatbot_refresh_token) sent automatically
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handles 401 errors and auto-refreshes token
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

        await refreshAccessToken();


        processQueue(null);

  
        return apiClientInstance(originalRequest);
      } catch (refreshError) {
    
        processQueue(refreshError, null);
        console.error('Session expired, please refresh the page');
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);


export const initSession = async () => {
  try {
    const response = await apiClientInstance.post('/chatbot/init-session');

    // Backend returns sender_id and sets JWT cookies
    // (chatbot_access_token and chatbot_refresh_token)
    // Backend response structure: { data: { sender_id: "...", expires_in: 900 }, message: "...", status: true }
    if (response?.data?.data?.sender_id) {
      return response.data.data.sender_id;
    }

    throw new Error('No sender_id in response');
  } catch (error) {
    console.error('Failed to initialize session:', error);
    throw error;
  }
};


const get = async (url, params = {}, config = {}) => {
  return apiClientInstance
    .get(url, { params, ...config })
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

const del = async (url, body = {}, config = {}) => {
  return apiClientInstance
    .request({ method: "delete", url, data: body, ...config })
    .then((res) => res.data);
};

const apiClient = {
  get,
  post,
  put,
  delete: del,
  postFile,
  postFiles,
  initSession, 
};

export default apiClient;
export { BASE_URL };