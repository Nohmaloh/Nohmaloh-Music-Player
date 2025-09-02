// frontend/src/components/focus/FocusControls.js

import React, { useState } from 'react';

/**
 * Focus Controls Component - Phase 2B Step 1
 * 
 * Basic UI controls for focus mode processing
 * 
 * Why start here:
 * - Pure UI component, no backend dependency
 * - Immediate visual feedback
 * - Foundation for all other focus functionality
 * - Easy to test and iterate on
 */

const FocusControls = ({ 
  currentSong, 
  isEnabled = true,
  onFocusRequest = () => {}, // Placeholder callback
  layout = "vertical" // New prop: "vertical" (default) or "expanded"
}) => {
  // Local state for UI controls
  const [focusIntensity, setFocusIntensity] = useState(50);
  const [targetBpm, setTargetBpm] = useState(0); // 0 = auto
  const [selectedPreset, setSelectedPreset] = useState('custom');

  // Focus intensity presets for quick selection
  // Why presets? Makes it easier for users to choose good settings
  const presets = [
    { id: 'light', name: 'Light Work', intensity: 25, bpm: 0, description: 'Subtle changes, keeps energy' },
    { id: 'study', name: 'Deep Study', intensity: 65, bpm: 0, description: 'Reduced distractions' },
    { id: 'coding', name: 'Coding', intensity: 60, bpm: 70, description: 'Steady rhythm' },
    { id: 'meditation', name: 'Meditation', intensity: 85, bpm: 60, description: 'Very calm and ambient' },
    { id: 'custom', name: 'Custom', intensity: focusIntensity, bpm: targetBpm, description: 'Your settings' }
  ];

  // Handle preset selection
  const handlePresetChange = (preset) => {
    setSelectedPreset(preset.id);
    if (preset.id !== 'custom') {
      setFocusIntensity(preset.intensity);
      setTargetBpm(preset.bpm);
    }
  };

  // Handle manual slider changes (switches to custom)
  const handleIntensityChange = (value) => {
    setFocusIntensity(value);
    setSelectedPreset('custom');
  };

  const handleBpmChange = (value) => {
    setTargetBpm(value);
    setSelectedPreset('custom');
  };

  // Handle focus mode button click
  const handleFocusClick = () => {
    console.log('Focus mode requested:', {
      songId: currentSong?.id,
      focusIntensity,
      targetBpm,
      preset: selectedPreset
    });
    
    // Call parent callback with focus parameters
    onFocusRequest({
      focusIntensity,
      targetBpm,
      preset: selectedPreset
    });
  };

  // Don't render the "no song" state in expanded layout (handled by parent)
  if (!currentSong && layout === "vertical") {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center">
        <div className="text-gray-400 mb-2">
          <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd"/>
          </svg>
        </div>
        <p className="text-gray-600 text-sm">Select a song to access Focus Mode</p>
      </div>
    );
  }

  // Vertical layout (original compact design)
  if (layout === "vertical") {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        {/* Header */}
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Focus Mode</h3>
          <p className="text-sm text-gray-600">
            Transform "{currentSong.title}" for better concentration
          </p>
        </div>

        {/* Quick Presets */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Quick Presets
          </label>
          <div className="grid grid-cols-2 gap-2">
            {presets.filter(p => p.id !== 'custom').map((preset) => (
              <button
                key={preset.id}
                onClick={() => handlePresetChange(preset)}
                className={`p-3 text-left rounded-lg border transition-colors ${
                  selectedPreset === preset.id
                    ? 'border-blue-500 bg-blue-50 text-blue-900'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="font-medium text-sm">{preset.name}</div>
                <div className="text-xs text-gray-600 mt-1">{preset.description}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {preset.intensity}% intensity
                  {preset.bpm > 0 && ` • ${preset.bpm} BPM`}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Custom Controls */}
        <div className="space-y-4">
          {/* Focus Intensity Slider */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">
                Focus Intensity
              </label>
              <span className="text-sm text-gray-600">{focusIntensity}%</span>
            </div>
            
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={focusIntensity}
              onChange={(e) => handleIntensityChange(parseInt(e.target.value))}
              disabled={!isEnabled}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Minimal</span>
              <span>Moderate</span>
              <span>Maximum</span>
            </div>
          </div>

          {/* Target BPM Control */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">
                Target BPM
              </label>
              <span className="text-sm text-gray-600">
                {targetBpm === 0 ? 'Auto' : `${targetBpm} BPM`}
              </span>
            </div>
            
            <input
              type="range"
              min="0"
              max="120"
              step="5"
              value={targetBpm}
              onChange={(e) => handleBpmChange(parseInt(e.target.value))}
              disabled={!isEnabled}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Auto</span>
              <span>60 BPM</span>
              <span>120 BPM</span>
            </div>
          </div>
        </div>

        {/* Processing Info */}
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
              </svg>
            </div>
            <div className="ml-3">
              <h4 className="text-sm font-medium text-blue-900">What Focus Mode Does</h4>
              <ul className="mt-2 text-sm text-blue-800 space-y-1">
                <li>• Separates vocals from instruments using AI</li>
                <li>• Reduces vocal prominence by up to 70%</li>
                <li>• Slows tempo for a calmer feel</li>
                <li>• Softens distracting frequencies</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={handleFocusClick}
          disabled={!isEnabled}
          className={`w-full py-3 px-4 rounded-lg font-semibold transition-all ${
            isEnabled
              ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          🎯 Create Focus Version
        </button>

        {/* Estimated Processing Time */}
        {currentSong && (
          <div className="text-center">
            <p className="text-xs text-gray-500">
              Estimated processing time: ~{Math.ceil((currentSong.duration || 180) / 60)} minutes
            </p>
          </div>
        )}
      </div>
    );
  }

  // Expanded horizontal layout - IMPROVED VERSION
  return (
    <div className="h-full max-h-screen overflow-hidden flex flex-col">
      {/* Compact Header */}
      <div className="text-center py-4 border-b border-gray-200">
        <h3 className="text-lg font-bold text-gray-900">Focus Mode Configuration</h3>
        <p className="text-sm text-gray-600 mt-1">
          Customize how "{currentSong?.title}" will be transformed for better concentration
        </p>
      </div>

      {/* Main content with controlled height */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
            
            {/* Left: Presets */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-gray-900">Quick Presets</h4>
              <div className="grid grid-cols-1 gap-3">
                {presets.filter(p => p.id !== 'custom').map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => handlePresetChange(preset)}
                    className={`p-4 text-left rounded-lg border transition-all duration-200 ${
                      selectedPreset === preset.id
                        ? 'border-blue-500 bg-blue-50 text-blue-900 shadow-md ring-2 ring-blue-200'
                        : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50 hover:shadow-sm'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-semibold text-sm">{preset.name}</div>
                      <div className={`text-xs font-bold px-2 py-1 rounded-full ${
                        selectedPreset === preset.id ? 'bg-blue-200 text-blue-800' : 'bg-gray-200 text-gray-600'
                      }`}>
                        {preset.intensity}%
                      </div>
                    </div>
                    <div className="text-xs text-gray-600 mb-1">{preset.description}</div>
                    <div className="text-xs text-gray-500">
                      {preset.bpm > 0 ? `${preset.bpm} BPM` : 'Auto BPM'}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Center: Custom controls */}
            <div className="space-y-6">
              <h4 className="text-lg font-semibold text-gray-900">Custom Settings</h4>
              
              {/* Focus Intensity Slider */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex justify-between items-center mb-3">
                  <label className="text-sm font-semibold text-gray-700">
                    Focus Intensity
                  </label>
                  <span className="text-lg font-bold text-blue-600">{focusIntensity}%</span>
                </div>
                
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={focusIntensity}
                  onChange={(e) => handleIntensityChange(parseInt(e.target.value))}
                  disabled={!isEnabled}
                  className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>Minimal</span>
                  <span>Balanced</span>
                  <span>Maximum</span>
                </div>
              </div>

              {/* Target BPM Control */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex justify-between items-center mb-3">
                  <label className="text-sm font-semibold text-gray-700">
                    Target Tempo
                  </label>
                  <span className="text-lg font-bold text-blue-600">
                    {targetBpm === 0 ? 'Auto' : `${targetBpm} BPM`}
                  </span>
                </div>
                
                <input
                  type="range"
                  min="0"
                  max="120"
                  step="5"
                  value={targetBpm}
                  onChange={(e) => handleBpmChange(parseInt(e.target.value))}
                  disabled={!isEnabled}
                  className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>Auto</span>
                  <span>Meditation (60)</span>
                  <span>Upbeat (120)</span>
                </div>
              </div>
            </div>

            {/* Right: Info and action */}
            <div className="space-y-4">
              {/* Compact Processing Info */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h4 className="text-sm font-semibold text-blue-900 mb-3">How Focus Mode Works</h4>
                    <ul className="space-y-2 text-sm text-blue-800">
                      <li className="flex items-center">
                        <svg className="w-3 h-3 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                        </svg>
                        AI separates vocals from instruments
                      </li>
                      <li className="flex items-center">
                        <svg className="w-3 h-3 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                        </svg>
                        Reduces vocal prominence by up to 70%
                      </li>
                      <li className="flex items-center">
                        <svg className="w-3 h-3 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                        </svg>
                        Adjusts tempo for optimal concentration
                      </li>
                      <li className="flex items-center">
                        <svg className="w-3 h-3 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                        </svg>
                        Softens harsh frequencies
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Action button */}
              <div className="space-y-3">
                <button
                  onClick={handleFocusClick}
                  disabled={!isEnabled}
                  className={`w-full py-4 px-6 rounded-lg font-bold text-base transition-all duration-200 ${
                    isEnabled
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg hover:shadow-xl transform hover:scale-105'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  🎯 Create Focus Version
                </button>
                
                {currentSong && (
                  <p className="text-xs text-gray-500 text-center">
                    Estimated processing time: ~{Math.ceil((currentSong.duration || 180) / 60)} minutes
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FocusControls;

// Why this component design:
// 1. **Self-contained**: All focus controls in one place
// 2. **Preset system**: Makes it easier for users to choose good settings
// 3. **Visual feedback**: Real-time updates as users move sliders
// 4. **Disabled state**: Handles cases where focus mode isn't available
// 5. **Informational**: Explains what focus mode does
// 6. **Responsive**: Works on different screen sizes
// 7. **Callback pattern**: Parent component controls actual processing