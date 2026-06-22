/* eslint-disable @next/next/no-img-element */
'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Video, Play, Pause, Square, Wifi, WifiOff, Camera, Zap } from 'lucide-react';
import api from '@/lib/api';
import { ViolationBadge, ConfidenceMeter } from '@/components/StatsCard';
import type { Detection, Violation } from '@/lib/types';

export default function LiveStreamPage() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [connected, setConnected] = useState(false);
  const [frameCount, setFrameCount] = useState(0);
  const [fps, setFps] = useState(0);
  const [lastProcessingTime, setLastProcessingTime] = useState(0);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [annotatedFrame, setAnnotatedFrame] = useState<string>('');
  const [source, setSource] = useState<'webcam' | 'file'>('webcam');

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameTimerRef = useRef<number>(0);
  const fpsCounterRef = useRef<{ frames: number; lastTime: number }>({ frames: 0, lastTime: 0 });
  
  useEffect(() => {
    fpsCounterRef.current.lastTime = Date.now();
  }, []);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const connectWebSocket = useCallback(() => {
    const wsUrl = api.getWebSocketUrl();
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'result') {
          setDetections(data.detections || []);
          setViolations(data.violations || []);
          setLastProcessingTime(data.processing_time_ms || 0);
          if (data.annotated_frame) {
            setAnnotatedFrame(data.annotated_frame);
          }

          // FPS counter
          fpsCounterRef.current.frames++;
          const now = Date.now();
          if (now - fpsCounterRef.current.lastTime >= 1000) {
            setFps(fpsCounterRef.current.frames);
            fpsCounterRef.current.frames = 0;
            fpsCounterRef.current.lastTime = now;
          }
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('WebSocket disconnected');
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setConnected(false);
    };

    wsRef.current = ws;
  }, []);

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      return true;
    } catch (err) {
      console.error('Failed to access webcam:', err);
      alert('Could not access webcam. Please ensure camera permissions are granted.');
      return false;
    }
  };

  const sendFrame = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    if (!videoRef.current || !canvasRef.current) return;
    if (isPaused) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = 640;
    canvas.height = 480;
    ctx.drawImage(video, 0, 0, 640, 480);

    // Convert to base64
    const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
    const base64 = dataUrl.split(',')[1];

    setFrameCount(prev => prev + 1);

    wsRef.current.send(JSON.stringify({
      type: 'frame',
      data: base64,
      frame_number: frameCount,
    }));
  }, [isPaused, frameCount]);

  const startStream = async () => {
    if (source === 'webcam') {
      const success = await startWebcam();
      if (!success) return;
    }

    connectWebSocket();
    setIsStreaming(true);

    // Start sending frames every 200ms (5 FPS to server)
    frameTimerRef.current = window.setInterval(sendFrame, 200);
  };

  const stopStream = () => {
    if (frameTimerRef.current) {
      clearInterval(frameTimerRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
    }
    setIsStreaming(false);
    setConnected(false);
    setDetections([]);
    setViolations([]);
    setAnnotatedFrame('');
    setFrameCount(0);
    setFps(0);
  };

  const togglePause = () => {
    setIsPaused(!isPaused);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'control',
        action: isPaused ? 'resume' : 'pause',
      }));
    }
  };

  useEffect(() => {
    return () => {
      stopStream();
    };
  }, []);

  // Update frame sending interval when sendFrame changes
  useEffect(() => {
    if (isStreaming && frameTimerRef.current) {
      clearInterval(frameTimerRef.current);
      frameTimerRef.current = window.setInterval(sendFrame, 200);
    }
  }, [sendFrame, isStreaming]);

  return (
    <div className="p-8  min-h-screen">
      <div className="mb-8 animate-slide-up">
        <h1 className="text-2xl font-bold">
          <span className="text-[var(--accent-blue)]">Live Detection</span>
        </h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Real-time traffic violation detection via webcam or video feed
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Video Feed */}
        <div className="lg:col-span-2 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] overflow-hidden">
            {/* Status bar */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--border-color)]">
              <div className="flex items-center gap-3">
                {connected ? (
                  <span className="flex items-center gap-2 text-xs text-[var(--accent-green)]">
                    <Wifi className="w-3 h-3" /> Connected
                  </span>
                ) : (
                  <span className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                    <WifiOff className="w-3 h-3" /> Disconnected
                  </span>
                )}
                {isStreaming && (
                  <>
                    <span className="text-xs text-[var(--text-secondary)]">|</span>
                    <span className="flex items-center gap-1 text-xs text-[var(--accent-red)]">
                      <div className="w-2 h-2 rounded-full bg-[var(--accent-red)] animate-pulse-glow" />
                      LIVE
                    </span>
                    <span className="text-xs text-[var(--text-secondary)]">
                      {fps} FPS • {lastProcessingTime.toFixed(0)}ms • Frame #{frameCount}
                    </span>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value as 'webcam' | 'file')}
                  disabled={isStreaming}
                  className="text-xs px-3 py-1.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-color)] text-[var(--text-primary)]"
                >
                  <option value="webcam">Webcam</option>
                  <option value="file">Video File</option>
                </select>
              </div>
            </div>

            {/* Video / Annotated Feed */}
            <div className="relative aspect-video bg-black flex items-center justify-center">
              {annotatedFrame && isStreaming ? (
                <img
                  src={`data:image/jpeg;base64,${annotatedFrame}`}
                  alt="Annotated frame"
                  className="w-full h-full object-contain"
                />
              ) : (
                <>
                  <video
                    ref={videoRef}
                    className={`w-full h-full object-contain ${isStreaming ? '' : 'hidden'}`}
                    autoPlay
                    muted
                    playsInline
                  />
                  {!isStreaming && (
                    <div className="flex flex-col items-center gap-4">
                      <div className="w-20 h-20 rounded-2xl bg-[rgba(79,124,255,0.08)] flex items-center justify-center">
                        <Video className="w-8 h-8 text-[var(--border-color)]" />
                      </div>
                      <p className="text-sm text-[var(--text-secondary)]">
                        Click Start to begin live detection
                      </p>
                    </div>
                  )}
                </>
              )}
              <canvas ref={canvasRef} className="hidden" />
            </div>

            {/* Controls */}
            <div className="flex items-center justify-center gap-3 p-4 border-t border-[var(--border-color)]">
              {!isStreaming ? (
                <button className="btn-primary flex items-center gap-2" onClick={startStream}>
                  <Play className="w-4 h-4" /> Start Stream
                </button>
              ) : (
                <>
                  <button
                    className="btn-secondary flex items-center gap-2"
                    onClick={togglePause}
                  >
                    {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                    {isPaused ? 'Resume' : 'Pause'}
                  </button>
                  <button
                    className="btn-secondary flex items-center gap-2 border-[rgba(255,71,87,0.3)] hover:border-[var(--accent-red)] hover:text-[var(--accent-red)]"
                    onClick={stopStream}
                  >
                    <Square className="w-4 h-4" /> Stop
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Live Detection Feed */}
        <div className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5 mb-4">
            <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4 text-[var(--accent-orange)]" />
              Live Detections
            </h3>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="text-center p-3 rounded-xl bg-[var(--bg-primary)]">
                <p className="text-2xl font-bold text-[var(--accent-blue)]">{detections.length}</p>
                <p className="text-[10px] text-[var(--text-secondary)]">Objects</p>
              </div>
              <div className="text-center p-3 rounded-xl bg-[var(--bg-primary)]">
                <p className="text-2xl font-bold text-[var(--accent-red)]">{violations.length}</p>
                <p className="text-[10px] text-[var(--text-secondary)]">Violations</p>
              </div>
            </div>

            {/* Detected Objects */}
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {detections.slice(0, 10).map((d, i) => (
                <div key={i} className="flex items-center justify-between py-1.5 px-2 rounded-lg text-xs">
                  <span className="text-[var(--text-secondary)]">
                    {d.class_name}
                    {d.track_id !== undefined && (
                      <span className="text-[var(--accent-blue)] ml-1">#{d.track_id}</span>
                    )}
                  </span>
                  <span className="font-mono text-[var(--accent-green)]">
                    {(d.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
              {detections.length === 0 && (
                <p className="text-xs text-[var(--text-secondary)] text-center py-4">
                  {isStreaming ? 'Waiting for detections...' : 'Start streaming to detect objects'}
                </p>
              )}
            </div>
          </div>

          {/* Active Violations */}
          <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5">
            <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4 flex items-center gap-2">
              <Camera className="w-4 h-4 text-[var(--accent-red)]" />
              Active Violations
            </h3>
            <div className="space-y-3">
              {violations.map((v, i) => (
                <div key={i} className="p-3 rounded-xl bg-[rgba(255,71,87,0.05)] border border-[rgba(255,71,87,0.15)]">
                  <div className="flex items-center justify-between mb-2">
                    <ViolationBadge type={v.type} size="sm" />
                    <ConfidenceMeter value={v.confidence} size="sm" />
                  </div>
                  <p className="text-[10px] text-[var(--text-secondary)] truncate">
                    {v.description}
                  </p>
                </div>
              ))}
              {violations.length === 0 && (
                <p className="text-xs text-[var(--text-secondary)] text-center py-4">
                  {isStreaming ? 'No violations detected' : 'Start streaming to monitor'}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="video/*"
        className="hidden"
      />
    </div>
  );
}
