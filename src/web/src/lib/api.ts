/**
 * VoiceClone API Client
 * Communicates with local FastAPI server on port 8765
 */

const API_BASE = "http://localhost:8765";

class VoiceCloneAPI {
  async isAvailable(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/health`, {
        method: "GET",
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  async cloneVoice(formData: FormData): Promise<{ id: string; name: string }> {
    const response = await fetch(`${API_BASE}/clone`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Clone failed: ${response.statusText}`);
    }

    return response.json();
  }

  async synthesize(text: string, voiceId: string): Promise<ArrayBuffer> {
    const response = await fetch(`${API_BASE}/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice_id: voiceId }),
    });

    if (!response.ok) {
      throw new Error(`Synthesis failed: ${response.statusText}`);
    }

    return response.arrayBuffer();
  }

  async listVoices(): Promise<Array<{ id: string; name: string; has_personality?: boolean }>> {
    const response = await fetch(`${API_BASE}/voices`, {
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(`List failed: ${response.statusText}`);
    }

    return response.json();
  }

  async deleteVoice(voiceId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/voices/${voiceId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`Delete failed: ${response.statusText}`);
    }
  }

  async setupPersonality(
    voiceId: string,
    answers: Record<number, string>
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/personality/setup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ voice_id: voiceId, answers }),
    });

    if (!response.ok) {
      throw new Error(`Setup failed: ${response.statusText}`);
    }
  }

  async synthesizeWithPersonality(
    text: string,
    voiceId: string
  ): Promise<ArrayBuffer> {
    const response = await fetch(`${API_BASE}/personality/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice_id: voiceId }),
    });

    if (!response.ok) {
      throw new Error(`Personality synthesis failed: ${response.statusText}`);
    }

    return response.arrayBuffer();
  }
}

export const api = new VoiceCloneAPI();
