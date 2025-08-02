import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [cookieFile, setCookieFile] = useState(null);
  const [cookieStatus, setCookieStatus] = useState({ exists: false, size: 0, modified: null });
  const [urls, setUrls] = useState('');
  const [queueData, setQueueData] = useState({ items: [], counts: { waiting: 0, in_progress: 0, completed: 0, failed: 0, total: 0 } });
  const [isUploading, setIsUploading] = useState(false);
  const [isAddingUrls, setIsAddingUrls] = useState(false);

  const uploadCookie = async () => {
    if (!cookieFile) return;
    
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', cookieFile);
    
    try {
      await axios.post('/upload-cookie', formData);
      await fetchCookieStatus();
      setCookieFile(null);
      // Reset file input
      document.getElementById('cookie-input').value = '';
    } catch (error) {
      console.error('Error uploading cookie file:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const addDownloads = async () => {
    const urlList = urls.split('\n').filter(url => url.trim() !== '');
    if (urlList.length === 0) return;

    setIsAddingUrls(true);
    try {
      await axios.post('/add-downloads', urlList);
      setUrls('');
      await fetchQueueStatus();
    } catch (error) {
      console.error('Error adding downloads:', error);
    } finally {
      setIsAddingUrls(false);
    }
  };

  const fetchCookieStatus = async () => {
    try {
      const response = await axios.get('/cookie-status');
      setCookieStatus(response.data);
    } catch (error) {
      console.error('Error fetching cookie status:', error);
    }
  };

  const fetchQueueStatus = async () => {
    try {
      const response = await axios.get('/queue-status');
      setQueueData(response.data);
    } catch (error) {
      console.error('Error fetching queue status:', error);
    }
  };

  const clearQueue = async () => {
    try {
      await axios.delete('/clear-queue');
      await fetchQueueStatus();
    } catch (error) {
      console.error('Error clearing queue:', error);
    }
  };

  const removeItem = async (itemId) => {
    try {
      await axios.delete(`/remove-item/${itemId}`);
      await fetchQueueStatus();
    } catch (error) {
      console.error('Error removing item:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'waiting': return '⏳';
      case 'in_progress': return '⏬';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '❓';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'waiting': return '#fbbf24';
      case 'in_progress': return '#3b82f6';
      case 'completed': return '#10b981';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  useEffect(() => {
    fetchCookieStatus();
    fetchQueueStatus();
    
    const interval = setInterval(() => {
      fetchQueueStatus();
    }, 2000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1 className="title">
            <span className="title-icon">🎵</span>
            Music Downloader
          </h1>
          <p className="subtitle">Download music from Spotify and YouTube</p>
        </header>

        {/* Cookie Upload Section */}
        <div className="section cookie-section">
          <h2>Authentication</h2>
          <div className="cookie-upload">
            <div className="cookie-status">
              <div className={`status-indicator ${cookieStatus.exists ? 'active' : 'inactive'}`}>
                <span className="status-dot"></span>
                <span className="status-text">
                  {cookieStatus.exists ? 'Cookie file uploaded' : 'No cookie file'}
                </span>
              </div>
              {cookieStatus.exists && (
                <div className="cookie-info">
                  <span>Size: {formatFileSize(cookieStatus.size)}</span>
                  <span>Modified: {formatDate(cookieStatus.modified)}</span>
                </div>
              )}
            </div>
            
            <div className="file-input-container">
              <input
                type="file"
                id="cookie-input"
                accept=".txt"
                onChange={(e) => setCookieFile(e.target.files[0])}
                className="file-input"
              />
              <label htmlFor="cookie-input" className="file-input-label">
                📁 Choose Cookie File
              </label>
              
              <button
                onClick={uploadCookie}
                disabled={!cookieFile || isUploading}
                className={`upload-btn ${cookieFile && !isUploading ? 'ready' : ''}`}
              >
                {isUploading ? (
                  <>
                    <span className="spinner"></span>
                    Uploading...
                  </>
                ) : (
                  <>
                    ⬆️ Upload
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* URL Input Section */}
        <div className="section">
          <h2>Add Downloads</h2>
          <div className="url-input-container">
            <textarea
              value={urls}
              onChange={(e) => setUrls(e.target.value)}
              placeholder="Paste Spotify or YouTube URLs here (one per line)&#10;https://open.spotify.com/track/...&#10;https://music.youtube.com/watch?v=..."
              className="url-textarea"
              rows="6"
            />
            <button
              onClick={addDownloads}
              disabled={!urls.trim() || isAddingUrls}
              className={`add-btn ${urls.trim() && !isAddingUrls ? 'ready' : ''}`}
            >
              {isAddingUrls ? (
                <>
                  <span className="spinner"></span>
                  Adding...
                </>
              ) : (
                <>
                  ➕ Add to Queue
                </>
              )}
            </button>
          </div>
        </div>

        {/* Queue Status */}
        <div className="section">
          <div className="queue-header">
            <h2>Download Queue</h2>
            <div className="queue-actions">
              <button onClick={clearQueue} className="clear-btn">
                🗑️ Clear Completed
              </button>
            </div>
          </div>
          
          <div className="queue-stats">
            <div className="stat-card waiting">
              <span className="stat-number">{queueData.counts.waiting}</span>
              <span className="stat-label">Waiting</span>
            </div>
            <div className="stat-card in-progress">
              <span className="stat-number">{queueData.counts.in_progress}</span>
              <span className="stat-label">In Progress</span>
            </div>
            <div className="stat-card completed">
              <span className="stat-number">{queueData.counts.completed}</span>
              <span className="stat-label">Completed</span>
            </div>
            <div className="stat-card failed">
              <span className="stat-number">{queueData.counts.failed}</span>
              <span className="stat-label">Failed</span>
            </div>
          </div>

          <div className="queue-list">
            {queueData.items.length === 0 ? (
              <div className="empty-queue">
                <span className="empty-icon">📭</span>
                <p>No downloads in queue</p>
              </div>
            ) : (
              queueData.items.map((item) => (
                <div key={item.id} className={`queue-item ${item.status}`}>
                  <div className="item-info">
                    <div className="item-header">
                      <span className="status-icon" style={{ color: getStatusColor(item.status) }}>
                        {getStatusIcon(item.status)}
                      </span>
                      <span className="track-name">
                        {item.track_name || 'Unknown Track'}
                      </span>
                      <span className="download-type-badge">
                        {item.download_type}
                      </span>
                    </div>
                    <div className="item-details">
                      <span className="artist-name">
                        {item.artist_name || 'Unknown Artist'}
                      </span>
                      <span className="status-text">
                        {item.status.replace('_', ' ')}
                      </span>
                    </div>
                    {item.error_message && (
                      <div className="error-message">
                        {item.error_message}
                      </div>
                    )}
                    <div className="item-timestamps">
                      <span>Added: {formatDate(item.created_at)}</span>
                      {item.started_at && (
                        <span>Started: {formatDate(item.started_at)}</span>
                      )}
                      {item.completed_at && (
                        <span>Finished: {formatDate(item.completed_at)}</span>
                      )}
                    </div>
                  </div>
                  <div className="item-actions">
                    <button
                      onClick={() => removeItem(item.id)}
                      className="remove-btn"
                      title="Remove from queue"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;