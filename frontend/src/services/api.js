// frontend/src/services/api.js

import axios from 'axios';

// Create axios instance with base configuration
// Why axios: Better error handling, request/response interceptors, automatic JSON parsing
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 second timeout for large files
});

// Request interceptor - add common headers
api.interceptors.request.use(
  (config) => {
    // Add any common headers here (auth tokens, etc.)
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API service functions
export const musicApi = {
  
  // Get songs from library with optional search and pagination
  async getSongs(params = {}) {
    const { limit = 100, offset = 0, search = '' } = params;
    const response = await api.get('/songs', {
      params: { limit, offset, search: search || undefined }
    });
    return response.data;
  },

  // Get detailed info about specific song
  async getSong(songId) {
    const response = await api.get(`/songs/${songId}`);
    return response.data;
  },

  // Get library statistics
  async getStats() {
    const response = await api.get('/stats');
    return response.data;
  },

  // Trigger music library scan
  async scanLibrary() {
    const response = await api.post('/scan');
    return response.data;
  },

  // Get audio stream URL for a song
  getAudioUrl(songId) {
    return `${api.defaults.baseURL}/audio/${songId}`;
  },

  // Utility: Format duration from seconds to MM:SS
  formatDuration(seconds) {
    if (!seconds) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  },

  // Utility: Get file size in human readable format
  formatFileSize(bytes) {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }
};

// Export default for convenience
export default musicApi;

// Why this structure:
// 1. Centralized API logic - all backend calls in one place
// 2. Error handling - consistent error management across the app
// 3. Utility functions - common formatting operations
// 4. Easy to extend - add new endpoints here
// 5. Environment aware - works in development and production