/**
 * Utility functions for VoiceClone web app
 */

export function formatSeconds(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function isChrome(): boolean {
  if (typeof window === "undefined") return false;
  return /Chrome/.test(navigator.userAgent);
}

export function isSafari(): boolean {
  if (typeof window === "undefined") return false;
  return /Safari/.test(navigator.userAgent);
}

export function isEdge(): boolean {
  if (typeof window === "undefined") return false;
  return /Edg/.test(navigator.userAgent);
}

export function supportsMediaRecorder(): boolean {
  if (typeof window === "undefined") return false;
  return (
    typeof MediaRecorder !== "undefined" &&
    typeof navigator.mediaDevices !== "undefined"
  );
}
