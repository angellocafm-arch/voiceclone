"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { LandingScreen } from "@/components/LandingScreen";
import { InstallScreen } from "@/components/InstallScreen";
import { CloneScreen } from "@/components/CloneScreen";
import { PersonalityScreen } from "@/components/PersonalityScreen";
import { IntegrationScreen } from "@/components/IntegrationScreen";
import { DashboardScreen } from "@/components/DashboardScreen";

/**
 * VoiceClone — Main App
 *
 * Wizard flow: Landing → Install → Clone → Personality → Integration → Dashboard
 * Designed for people with ALS/ELA: WCAG 2.2 AA, eye tracking, switch access
 */

type Screen =
  | "landing"
  | "install"
  | "clone"
  | "personality"
  | "integration"
  | "dashboard";

interface AppState {
  screen: Screen;
  apiAvailable: boolean;
  voiceId: string | null;
  voiceName: string | null;
  hasPersonality: boolean;
}

export default function Home() {
  const [state, setState] = useState<AppState>({
    screen: "landing",
    apiAvailable: false,
    voiceId: null,
    voiceName: null,
    hasPersonality: false,
  });

  // Check API status on mount and periodically
  useEffect(() => {
    const checkApi = async () => {
      const available = await api.isAvailable();
      setState((prev) => ({ ...prev, apiAvailable: available }));

      // If API is available and user has voices, go to dashboard
      if (available) {
        try {
          const voices = await api.listVoices();
          if (voices.length > 0) {
            const voice = voices[0];
            setState((prev) => ({
              ...prev,
              voiceId: voice.id,
              voiceName: voice.name,
              hasPersonality: voice.has_personality,
              // Don't auto-redirect — let user choose from landing
            }));
          }
        } catch {
          // API available but no voices yet — fine
        }
      }
    };

    checkApi();
    const interval = setInterval(checkApi, 10000);
    return () => clearInterval(interval);
  }, []);

  const navigate = (screen: Screen) => {
    setState((prev) => ({ ...prev, screen }));
    // Scroll to top and announce to screen readers
    window.scrollTo(0, 0);
  };

  const setVoice = (voiceId: string, voiceName: string) => {
    setState((prev) => ({ ...prev, voiceId, voiceName }));
  };

  const setPersonality = (hasPersonality: boolean) => {
    setState((prev) => ({ ...prev, hasPersonality }));
  };

  // Render current screen
  const renderScreen = () => {
    switch (state.screen) {
      case "landing":
        return (
          <LandingScreen
            apiAvailable={state.apiAvailable}
            hasVoice={!!state.voiceId}
            onDownload={() => navigate("install")}
            onOpenApp={() => navigate("dashboard")}
            onStartClone={() => navigate("clone")}
          />
        );

      case "install":
        return (
          <InstallScreen
            onComplete={() => navigate("clone")}
            onCancel={() => navigate("landing")}
          />
        );

      case "clone":
        return (
          <CloneScreen
            apiAvailable={state.apiAvailable}
            onComplete={(voiceId, voiceName) => {
              setVoice(voiceId, voiceName);
              navigate("personality");
            }}
            onBack={() => navigate("landing")}
          />
        );

      case "personality":
        return (
          <PersonalityScreen
            voiceId={state.voiceId!}
            voiceName={state.voiceName!}
            onComplete={(didSetup) => {
              setPersonality(didSetup);
              navigate("integration");
            }}
            onSkip={() => {
              setPersonality(false);
              navigate("integration");
            }}
            onBack={() => navigate("clone")}
          />
        );

      case "integration":
        return (
          <IntegrationScreen
            voiceName={state.voiceName!}
            onUseDirect={() => navigate("dashboard")}
            onBack={() => navigate("personality")}
          />
        );

      case "dashboard":
        return (
          <DashboardScreen
            voiceId={state.voiceId}
            voiceName={state.voiceName}
            hasPersonality={state.hasPersonality}
            apiAvailable={state.apiAvailable}
            onNewVoice={() => navigate("clone")}
            onEditPersonality={() => navigate("personality")}
          />
        );
    }
  };

  return (
    <div aria-live="polite" aria-atomic="true">
      {renderScreen()}
    </div>
  );
}
