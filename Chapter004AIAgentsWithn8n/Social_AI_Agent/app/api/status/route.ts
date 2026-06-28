import { NextResponse } from 'next/server';
import { currentStatus } from '@/lib/pipeline';
import { getNextScheduledTime } from '@/lib/scheduler';
import { Groq } from 'groq-sdk';
import { GoogleGenAI } from '@google/genai';

// Cache verification check results for 60 seconds to prevent API rate limiting from status polling
let cachedKeyHealth: { groq: boolean; gemini: boolean; lastChecked: number } | null = null;
const CACHE_TTL_MS = 60 * 1000;

async function checkApiKeyHealth() {
  const now = Date.now();
  if (cachedKeyHealth && (now - cachedKeyHealth.lastChecked < CACHE_TTL_MS)) {
    return { groq: cachedKeyHealth.groq, gemini: cachedKeyHealth.gemini };
  }

  let groqValid = false;
  let geminiValid = false;

  const groqKey = process.env.GROQ_API_KEY || process.env.GROQ_KEY;
  const geminiKey = process.env.GEMINI_API_KEY || process.env.GEMINI_KEY;

  if (groqKey) {
    try {
      const groq = new Groq({ apiKey: groqKey });
      await groq.chat.completions.create({
        model: 'llama-3.3-70b-versatile',
        messages: [{ role: 'user', content: 'ping' }],
        max_tokens: 1,
      });
      groqValid = true;
    } catch (e) {
      console.warn('[API Key Health Check] Groq test failed:', e);
    }
  }

  if (geminiKey) {
    try {
      const ai = new GoogleGenAI({ apiKey: geminiKey });
      await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: 'ping',
        config: { maxOutputTokens: 1 }
      });
      geminiValid = true;
    } catch (e) {
      console.warn('[API Key Health Check] Gemini test failed:', e);
    }
  }

  cachedKeyHealth = {
    groq: groqValid,
    gemini: geminiValid,
    lastChecked: now
  };

  return { groq: groqValid, gemini: geminiValid };
}

export async function GET() {
  try {
    const keyHealth = await checkApiKeyHealth();
    const nextScheduled = getNextScheduledTime();

    return NextResponse.json({
      success: true,
      pipeline: currentStatus,
      nextScheduled,
      keys: keyHealth
    });
  } catch (error: any) {
    console.error('[API /api/status] Status fetch failed:', error);
    return NextResponse.json(
      { success: false, error: error.message || String(error) },
      { status: 500 }
    );
  }
}
