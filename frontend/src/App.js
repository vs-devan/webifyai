import React, { useState, useEffect } from 'react';
import InputForm from './components/InputForm';
import Preview from './components/Preview';
import DownloadButton from './components/DownloadButton';
import { checkStatus } from './services/api';

function App() {
  const [projectId, setProjectId] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [zipUrl, setZipUrl] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = (id) => {
    setProjectId(id);
    setLoadingPreview(true);
    setError(null);
  };

  useEffect(() => {
    if (!projectId) return;

    const pollStatus = setInterval(async () => {
      try {
        const { status, preview_url, zip_url } = await checkStatus(projectId);
        if (status === 'ready') {
          setPreviewUrl(preview_url);
          setZipUrl(zip_url);
          setLoadingPreview(false);
          clearInterval(pollStatus);
        }
      } catch (err) {
        setError(err.message);
        setLoadingPreview(false);
        clearInterval(pollStatus);
      }
    }, 5000); // Poll every 5s

    return () => clearInterval(pollStatus);
  }, [projectId]);

  return (
    <div>
      <div className="navbar">WebGenAI - Create Websites with AI</div>
      <div className="container">
        <InputForm onGenerate={handleGenerate} />
        <Preview previewUrl={previewUrl} loading={loadingPreview} />
        <DownloadButton zipUrl={zipUrl} disabled={loadingPreview} />
        {error && <div className="error">{error}</div>}
      </div>
    </div>
  );
}

export default App;