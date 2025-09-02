// frontend/src/App.js

import React, { useState, useEffect } from 'react';
import Library from './components/Library';
import Controls from './components/Controls';
import FocusControls from './components/focus/FocusControls'; // Import our new component
import './index.css'; // Tailwind CSS

/**
 * Main App Component
 * 
 * State Management Strategy:
 * - currentSong: Currently selected/playing song
 * - library: All songs for potential future features (playlists, etc.)
 * - Simple prop drilling for now, can upgrade to Context/Redux later
 */

function App() {
  const [currentSong, setCurrentSong] = useState(null);
  const [library, setLibrary] = useState([]);
  const [currentSongIndex, setCurrentSongIndex] = useState(-1);
  const [focusExpanded, setFocusExpanded] = useState(false); // New state for focus UI expansion

  // Handle song selection from library
  const handleSongSelect = (song) => {
    setCurrentSong(song);
    
    // Find song index for future prev/next functionality
    const songIndex = library.findIndex(s => s.id === song.id);
    setCurrentSongIndex(songIndex);
  };

  // Handle when current song ends (future: auto-play next)
  const handleSongEnd = () => {
    console.log('Song ended - could auto-play next song here');
    // Future implementation:
    // if (currentSongIndex < library.length - 1) {
    //   const nextSong = library[currentSongIndex + 1];
    //   handleSongSelect(nextSong);
    // }
  };

  // Handle time updates (future: visualizations, progress saving)
  const handleTimeUpdate = (currentTime, duration) => {
    // Future implementation: save progress, update visualizations
    // console.log('Time update:', currentTime, duration);
  };

  // Handle library load
  const handleLibraryLoad = (songs) => {
    setLibrary(songs);
  };

  // Handle focus mode request (placeholder for now)
  const handleFocusRequest = (focusParams) => {
    console.log('Focus mode requested with parameters:', focusParams);
    // TODO: In next steps, this will:
    // 1. Call the backend API to start processing
    // 2. Show processing overlay
    // 3. Poll for completion
    // 4. Switch to focus audio when ready
    alert(`Focus mode requested!\nIntensity: ${focusParams.focusIntensity}%\nTarget BPM: ${focusParams.targetBpm || 'Auto'}\nPreset: ${focusParams.preset}`);
  };

  // Handle focus button toggle
  const handleFocusToggle = () => {
    setFocusExpanded(!focusExpanded);
  };

  // Keyboard shortcuts (future enhancement)
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Space bar: play/pause (when not typing in input)
      if (event.code === 'Space' && event.target.tagName !== 'INPUT') {
        event.preventDefault();
        // Could trigger play/pause here
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {/* Logo/Icon */}
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM15.657 6.343a1 1 0 011.414 0A9.972 9.972 0 0119 12a9.972 9.972 0 01-1.929 5.657 1 1 0 11-1.414-1.414A7.971 7.971 0 0017 12a7.971 7.971 0 00-1.343-4.243 1 1 0 010-1.414z" clipRule="evenodd"/>
              </svg>
            </div>
            
            <div>
              <h1 className="text-xl font-bold text-gray-900">Focus Music Player</h1>
              <p className="text-sm text-gray-600">
                {currentSong ? 'Now Playing' : 'Select a song to start'}
              </p>
            </div>
          </div>

          {/* Future: User menu, settings, etc. */}
          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Main content area */}
      <main className="flex-1 flex overflow-hidden">
        
        {/* Left sidebar - Library */}
        <div className="w-1/2 lg:w-2/5 xl:w-1/3 bg-white border-r border-gray-200 flex flex-col">
          <Library 
            onSongSelect={handleSongSelect}
            currentSong={currentSong}
            onLibraryLoad={handleLibraryLoad}
          />
        </div>

        {/* Right panel - Player and future focus controls */}
        <div className="flex-1 flex flex-col">
          
          {/* Main player area */}
          <div className="flex-1 flex flex-col bg-gradient-to-br from-gray-50 to-gray-100">
            {currentSong ? (
              <div className={`flex-1 transition-all duration-500 ease-in-out ${focusExpanded ? 'p-6' : 'flex items-center justify-center p-8'}`}>
                
                {/* Compact Layout (Default) */}
                {!focusExpanded && (
                  <div className="text-center max-w-md mx-auto">
                    {/* Large album art placeholder */}
                    <div className="w-48 h-48 mx-auto mb-6 bg-gradient-to-br from-blue-400 to-blue-600 rounded-2xl shadow-2xl flex items-center justify-center album-art-transition transform transition-transform duration-300 hover:scale-105">
                      <svg className="w-24 h-24 text-white opacity-80" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM15.657 6.343a1 1 0 011.414 0A9.972 9.972 0 0119 12a9.972 9.972 0 01-1.929 5.657 1 1 0 11-1.414-1.414A7.971 7.971 0 0017 12a7.971 7.971 0 00-1.343-4.243 1 1 0 010-1.414z" clipRule="evenodd"/>
                      </svg>
                    </div>

                    {/* Song info */}
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">{currentSong.title}</h2>
                    <p className="text-lg text-gray-600 mb-2">{currentSong.artist}</p>
                    {currentSong.album && (
                      <p className="text-md text-gray-500 mb-6">{currentSong.album}</p>
                    )}

                    {/* Compact Focus Button */}
                    <button
                      onClick={handleFocusToggle}
                      className="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
                    >
                      <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd"/>
                      </svg>
                      Focus Mode
                    </button>
                  </div>
                )}

                {/* Expanded Layout */}
                {focusExpanded && (
                  <div className="h-full flex flex-col">
                    {/* Top bar with compact song info */}
                    <div className="flex items-center mb-6 pb-4 border-b border-gray-200">
                      {/* Small album art */}
                      <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg shadow-lg flex items-center justify-center flex-shrink-0 album-art-transition">
                        <svg className="w-8 h-8 text-white opacity-80" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM15.657 6.343a1 1 0 011.414 0A9.972 9.972 0 0119 12a9.972 9.972 0 01-1.929 5.657 1 1 0 11-1.414-1.414A7.971 7.971 0 0017 12a7.971 7.971 0 00-1.343-4.243 1 1 0 010-1.414z" clipRule="evenodd"/>
                        </svg>
                      </div>
                      
                      {/* Compact song details */}
                      <div className="ml-4 flex-1 min-w-0">
                        <h3 className="text-lg font-semibold text-gray-900 truncate">{currentSong.title}</h3>
                        <p className="text-sm text-gray-600 truncate">{currentSong.artist}</p>
                      </div>

                      {/* Collapse button */}
                      <button
                        onClick={handleFocusToggle}
                        className="ml-4 p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Collapse Focus Mode"
                      >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd"/>
                        </svg>
                      </button>
                    </div>

                    {/* Expanded focus controls */}
                    <div className="flex-1">
                      <FocusControls 
                        currentSong={currentSong}
                        isEnabled={true}
                        onFocusRequest={handleFocusRequest}
                        layout="expanded" // Pass layout prop to component
                      />
                    </div>
                  </div>
                )}

              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-center text-gray-500">
                <div>
                  <svg className="w-24 h-24 mx-auto mb-4 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM15.657 6.343a1 1 0 011.414 0A9.972 9.972 0 0119 12a9.972 9.972 0 01-1.929 5.657 1 1 0 11-1.414-1.414A7.971 7.971 0 0017 12a7.971 7.971 0 00-1.343-4.243 1 1 0 010-1.414z" clipRule="evenodd"/>
                  </svg>
                  <h2 className="text-xl font-semibold mb-2">Welcome to Focus Music Player</h2>
                  <p className="mb-4">Select a song from your library to start listening</p>
                  <p className="text-sm text-gray-400">
                    Click Focus Mode to transform any song for better concentration
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Bottom player controls - always visible when song is selected */}
      <div className="bg-white border-t border-gray-200">
        <Controls 
          currentSong={currentSong}
          onSongEnd={handleSongEnd}
          onTimeUpdate={handleTimeUpdate}
        />
      </div>
    </div>
  );
}

export default App;

// Why this architecture:
// 1. Single source of truth - App manages global state
// 2. Component composition - each component has single responsibility  
// 3. Future-ready - easy to add Context, routing, more features
// 4. Responsive layout - works on different screen sizes
// 5. Visual hierarchy - clear information architecture
// 6. Extensible - placeholder areas for future focus mode features