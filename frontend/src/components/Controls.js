// frontend/src/components/Controls.js

import React, { useState, useRef, useEffect } from 'react';
import { musicApi } from '../services/api';

/**
 * Music Player Controls Component
 * 
 * Why separate component: Encapsulates all audio logic, reusable
 * Why useRef for audio: Direct DOM manipulation needed for audio control
 * Why useState for UI: React state for UI updates and progress tracking
 */

const Controls = ({ currentSong, onSongEnd, onTimeUpdate }) => {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.7);
  const [loading, setLoading] = useState(false);

  // Load new song when currentSong changes
  useEffect(() => {
    if (currentSong && audioRef.current) {
      setLoading(true);
      const audioUrl = musicApi.getAudioUrl(currentSong.id);
      audioRef.current.src = audioUrl;
      audioRef.current.load(); // Force reload of audio element
    }
  }, [currentSong]);

  // Audio event handlers
  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
      setLoading(false);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      const time = audioRef.current.currentTime;
      setCurrentTime(time);
      // Notify parent component of time updates (for visualizations, etc.)
      onTimeUpdate?.(time, duration);
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
    onSongEnd?.(); // Notify parent to play next song
  };

  const handleCanPlay = () => {
    setLoading(false);
  };

  const handleError = (e) => {
    console.error('Audio error:', e);
    setLoading(false);
    setIsPlaying(false);
  };

  // Control functions
  const togglePlayPause = () => {
    if (!audioRef.current || !currentSong) return;

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play()
        .then(() => setIsPlaying(true))
        .catch(err => {
          console.error('Playback failed:', err);
          setIsPlaying(false);
        });
    }
  };

  const handleSeek = (e) => {
    if (!audioRef.current || !duration) return;
    
    const progressBar = e.currentTarget;
    const clickPosition = e.nativeEvent.offsetX;
    const progressBarWidth = progressBar.offsetWidth;
    const newTime = (clickPosition / progressBarWidth) * duration;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  };

  // Calculate progress percentage
  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="bg-white border-t border-gray-200 p-4">
      {/* Hidden audio element */}
      <audio
        ref={audioRef}
        onLoadedMetadata={handleLoadedMetadata}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleEnded}
        onCanPlay={handleCanPlay}
        onError={handleError}
        preload="metadata"
      />

      {/* Progress bar - Topmost */}
      <div className="mb-4">
        <div 
          className="w-full h-2 bg-gray-200 rounded-full cursor-pointer relative"
          onClick={handleSeek}
        >
          <div 
            className="h-2 bg-blue-500 rounded-full transition-all duration-100"
            style={{ width: `${progressPercentage}%` }}
          />
          {/* Progress indicator */}
          <div 
            className="absolute top-0 w-4 h-4 bg-blue-500 rounded-full shadow-lg transform -translate-y-1 -translate-x-2 cursor-pointer"
            style={{ left: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Main control row */}
      <div className="flex items-center justify-between">
        {/* Left section: Play controls and timer */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          {/* Previous button (placeholder for future) */}
          <button 
            className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
            disabled
          >
            <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8.445 14.832A1 1 0 0010 14v-2.798l5.445 3.63A1 1 0 0017 14V6a1 1 0 00-1.555-.832L10 8.798V6a1 1 0 00-1.555-.832l-6 4a1 1 0 000 1.664l6 4z"/>
            </svg>
          </button>

          {/* Play/Pause button */}
          <button 
            className={`p-2 rounded-full transition-all ${
              currentSong && !loading
                ? 'bg-blue-500 hover:bg-blue-600 text-white shadow-lg'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
            onClick={togglePlayPause}
            disabled={!currentSong || loading}
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : isPlaying ? (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd"/>
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd"/>
              </svg>
            )}
          </button>

          {/* Next button (placeholder for future) */}
          <button 
            className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
            disabled
          >
            <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4.555 5.168A1 1 0 003 6v8a1 1 0 001.555.832L10 11.202V14a1 1 0 001.555.832l6-4a1 1 0 000-1.664l-6-4A1 1 0 0010 6v2.798l-5.445-3.63z"/>
            </svg>
          </button>

          {/* Time display */}
          <div className="text-xs text-gray-500 whitespace-nowrap">
            <span>{musicApi.formatDuration(currentTime)}</span>
            <span className="mx-1">/</span>
            <span>{musicApi.formatDuration(duration)}</span>
          </div>
        </div>

        {/* Middle section: Song details */}
        <div className="flex-1 text-center px-4 min-w-0">
          {currentSong ? (
            <div>
              <h3 className="font-semibold text-gray-900 truncate text-sm">
                {currentSong.title}
              </h3>
              <p className="text-xs text-gray-600 truncate">
                {currentSong.artist} • {currentSong.album}
              </p>
            </div>
          ) : (
            <div className="text-sm text-gray-400">
              No song selected
            </div>
          )}
        </div>

        {/* Right section: Volume control */}
        <div className="flex items-center space-x-2 flex-shrink-0">
          <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM15.657 6.343a1 1 0 011.414 0A9.972 9.972 0 0119 12a9.972 9.972 0 01-1.929 5.657 1 1 0 11-1.414-1.414A7.971 7.971 0 0017 12a7.971 7.971 0 00-1.343-4.243 1 1 0 010-1.414z" clipRule="evenodd"/>
          </svg>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={handleVolumeChange}
            className="w-20 h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
};

export default Controls;

// Why this approach:
// 1. Native HTML5 audio - reliable, cross-browser support
// 2. Ref for direct audio control - React state for UI updates
// 3. Comprehensive error handling - graceful degradation
// 4. Accessible controls - keyboard and screen reader friendly
// 5. Visual feedback - loading states, progress indication
// 6. Future-proof - easy to add prev/next functionality
// 7. Responsive layout - flexbox ensures proper spacing and alignment