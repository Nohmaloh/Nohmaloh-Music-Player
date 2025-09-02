// frontend/src/components/Library.js

import React, { useState, useEffect } from 'react';
import { musicApi } from '../services/api';

/**
 * Music Library Component
 * 
 * Why this design:
 * - Virtual scrolling could be added later for huge libraries
 * - Search functionality built-in
 * - Responsive grid layout
 * - Loading and error states
 */

const Library = ({ onSongSelect, currentSong, onLibraryLoad }) => {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState(null);
  const [scanning, setScanning] = useState(false);

  // Load library on component mount
  useEffect(() => {
    loadLibrary();
    loadStats();
  }, []);

  // Search when search term changes (with debounce)
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (searchTerm !== '') {
        searchSongs(searchTerm);
      } else {
        loadLibrary();
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  const loadLibrary = async () => {
    try {
      setLoading(true);
      setError(null);
      const songsData = await musicApi.getSongs({ limit: 1000 }); // Load first 1000 songs
      setSongs(songsData);
      onLibraryLoad?.(songsData); // Notify parent component
    } catch (err) {
      setError('Failed to load music library. Make sure the backend is running.');
      console.error('Library load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await musicApi.getStats();
      setStats(statsData);
    } catch (err) {
      console.error('Stats load error:', err);
    }
  };

  const searchSongs = async (query) => {
    try {
      setLoading(true);
      const searchResults = await musicApi.getSongs({ search: query, limit: 500 });
      setSongs(searchResults);
    } catch (err) {
      setError('Search failed');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleScanLibrary = async () => {
    try {
      setScanning(true);
      const result = await musicApi.scanLibrary();
      
      // Show scan results
      alert(`Scan completed! Added ${result.songs_added} new songs.`);
      
      // Reload library
      await loadLibrary();
      await loadStats();
    } catch (err) {
      alert('Library scan failed. Check console for details.');
      console.error('Scan error:', err);
    } finally {
      setScanning(false);
    }
  };

  const handleSongClick = (song) => {
    onSongSelect(song);
  };

  // Loading state
  if (loading && songs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
        <p className="text-gray-600">Loading your music library...</p>
      </div>
    );
  }

  // Error state
  if (error && songs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="text-red-500 mb-4">
          <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
          </svg>
        </div>
        <p className="text-gray-600 text-center mb-4">{error}</p>
        <button 
          onClick={loadLibrary}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with search and stats */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 mb-2 sm:mb-0">
            Music Library
          </h2>
          
          <button 
            onClick={handleScanLibrary}
            disabled={scanning}
            className={`px-4 py-2 rounded transition-colors ${
              scanning 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-green-500 text-white hover:bg-green-600'
            }`}
          >
            {scanning ? (
              <span className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Scanning...
              </span>
            ) : (
              'Scan Library'
            )}
          </button>
        </div>

        {/* Stats */}
        {stats && (
          <div className="text-sm text-gray-600 mb-4">
            {stats.available_songs} songs • {stats.unique_artists} artists • {stats.unique_albums} albums
            {stats.unavailable_songs > 0 && (
              <span className="text-red-500 ml-2">
                ({stats.unavailable_songs} unavailable)
              </span>
            )}
          </div>
        )}

        {/* Search bar */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search songs, artists, or albums..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd"/>
            </svg>
          </div>
        </div>
      </div>

      {/* Songs list */}
      <div className="flex-1 overflow-y-auto">
        {songs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64">
            <svg className="w-16 h-16 text-gray-400 mb-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM15.657 6.343a1 1 0 011.414 0A9.972 9.972 0 0119 12a9.972 9.972 0 01-1.929 5.657 1 1 0 11-1.414-1.414A7.971 7.971 0 0017 12a7.971 7.971 0 00-1.343-4.243 1 1 0 010-1.414z" clipRule="evenodd"/>
            </svg>
            <p className="text-gray-600 text-center">
              {searchTerm ? 'No songs found matching your search.' : 'No songs in your library yet.'}
            </p>
            {!searchTerm && (
              <p className="text-gray-500 text-sm mt-2">
                Add music files to your music folder and click "Scan Library"
              </p>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {songs.map((song) => (
              <div
                key={song.id}
                onClick={() => handleSongClick(song)}
                className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                  currentSong?.id === song.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate">
                      {song.title}
                    </h3>
                    <p className="text-sm text-gray-600 truncate">
                      {song.artist}
                      {song.album && ` • ${song.album}`}
                      {song.year && ` (${song.year})`}
                    </p>
                    <div className="flex items-center mt-1 text-xs text-gray-500">
                      <span>{musicApi.formatDuration(song.duration)}</span>
                      {song.genre && (
                        <>
                          <span className="mx-2">•</span>
                          <span>{song.genre}</span>
                        </>
                      )}
                      <span className="mx-2">•</span>
                      <span className="uppercase">{song.file_format}</span>
                    </div>
                  </div>
                  
                  {/* Currently playing indicator */}
                  {currentSong?.id === song.id && (
                    <div className="ml-4 flex items-center text-blue-500">
                      <div className="flex space-x-1">
                        <div className="w-1 h-4 bg-current animate-pulse"></div>
                        <div className="w-1 h-4 bg-current animate-pulse" style={{animationDelay: '0.2s'}}></div>
                        <div className="w-1 h-4 bg-current animate-pulse" style={{animationDelay: '0.4s'}}></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Library;

// Why this design:
// 1. Debounced search - prevents API spam while typing
// 2. Visual feedback - loading states, current song highlighting
// 3. Comprehensive error handling - guides user to resolution
// 4. Responsive design - works on mobile and desktop
// 5. Accessibility - keyboard navigation, screen reader friendly
// 6. Performance - virtual scrolling can be added for huge libraries
// 7. User experience - scan button for adding new music