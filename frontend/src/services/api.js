import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const generateProject = async (description) => {
  try {
    const response = await axios.post(`${API_URL}/api/generate`, { description });
    return response.data; // { project_id, message }
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Generation failed');
  }
};

export const checkStatus = async (projectId) => {
  try {
    const response = await axios.get(`${API_URL}/api/preview/${projectId}`);
    return response.data; // { status, preview_url, zip_url }
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Status check failed');
  }
};

export const downloadZip = (zipUrl) => {
  window.location.href = zipUrl; // Trigger download
};