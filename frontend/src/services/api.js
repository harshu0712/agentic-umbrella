import axios from "axios";

// ✅ Base API instance
const api = axios.create({
  baseURL: "",   // 🔥 FIXED
  headers: {
    "Content-Type": "application/json",
  },
});

// ✅ Request interceptor (attach token if exists)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// ✅ Response interceptor (handle token refresh)
api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config;

    // 🔁 Handle 401 (token expired)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");

        if (!refreshToken) {
          throw new Error("No refresh token available");
        }

        // 🔄 Refresh token API (update if needed)
        const response = await axios.post(
          "http://127.0.0.1:8000/api/v1/auth/token/refresh/",
          {
            refresh: refreshToken,
          }
        );

        const { access } = response.data;

        // 💾 Save new token
        localStorage.setItem("access_token", access);

        // 🔁 Retry original request
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);

      } catch (refreshError) {
        // ❌ If refresh fails → logout
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;