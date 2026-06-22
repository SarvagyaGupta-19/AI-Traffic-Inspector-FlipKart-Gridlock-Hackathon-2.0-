/* eslint-disable @next/next/no-img-element */
'use client';

import { useState, useRef, useCallback } from 'react';
import {
  Upload, Video, Image as ImageIcon, Loader2, CheckCircle2,
  AlertTriangle, X, Play, BarChart3, Trash2, Film, Zap,
} from 'lucide-react';
import api from '@/lib/api';
import type { AnalysisResult } from '@/lib/types';
import { ViolationBadge, ConfidenceMeter } from '@/components/StatsCard';

const IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.bmp', '.webp'];
const VIDEO_EXTS = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
const ALL_ACCEPT = [...IMAGE_EXTS, ...VIDEO_EXTS].join(',');

interface VideoStats {
  total_frames: number;
  processed_frames: number;
  total_detections: number;
  total_violations: number;
  total_plates: number;
  elapsed_sec: number;
  fps: number;
  progress_pct: number;
}

interface FrameResult {
  type: string;
  frame_number?: number;
  progress?: number;
  detections?: Array<{ class_name: string; confidence: number }>;
  violations?: Array<{ type: string; confidence: number; description: string }>;
  plates?: Array<{ text: string; confidence: number }>;
  processing_time_ms?: number;
  annotated_frame?: string;
  stats?: VideoStats;
  // video_info fields
  width?: number;
  height?: number;
  fps?: number;
  total_frames?: number;
  duration_sec?: number;
  message?: string;
}

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<'image' | 'video' | null>(null);
  const [preview, setPreview] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);

  // Video processing state
  const [isProcessingVideo, setIsProcessingVideo] = useState(false);
  const [currentFrame, setCurrentFrame] = useState<string>('');
  const [videoStats, setVideoStats] = useState<VideoStats | null>(null);
  const [videoInfo, setVideoInfo] = useState<{ width: number; height: number; fps: number; total_frames: number; duration_sec: number } | null>(null);
  const [liveViolations, setLiveViolations] = useState<Array<{ type: string; confidence: number; description: string }>>([]);
  const [liveDetections, setLiveDetections] = useState<Array<{ class_name: string; confidence: number }>>([]);
  const [livePlates, setLivePlates] = useState<Array<{ text: string; confidence: number }>>([]);
  const [videoComplete, setVideoComplete] = useState(false);
  const [location, setLocation] = useState('MG Road Junction');
  const abortController = useRef<AbortController | null>(null);

  const handleFile = useCallback((f: File) => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    const isVideo = VIDEO_EXTS.includes(ext);
    const isImage = IMAGE_EXTS.includes(ext) || f.type.startsWith('image/');

    if (!isVideo && !isImage) {
      setError('Please upload an image or video file');
      return;
    }

    setFile(f);
    setFileType(isVideo ? 'video' : 'image');
    setResult(null);
    setError('');
    setVideoComplete(false);
    setLiveViolations([]);
    setLiveDetections([]);
    setLivePlates([]);
    setVideoStats(null);
    setVideoInfo(null);
    setCurrentFrame('');

    if (isImage) {
      setPreview(URL.createObjectURL(f));
    } else {
      // Create video thumbnail
      const video = document.createElement('video');
      video.preload = 'metadata';
      video.onloadeddata = () => {
        video.currentTime = 1; // seek to 1s for thumbnail
      };
      video.onseeked = () => {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx?.drawImage(video, 0, 0);
        setPreview(canvas.toDataURL('image/jpeg'));
        URL.revokeObjectURL(video.src);
      };
      video.src = URL.createObjectURL(f);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  // Image upload handler (existing)
  const handleImageUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(10);
    setError('');

    try {
      const progressInterval = setInterval(() => {
        setProgress(p => Math.min(p + 15, 85));
      }, 500);

      const response = await api.uploadImage(file);
      clearInterval(progressInterval);
      setProgress(100);

      if (response.success && response.result) {
        setResult(response.result);
      } else {
        setError(response.message || 'Processing failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  // Video upload with SSE streaming
  const handleVideoUpload = async () => {
    if (!file) return;
    setIsProcessingVideo(true);
    setError('');
    setLiveViolations([]);
    setLiveDetections([]);
    setLivePlates([]);
    setVideoComplete(false);

    abortController.current = new AbortController();

    try {
      const response = await api.uploadVideoStream(file, 10, location);
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response stream');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;

          try {
            const data: FrameResult = JSON.parse(line.slice(6));

            if (data.type === 'video_info') {
              setVideoInfo({
                width: data.width || 0,
                height: data.height || 0,
                fps: data.fps || 30,
                total_frames: data.total_frames || 0,
                duration_sec: data.duration_sec || 0,
              });
            } else if (data.type === 'frame_result') {
              // Update live frame
              if (data.annotated_frame) {
                setCurrentFrame(`data:image/jpeg;base64,${data.annotated_frame}`);
              }
              // Update stats
              if (data.stats) {
                setVideoStats(data.stats);
                setProgress(data.stats.progress_pct);
              }
              // Accumulate violations
              if (data.violations && data.violations.length > 0) {
                setLiveViolations(prev => [...prev, ...data.violations!]);
              }
              // Update latest detections
              if (data.detections && data.detections.length > 0) {
                setLiveDetections(data.detections);
              }
              // Accumulate plates
              if (data.plates && data.plates.length > 0) {
                setLivePlates(prev => {
                  const existing = new Set(prev.map(p => p.text));
                  const newPlates = data.plates!.filter(p => !existing.has(p.text));
                  return [...prev, ...newPlates];
                });
              }
            } else if (data.type === 'complete') {
              if (data.stats) setVideoStats(data.stats);
              setVideoComplete(true);
              setProgress(100);
            } else if (data.type === 'error') {
              setError(data.message || 'Video processing failed');
            }
          } catch {
            // Skip unparseable lines
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setError(err instanceof Error ? err.message : 'Video processing failed');
      }
    } finally {
      setIsProcessingVideo(false);
    }
  };

  const handleUpload = () => {
    if (fileType === 'video') {
      handleVideoUpload();
    } else {
      handleImageUpload();
    }
  };

  const handleStop = () => {
    abortController.current?.abort();
    setIsProcessingVideo(false);
    setVideoComplete(true);
  };

  const handleReset = async () => {
    try {
      await api.resetDatabase();
    } catch { /* ignore */ }
    reset();
  };

  const reset = () => {
    abortController.current?.abort();
    setFile(null);
    setFileType(null);
    setPreview('');
    setResult(null);
    setError('');
    setProgress(0);
    setIsProcessingVideo(false);
    setCurrentFrame('');
    setVideoStats(null);
    setVideoInfo(null);
    setLiveViolations([]);
    setLiveDetections([]);
    setLivePlates([]);
    setVideoComplete(false);
  };

  const isProcessing = uploading || isProcessingVideo;
  const hasVideoResults = videoStats && (videoStats.total_detections > 0 || videoComplete);

  return (
    <div className="p-8  min-h-screen">
      <div className="mb-8 animate-slide-up">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">
              <span className="text-[var(--accent-blue)]">Upload & Analyze</span>
            </h1>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Upload a traffic image or video — AI detects violations in real-time
            </p>
          </div>
          <button
            className="btn-secondary flex items-center gap-2 text-xs"
            onClick={handleReset}
            title="Reset database for a fresh demo"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Fresh Start
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Upload / Live Feed */}
        <div className="animate-slide-up" style={{ animationDelay: '0.1s' }}>
          {!preview && !currentFrame ? (
            <div
              className={`drop-zone p-12 text-center cursor-pointer h-[480px] flex flex-col items-center justify-center ${isDragging ? 'active' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInput.current?.click()}
            >
              <div className="w-20 h-20 rounded-2xl bg-[rgba(79,124,255,0.1)] flex items-center justify-center mb-6">
                <Upload className={`w-8 h-8 ${isDragging ? 'text-[var(--accent-blue)]' : 'text-[var(--text-secondary)]'}`} />
              </div>
              <p className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                {isDragging ? 'Drop file here' : 'Drag & drop traffic footage'}
              </p>
              <p className="text-sm text-[var(--text-secondary)] mb-2">
                Image or Video — AI processes every frame
              </p>
              <p className="text-xs text-[var(--text-secondary)] mb-6">
                Supports: MP4, AVI, MOV, JPEG, PNG
              </p>
              <div className="flex gap-3">
                <button className="btn-primary flex items-center gap-2" type="button">
                  <Video className="w-4 h-4" /> Select Video
                </button>
                <button className="btn-secondary flex items-center gap-2" type="button">
                  <ImageIcon className="w-4 h-4" /> Select Image
                </button>
              </div>
              <input
                ref={fileInput}
                type="file"
                accept={ALL_ACCEPT}
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
            </div>
          ) : (
            <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] overflow-hidden">
              {/* Live Frame Display (video processing) */}
              {currentFrame ? (
                <div className="relative aspect-video bg-black flex items-center justify-center">
                  <img
                    src={currentFrame}
                    alt="AI detection frame"
                    className="max-w-full max-h-full object-contain"
                  />
                  {/* Live badge */}
                  {isProcessingVideo && (
                    <div className="absolute top-3 left-3 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-600/90 text-white text-xs font-bold">
                      <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                      AI PROCESSING
                    </div>
                  )}
                  {videoComplete && (
                    <div className="absolute top-3 left-3 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-600/90 text-white text-xs font-bold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      COMPLETE
                    </div>
                  )}
                  {/* Frame counter */}
                  {videoStats && (
                    <div className="absolute bottom-3 left-3 px-2 py-1 rounded bg-black/70 text-white text-[10px] font-mono">
                      Frame {videoStats.processed_frames}/{videoStats.total_frames} | {videoStats.fps} FPS
                    </div>
                  )}
                  <button
                    onClick={reset}
                    className="absolute top-3 right-3 w-8 h-8 rounded-lg bg-black/60 flex items-center justify-center hover:bg-black/80 transition-colors"
                  >
                    <X className="w-4 h-4 text-white" />
                  </button>
                </div>
              ) : (
                /* Image Preview or Video Thumbnail */
                <div className="relative aspect-video bg-black flex items-center justify-center">
                  <img
                    src={preview}
                    alt="Upload preview"
                    className="max-w-full max-h-full object-contain"
                  />
                  {fileType === 'video' && !isProcessing && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-16 h-16 rounded-full bg-black/60 flex items-center justify-center">
                        <Play className="w-8 h-8 text-white ml-1" />
                      </div>
                    </div>
                  )}
                  <button
                    onClick={reset}
                    className="absolute top-3 right-3 w-8 h-8 rounded-lg bg-black/60 flex items-center justify-center hover:bg-black/80 transition-colors"
                  >
                    <X className="w-4 h-4 text-white" />
                  </button>
                </div>
              )}

              {/* File info & actions */}
              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {fileType === 'video' ? (
                      <Film className="w-5 h-5 text-[var(--accent-purple)]" />
                    ) : (
                      <ImageIcon className="w-5 h-5 text-[var(--accent-blue)]" />
                    )}
                    <div>
                      <p className="text-sm font-medium">{file?.name}</p>
                      <p className="text-xs text-[var(--text-secondary)]">
                        {file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : ''}
                        {videoInfo ? ` | ${videoInfo.duration_sec}s | ${videoInfo.width}x${videoInfo.height}` : ''}
                      </p>
                    </div>
                  </div>
                    {fileType === 'video' && (
                    <span className="badge badge-purple text-[10px]">VIDEO</span>
                  )}
                </div>

                <div className="mb-4">
                  <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
                    Camera Location
                  </label>
                  <select
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--accent-blue)]"
                    disabled={isProcessing}
                  >
                    <option value="MG Road Junction">MG Road Junction</option>
                    <option value="Silk Board Signal">Silk Board Signal</option>
                    <option value="Indiranagar 100ft Road">Indiranagar 100ft Road</option>
                    <option value="Koramangala 80ft Road">Koramangala 80ft Road</option>
                    <option value="Hebbal Flyover">Hebbal Flyover</option>
                    <option value="Unknown">Other / Unknown</option>
                  </select>
                </div>

                {/* Progress bar */}
                {isProcessing && (
                  <div className="mb-4">
                    <div className="progress-bar h-[6px]">
                      <div
                        className="progress-bar-fill"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] mt-2 flex items-center gap-2">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      {fileType === 'video'
                        ? `Processing frames... ${progress.toFixed(0)}%`
                        : 'Running detection pipeline...'
                      }
                    </p>
                  </div>
                )}

                {error && (
                  <div className="mb-4 p-3 rounded-lg bg-[rgba(255,71,87,0.1)] border border-[rgba(255,71,87,0.3)] text-sm text-[var(--accent-red)]">
                    {error}
                  </div>
                )}

                <div className="flex gap-3">
                  {isProcessingVideo ? (
                    <button
                      className="btn-secondary flex-1 flex items-center justify-center gap-2 text-[var(--accent-red)]"
                      onClick={handleStop}
                    >
                      <X className="w-4 h-4" />
                      Stop Processing
                    </button>
                  ) : (
                    <button
                      className="btn-primary flex-1 flex items-center justify-center gap-2"
                      onClick={handleUpload}
                      disabled={isProcessing || (videoComplete && fileType === 'video')}
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Analyzing...
                        </>
                      ) : videoComplete ? (
                        <>
                          <CheckCircle2 className="w-4 h-4" />
                          Done — View Dashboard
                        </>
                      ) : result ? (
                        <>
                          <CheckCircle2 className="w-4 h-4" />
                          Re-analyze
                        </>
                      ) : fileType === 'video' ? (
                        <>
                          <Zap className="w-4 h-4" />
                          Start AI Detection
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4" />
                          Detect Violations
                        </>
                      )}
                    </button>
                  )}
                  <button className="btn-secondary" onClick={reset}>
                    Clear
                  </button>
                </div>

                {videoComplete && (
                  <a
                    href="/analytics"
                    className="mt-3 btn-primary w-full flex items-center justify-center gap-2 text-center"
                  >
                    <BarChart3 className="w-4 h-4" />
                    View Analytics Dashboard
                  </a>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Results Panel */}
        <div className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
          {/* Video Processing Results */}
          {(hasVideoResults || isProcessingVideo) ? (
            <div className="space-y-4">
              {/* Live Stats */}
              {videoStats && (
                <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5">
                  <div className="flex items-center gap-3 mb-4">
                    <Zap className="w-5 h-5 text-[var(--accent-yellow)]" />
                    <h3 className="font-semibold">
                      {videoComplete ? 'Detection Complete' : 'Live Detection'}
                    </h3>
                    <span className="text-xs text-[var(--text-secondary)] ml-auto">
                      {videoStats.elapsed_sec}s elapsed
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    <div className="text-center p-3 rounded-xl bg-[var(--bg-primary)]">
                      <p className="text-2xl font-bold text-[var(--accent-blue)]">
                        {videoStats.total_detections}
                      </p>
                      <p className="text-[10px] text-[var(--text-secondary)] mt-1">Objects</p>
                    </div>
                    <div className="text-center p-3 rounded-xl bg-[var(--bg-primary)]">
                      <p className="text-2xl font-bold text-[var(--accent-red)]">
                        {videoStats.total_violations}
                      </p>
                      <p className="text-[10px] text-[var(--text-secondary)] mt-1">Violations</p>
                    </div>
                    <div className="text-center p-3 rounded-xl bg-[var(--bg-primary)]">
                      <p className="text-2xl font-bold text-[var(--accent-cyan)]">
                        {livePlates.length}
                      </p>
                      <p className="text-[10px] text-[var(--text-secondary)] mt-1">Plates</p>
                    </div>
                    <div className="text-center p-3 rounded-xl bg-[var(--bg-primary)]">
                      <p className="text-2xl font-bold text-[var(--accent-green)]">
                        {videoStats.fps}
                      </p>
                      <p className="text-[10px] text-[var(--text-secondary)] mt-1">FPS</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Live Violations */}
              {liveViolations.length > 0 && (
                <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5 max-h-[280px] overflow-y-auto">
                  <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-[var(--accent-red)]" />
                    Violations Found ({liveViolations.length})
                  </h3>
                  <div className="space-y-2">
                    {liveViolations.slice(-15).reverse().map((v, i) => (
                      <div key={i} className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[rgba(255,71,87,0.12)]">
                        <div className="flex items-center justify-between mb-1">
                          <ViolationBadge type={v.type} size="sm" />
                          <ConfidenceMeter value={v.confidence} size="sm" />
                        </div>
                        <p className="text-[10px] text-[var(--text-secondary)] line-clamp-1">{v.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Live Plates */}
              {livePlates.length > 0 && (
                <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5">
                  <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">
                    License Plates
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {livePlates.map((p, i) => (
                      <span key={i} className="badge badge-blue font-mono font-bold text-xs px-3 py-1.5">
                        {p.text} ({(p.confidence * 100).toFixed(0)}%)
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Current Frame Detections */}
              {liveDetections.length > 0 && (
                <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5">
                  <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">
                    Current Frame Objects
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {liveDetections.map((d, i) => (
                      <span key={i} className="badge badge-blue text-[10px]">
                        {d.class_name} ({(d.confidence * 100).toFixed(0)}%)
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : result ? (
            /* Image Analysis Results */
            <div className="space-y-4">
              <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5">
                <div className="flex items-center gap-3 mb-4">
                  <CheckCircle2 className="w-5 h-5 text-[var(--accent-green)]" />
                  <h3 className="font-semibold">Analysis Complete</h3>
                  <span className="text-xs text-[var(--text-secondary)] ml-auto">
                    {result.processing_time_ms.toFixed(0)}ms
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-3 rounded-xl bg-[var(--bg-primary)]">
                    <p className="text-2xl font-bold text-[var(--accent-blue)]">
                      {result.detections.length}
                    </p>
                    <p className="text-[10px] text-[var(--text-secondary)] mt-1">Objects</p>
                  </div>
                  <div className="text-center p-3 rounded-xl bg-[var(--bg-primary)]">
                    <p className="text-2xl font-bold text-[var(--accent-red)]">
                      {result.violations.length}
                    </p>
                    <p className="text-[10px] text-[var(--text-secondary)] mt-1">Violations</p>
                  </div>
                  <div className="text-center p-3 rounded-xl bg-[var(--bg-primary)]">
                    <p className="text-2xl font-bold text-[var(--accent-cyan)]">
                      {result.plates.length}
                    </p>
                    <p className="text-[10px] text-[var(--text-secondary)] mt-1">Plates</p>
                  </div>
                </div>
              </div>

              {result.violations.length > 0 && (
                <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5">
                  <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
                    <AlertTriangle className="w-4 h-4 inline mr-2 text-[var(--accent-red)]" />
                    Violations Found
                  </h3>
                  <div className="space-y-3">
                    {result.violations.map((v, i) => (
                      <div key={i} className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[rgba(255,71,87,0.15)]">
                        <div className="flex items-center justify-between mb-2">
                          <ViolationBadge type={v.type} size="md" />
                          <ConfidenceMeter value={v.confidence} />
                        </div>
                        <p className="text-xs text-[var(--text-secondary)]">{v.description}</p>
                        {v.plate && (
                          <div className="mt-2 flex items-center gap-2">
                            <span className="badge badge-blue text-[10px]">
                              {v.plate.text}
                            </span>
                            <span className="text-[10px] text-[var(--text-secondary)]">
                              ({(v.plate.confidence * 100).toFixed(0)}% confidence)
                            </span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5">
                <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
                  Detected Objects
                </h3>
                <div className="flex flex-wrap gap-2">
                  {result.detections.map((d, i) => (
                    <span key={i} className="badge badge-blue">
                      {d.class_name} ({(d.confidence * 100).toFixed(0)}%)
                    </span>
                  ))}
                </div>
              </div>

              {result.plates.length > 0 && (
                <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5">
                  <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
                    License Plates
                  </h3>
                  <div className="space-y-2">
                    {result.plates.map((p, i) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-primary)]">
                        <span className="font-mono font-bold text-[var(--accent-cyan)]">{p.text}</span>
                        <ConfidenceMeter value={p.confidence} size="sm" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Empty State */
            <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-12 text-center h-[480px] flex flex-col items-center justify-center">
              <div className="w-20 h-20 rounded-2xl bg-[rgba(79,124,255,0.08)] flex items-center justify-center mb-6">
                <Video className="w-10 h-10 text-[var(--border-color)]" />
              </div>
              <p className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                Real-Time AI Detection
              </p>
              <p className="text-sm text-[var(--text-secondary)] mb-4 max-w-xs">
                Upload a traffic video and watch AI detect violations frame-by-frame in real-time
              </p>
              <div className="grid grid-cols-2 gap-3 text-left max-w-xs">
                <div className="flex items-start gap-2">
                  <Zap className="w-4 h-4 text-[var(--accent-yellow)] mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-[var(--text-secondary)]">YOLOv8s Object Detection</p>
                </div>
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-[var(--accent-red)] mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-[var(--text-secondary)]">7 Violation Types</p>
                </div>
                <div className="flex items-start gap-2">
                  <Film className="w-4 h-4 text-[var(--accent-purple)] mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-[var(--text-secondary)]">Frame-by-Frame Analysis</p>
                </div>
                <div className="flex items-start gap-2">
                  <BarChart3 className="w-4 h-4 text-[var(--accent-green)] mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-[var(--text-secondary)]">Live Dashboard</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
