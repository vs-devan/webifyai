import React from 'react';

const Preview = ({ previewUrl, loading }) => {
  if (loading) return <div className="loading">Loading preview...</div>;
  if (!previewUrl) return null;

  return (
    <div className="preview-container">
      <iframe src={previewUrl} title="Website Preview" />
    </div>
  );
};

export default Preview;