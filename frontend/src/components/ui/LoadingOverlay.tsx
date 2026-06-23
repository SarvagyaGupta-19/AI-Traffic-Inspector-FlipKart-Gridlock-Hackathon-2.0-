'use client';

import React from 'react';

interface LoadingOverlayProps {
  isVisible: boolean;
  text?: string;
}

export default function LoadingOverlay({ isVisible, text = 'INITIALIZING SYSTEM...' }: LoadingOverlayProps) {
  return (
    <div
      className={`fixed inset-0 z-[100] flex flex-col items-center justify-center bg-[#07707b] transition-opacity duration-500 ${
        isVisible ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
      }`}
      style={{ fontFamily: 'Impact, "Arial Black", sans-serif' }}
    >
      {/* Heavy Grain/Noise Texture matching landing page */}
      <div 
        className="absolute inset-0 opacity-20 pointer-events-none mix-blend-overlay z-0" 
        style={{ 
          backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 400 400%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' 
        }} 
      />
      
      {/* Container with gentle float animation */}
      <div className="relative z-10 flex flex-col items-center animate-[float_4s_ease-in-out_infinite]">
        
        {/* SVG Graphic */}
        <svg viewBox="0 0 400 400" className="w-64 h-64 md:w-80 md:h-80 drop-shadow-[0_20px_30px_rgba(0,0,0,0.3)]">
          <defs>
            <style>
              {`
                @keyframes dash {
                  to { stroke-dashoffset: -40; }
                }
                .road-dash {
                  stroke-dasharray: 20 20;
                  animation: dash 1s linear infinite;
                }
                @keyframes blinkRed {
                  0%, 33% { fill: #ff3b30; filter: drop-shadow(0 0 10px #ff3b30); }
                  34%, 100% { fill: #333; filter: none; }
                }
                @keyframes blinkYellow {
                  0%, 33% { fill: #333; filter: none; }
                  33%, 66% { fill: #ffcc00; filter: drop-shadow(0 0 10px #ffcc00); }
                  67%, 100% { fill: #333; filter: none; }
                }
                @keyframes blinkGreen {
                  0%, 66% { fill: #333; filter: none; }
                  66%, 100% { fill: #34c759; filter: drop-shadow(0 0 10px #34c759); }
                }
                .light-red { animation: blinkRed 3s infinite; }
                .light-yellow { animation: blinkYellow 3s infinite; }
                .light-green { animation: blinkGreen 3s infinite; }
                
                @keyframes float {
                  0%, 100% { transform: translateY(0); }
                  50% { transform: translateY(-10px); }
                }
                @keyframes spin-slow {
                  from { transform: rotate(0deg); }
                  to { transform: rotate(360deg); }
                }
                .spin-wheel {
                  transform-origin: 120px 260px;
                  animation: spin-slow 3s linear infinite;
                }
              `}
            </style>
            <filter id="drop-shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="4" dy="4" stdDeviation="4" floodColor="#000" floodOpacity="0.3"/>
            </filter>
          </defs>

          {/* BACKGROUND SPARKLES */}
          <circle cx="240" cy="90" r="5" fill="#f8c850" stroke="#000" strokeWidth="2" />
          <circle cx="80" cy="180" r="4" fill="#2f58cd" stroke="#000" strokeWidth="2" />
          <circle cx="330" cy="270" r="4" fill="#e23f44" stroke="#000" strokeWidth="2" />

          {/* RIGHT POLE (Traffic Light) */}
          <rect x="275" y="100" width="10" height="180" fill="#2f58cd" stroke="#000" strokeWidth="4" />

          {/* ROAD (Diagonal) */}
          <g filter="url(#drop-shadow)">
            <polygon points="125,120 185,120 270,280 210,280" fill="#a0aab2" stroke="#000" strokeWidth="4" strokeLinejoin="round" />
            <line x1="155" y1="120" x2="240" y2="280" stroke="#f8c850" strokeWidth="6" className="road-dash" />
          </g>

          {/* LEFT POLE (Stop Sign) */}
          <rect x="115" y="90" width="10" height="170" fill="#fff" stroke="#000" strokeWidth="4" />

          {/* TRAFFIC LIGHT BOX */}
          <g filter="url(#drop-shadow)">
            <rect x="260" y="80" width="40" height="110" rx="10" fill="#d5dbe1" stroke="#000" strokeWidth="4" />
            
            {/* Lights */}
            <circle cx="280" cy="105" r="10" className="light-red" stroke="#000" strokeWidth="2" />
            <circle cx="280" cy="135" r="10" className="light-yellow" stroke="#000" strokeWidth="2" />
            <circle cx="280" cy="165" r="10" className="light-green" stroke="#000" strokeWidth="2" />
            
            {/* Hoods */}
            <path d="M 267 100 Q 280 90 293 100" fill="none" stroke="#222" strokeWidth="3" strokeLinecap="round" />
            <path d="M 267 130 Q 280 120 293 130" fill="none" stroke="#222" strokeWidth="3" strokeLinecap="round" />
            <path d="M 267 160 Q 280 150 293 160" fill="none" stroke="#222" strokeWidth="3" strokeLinecap="round" />
          </g>

          {/* STOP SIGN */}
          <g transform="translate(80, 50)" filter="url(#drop-shadow)">
            {/* 80x80 Octagon */}
            <polygon points="24,0 56,0 80,24 80,56 56,80 24,80 0,56 0,24" fill="#e23f44" stroke="#000" strokeWidth="4" />
            <polygon points="26,5 54,5 75,26 75,54 54,75 26,75 5,54 5,26" fill="none" stroke="#fff" strokeWidth="3" />
            <rect x="20" y="34" width="40" height="12" fill="#fff" rx="2" />
          </g>

          {/* WHEEL */}
          <g className="spin-wheel" filter="url(#drop-shadow)">
            {/* Tire */}
            <circle cx="120" cy="260" r="50" fill="#2a2a2a" stroke="#000" strokeWidth="4" />
            {/* Hubcap */}
            <circle cx="120" cy="260" r="30" fill="#e4e8ec" stroke="#000" strokeWidth="4" />
            <circle cx="120" cy="260" r="8" fill="#a0aab2" stroke="#000" strokeWidth="3" />
            {/* Spokes */}
            <line x1="120" y1="230" x2="120" y2="252" stroke="#000" strokeWidth="4" />
            <line x1="120" y1="268" x2="120" y2="290" stroke="#000" strokeWidth="4" />
            <line x1="90" y1="260" x2="112" y2="260" stroke="#000" strokeWidth="4" />
            <line x1="128" y1="260" x2="150" y2="260" stroke="#000" strokeWidth="4" />
            {/* Spin indicators */}
            <circle cx="95" cy="235" r="3" fill="#555" />
            <circle cx="145" cy="285" r="3" fill="#555" />
          </g>

          {/* Base line */}
          <line x1="60" y1="300" x2="340" y2="300" stroke="#000" strokeWidth="3" strokeLinecap="round" />
        </svg>

        {/* Text */}
        <div className="mt-8 text-[#f0f0f0] text-center z-10">
          <h2 className="text-xl md:text-2xl font-black uppercase tracking-[0.2em] mb-2" style={{ textShadow: '0 4px 10px rgba(0,0,0,0.5)' }}>
            {text}
          </h2>
          <div className="flex gap-2 justify-center mt-4">
            <div className="w-3 h-3 bg-[#ff3b30] rounded-full animate-bounce shadow-[0_0_10px_#ff3b30]" style={{ animationDelay: '0ms' }} />
            <div className="w-3 h-3 bg-[#ffcc00] rounded-full animate-bounce shadow-[0_0_10px_#ffcc00]" style={{ animationDelay: '150ms' }} />
            <div className="w-3 h-3 bg-[#34c759] rounded-full animate-bounce shadow-[0_0_10px_#34c759]" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    </div>
  );
}
