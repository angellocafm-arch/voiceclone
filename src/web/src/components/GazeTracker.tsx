"use client";

import { useState, useEffect, useRef, useCallback } from "react";

/**
 * GazeTracker — Eye tracking cursor and dwell activation
 *
 * Connects to eye tracking hardware (Tobii, etc.) via WebSocket.
 * Shows a visual gaze cursor on screen.
 * Handles dwell time activation: when gaze stays on an interactive element
 * for the configured dwell time, it triggers a click.
 *
 * Protocol (via WebSocket ws://localhost:8765/ws/gaze):
 *   Server → Client: { x: number, y: number, fixation: boolean, timestamp: number }
 *   Client → Server: { type: "config", dwellTime: number, smoothing: number }
 *
 * Fallback: If no eye tracker connected, cursor follows mouse with
 * simulated dwell (for development/testing).
 */

interface GazePoint {
  x: number;
  y: number;
  fixation: boolean;
  timestamp: number;
}

interface GazeTrackerProps {
  /** Whether gaze tracking is active */
  active: boolean;
  /** Dwell time in ms to trigger click (default 800) */
  dwellTimeMs?: number;
  /** Smoothing factor 0-1 (higher = smoother but more latent) */
  smoothing?: number;
  /** Cursor size in pixels */
  cursorSize?: number;
  /** Whether to show dwell progress ring */
  showProgress?: boolean;
  /** Callback when dwell activates on an element */
  onDwellActivate?: (element: HTMLElement) => void;
}

