import axios from 'axios';

// Default to localhost:8000 if env variable is not set
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
    baseURL: baseURL,
    withCredentials: true,
});

export default apiClient;
