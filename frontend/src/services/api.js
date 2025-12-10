import axios from 'axios';

// Use environment variable for production, fallback to /api for local dev with proxy
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

/**
 * Analyze a poker spot using GTO lookup
 * @param {Object} data - { hero_position, villain_position, stack, hand }
 * @returns {Promise} API response
 */
export const analyzeSpot = async (data) => {
    const response = await api.post('/analyze-spot', data);
    return response.data;
};

/**
 * Calculate equity between two hands
 * @param {Object} data - { hero_hand, villain_hand, board }
 * @returns {Promise} API response
 */
export const calculateEquity = async (data) => {
    const response = await api.post('/equity', data);
    return response.data;
};

export default api;