export default function GazeTracker({
  active,
  dwellTimeMs = 800,
  smoothing = 0.3,
  cursorSize = 40,
  showProgress = true,
  onDwellActivate,
}: GazeTrackerProps) {
  const [gazePos, setGazePos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isConnected, setIsConnected] = useState(false);
  const [dwellProgress, setDwellProgress] = useState(0);
  const [dwellTarget, setDwellTarget] = useState<HTMLElement | null>(null);

  const smoothedPos = useRef({ x: 0, y: 0 });
  const wsRef = useRef<WebSocket | null>(null);
  const dwellTimerRef = useRef<NodeJS.Timeout | null>(null);
  const dwellStartRef = useRef<number | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // Smooth the gaze position using exponential moving average
  const updatePosition = useCallback(
    (rawX: number, rawY: number) => {
      const prev = smoothedPos.current;
      const newX = prev.x + (rawX - prev.x) * (1 - smoothing);
      const newY = prev.y + (rawY - prev.y) * (1 - smoothing);
      smoothedPos.current = { x: newX, y: newY };
      setGazePos({ x: newX, y: newY });
    },
    [smoothing]
  );

  // Check what interactive element is under the gaze point
  const getInteractiveElement = useCallback((x: number, y: number): HTMLElement | null => {
    const element = document.elementFromPoint(x, y);
    if (!element) return null;

    // Walk up to find the nearest interactive element
    let current: HTMLElement | null = element as HTMLElement;
    while (current) {
      const tag = current.tagName.toLowerCase();
      const role = current.getAttribute("role");
      const tabIndex = current.getAttribute("tabindex");

      if (
        tag === "button" ||
        tag === "a" ||
        tag === "input" ||
        tag === "textarea" ||
        tag === "select" ||
        role === "button" ||
        role === "link" ||
        role === "tab" ||
        role === "menuitem" ||
        (tabIndex !== null && tabIndex !== "-1")
      ) {
        return current;
      }
      current = current.parentElement;
    }
    return null;
  }, []);

  // Handle dwell activation
  const handleDwell = useCallback(
    (x: number, y: number) => {
      const element = getInteractiveElement(x, y);

      if (element !== dwellTarget) {
        // Gaze moved to a different element — reset
        if (dwellTimerRef.current) {
          clearInterval(dwellTimerRef.current);
          dwellTimerRef.current = null;
        }
        setDwellProgress(0);
        setDwellTarget(element);
        dwellStartRef.current = null;

        if (element) {
          // Start new dwell timer
          dwellStartRef.current = Date.now();
          element.classList.add("gaze-hover");

          dwellTimerRef.current = setInterval(() => {
            if (!dwellStartRef.current) return;
            const elapsed = Date.now() - dwellStartRef.current;
            const progress = Math.min(elapsed / dwellTimeMs, 1);
            setDwellProgress(progress);

            if (progress >= 1) {
              if (dwellTimerRef.current) clearInterval(dwellTimerRef.current);
              // Trigger click
              element.click();
              element.classList.remove("gaze-hover");
              element.classList.add("gaze-activated");
              setTimeout(() => element.classList.remove("gaze-activated"), 300);

              onDwellActivate?.(element);

              setDwellProgress(0);
              setDwellTarget(null);
              dwellStartRef.current = null;
            }
          }, 50);
        }
      }
    },
    [dwellTarget, dwellTimeMs, getInteractiveElement, onDwellActivate]
  );

  // Connect to eye tracker WebSocket
  useEffect(() => {
    if (!active) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setIsConnected(false);
      return;
    }

    const ws = new WebSocket("ws://localhost:8765/ws/gaze");
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      // Send config
      ws.send(
        JSON.stringify({
          type: "config",
          dwellTime: dwellTimeMs,
          smoothing,
        })
      );
    };

    ws.onmessage = (event) => {
      const data: GazePoint = JSON.parse(event.data);
      updatePosition(data.x, data.y);
      if (data.fixation) {
        handleDwell(data.x, data.y);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = () => {
      setIsConnected(false);
      // Fallback to mouse tracking for development
      console.info(
        "[GazeTracker] Eye tracker not available, using mouse fallback"
      );
    };

    return () => {
      ws.close();
    };
  }, [active, dwellTimeMs, smoothing, updatePosition, handleDwell]);

  // Mouse fallback when eye tracker is not connected
  useEffect(() => {
    if (!active || isConnected) return;

    const handleMouseMove = (e: MouseEvent) => {
      updatePosition(e.clientX, e.clientY);
      handleDwell(e.clientX, e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [active, isConnected, updatePosition, handleDwell]);

  // Cleanup dwell timers
  useEffect(() => {
    return () => {
      if (dwellTimerRef.current) clearInterval(dwellTimerRef.current);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      // Remove any lingering gaze classes
      document.querySelectorAll(".gaze-hover, .gaze-activated").forEach((el) => {
        el.classList.remove("gaze-hover", "gaze-activated");
      });
    };
  }, []);

  if (!active) return null;

  const halfSize = cursorSize / 2;

  return (
    <>
      {/* Gaze cursor overlay */}
      <div
        className="gaze-cursor"
        role="presentation"
        aria-hidden="true"
        style={{
          position: "fixed",
          left: gazePos.x - halfSize,
          top: gazePos.y - halfSize,
          width: cursorSize,
          height: cursorSize,
          pointerEvents: "none",
          zIndex: 99999,
          transition: "left 50ms linear, top 50ms linear",
        }}
      >
        {/* Outer ring */}
        <svg
          width={cursorSize}
          height={cursorSize}
          viewBox={`0 0 ${cursorSize} ${cursorSize}`}
          className="gaze-cursor-svg"
        >
          {/* Background ring */}
          <circle
            cx={halfSize}
            cy={halfSize}
            r={halfSize - 2}
            fill="none"
            stroke="rgba(255, 255, 255, 0.3)"
            strokeWidth={2}
          />

          {/* Dwell progress ring */}
          {showProgress && dwellProgress > 0 && (
            <circle
              cx={halfSize}
              cy={halfSize}
              r={halfSize - 2}
              fill="none"
              stroke="#FFD700"
              strokeWidth={3}
              strokeDasharray={`${2 * Math.PI * (halfSize - 2)}`}
              strokeDashoffset={`${2 * Math.PI * (halfSize - 2) * (1 - dwellProgress)}`}
              strokeLinecap="round"
              transform={`rotate(-90 ${halfSize} ${halfSize})`}
              style={{ transition: "stroke-dashoffset 50ms linear" }}
            />
          )}

          {/* Center dot */}
          <circle
            cx={halfSize}
            cy={halfSize}
            r={4}
            fill={dwellProgress > 0 ? "#FFD700" : "rgba(255, 255, 255, 0.6)"}
          />
        </svg>
      </div>

      {/* Connection status indicator (bottom-right) */}
      <div
        className="gaze-status"
        role="status"
        aria-label={isConnected ? "Eye tracker conectado" : "Modo mouse (eye tracker no disponible)"}
        style={{
          position: "fixed",
          bottom: 16,
          right: 16,
          zIndex: 99998,
          background: "rgba(0,0,0,0.7)",
          borderRadius: 8,
          padding: "4px 10px",
          fontSize: 12,
          color: isConnected ? "#2ECC71" : "#F39C12",
          pointerEvents: "none",
        }}
      >
        {isConnected ? "👁️ Eye tracker" : "🖱️ Mouse mode"}
      </div>
    </>
  );
}
