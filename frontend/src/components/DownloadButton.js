import React from 'react';
import { downloadZip } from '../services/api';

const DownloadButton = ({ zipUrl, disabled }) => {
  if (!zipUrl) return null;

  return (
    <button onClick={() => downloadZip(zipUrl)} disabled={disabled}>
      Download ZIP
    </button>
  );
};

export default DownloadButton;