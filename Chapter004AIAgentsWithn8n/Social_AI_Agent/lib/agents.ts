import { Groq } from 'groq-sdk';
import { GoogleGenAI } from '@google/genai';
import fs from 'fs';
import path from 'path';
import { ExcelManager } from './excelManager';
import { ContentRow } from './types';

const KEYWORDS = [
  "QA", "MCP", "RAG", "LLM", "AI Agents", "n8n", "LangFlow", "Crew AI",
  "DeepEval", "LangChain", "AI Harness", "LLM Eval"
];

// Helper to get formatted date string for today (local time YYYY-MM-DD)
export function getTodayDateString(): string {
  return new Date().toLocaleDateString('en-CA'); // en-CA returns YYYY-MM-DD
}

// -------------------------------------------------------------
// AGENT 1: Topic Generator
// -------------------------------------------------------------
export async function runAgent1TopicGenerator(excelManager: ExcelManager): Promise<ContentRow> {
  console.log('[Agent 1] Running Topic Generator...');
  const todayStr = getTodayDateString();

  // Load existing topics to avoid duplicates
  const rows = await excelManager.readRows();
  
  // Check if today's row already exists
  const todayRow = rows.find(r => r.date === todayStr);
  if (todayRow && todayRow.topic && todayRow.status !== 'Error') {
    console.log(`[Agent 1] Topic already exists for today (${todayStr}): "${todayRow.topic}"`);
    return todayRow;
  }

  const usedTopics = rows.map(r => r.topic).filter(Boolean);

  const groqKey = process.env.GROQ_API_KEY || process.env.GROQ_KEY;
  if (!groqKey) {
    throw new Error('GROQ_API_KEY or GROQ_KEY is not defined in environment variables.');
  }

  const groq = new Groq({ apiKey: groqKey });
  const prompt = `You are a Content Topic Generator.
Choose ONE keyword from this pool: ${JSON.stringify(KEYWORDS)}.
Generate a single, fresh, highly technical, and engaging content topic title based on that keyword.
Do NOT repeat or closely resemble any of these already used topics:
${usedTopics.map(t => `- ${t}`).join('\n')}

Response Format:
Return ONLY the raw topic title. Do not wrap in quotes, do not include any introductory or concluding text, and do not explain your choice.`;

  const completion = await groq.chat.completions.create({
    model: 'llama-3.3-70b-versatile',
    messages: [
      { role: 'system', content: 'You generate raw, publishable topic titles for tech content developers. You do not talk to the user. You output ONLY the title.' },
      { role: 'user', content: prompt }
    ],
    temperature: 0.8,
  });

  const topic = (completion.choices[0]?.message?.content || '').trim().replace(/^["']|["']$/g, '');
  if (!topic) {
    throw new Error('Failed to generate a topic from Groq.');
  }

  console.log(`[Agent 1] Generated Topic: "${topic}"`);

  // Create new or update today's row
  const newRow: ContentRow = {
    date: todayStr,
    topic,
    status: 'Pending',
    lastUpdated: new Date().toISOString(),
    writtenBy: 'Agent 1'
  };

  // Agent 4 (integrated): save back immediately
  await excelManager.saveRow(newRow);
  return newRow;
}

// -------------------------------------------------------------
// AGENT 2: Content Writer
// -------------------------------------------------------------
const WRITER_SYSTEM_PROMPT = `You are an expert technical content writer.
You write in a direct, opinionated, professional technical voice.
Rules:
1. Write short paragraphs.
2. Provide concrete, real examples or technical context.
3. Absolutely NO filler phrases like "game-changer", "dive deep", "in this digital age", "revolutionary", "look no further", "let's explore", "crucial", or "essential".
4. Write clear, publish-ready content without conversational intros/outros.`;

export async function runAgent2ContentWriter(excelManager: ExcelManager): Promise<ContentRow> {
  console.log('[Agent 2] Running Content Writer...');
  const todayStr = getTodayDateString();
  const rows = await excelManager.readRows();
  
  // Match on today's row
  let todayRow = rows.find(r => r.date === todayStr);
  if (!todayRow) {
    throw new Error(`[Agent 2] No row found for today's date (${todayStr}). Run Topic Generator first.`);
  }

  const topic = todayRow.topic;
  console.log(`[Agent 2] Writing content for topic: "${topic}"`);

  // Set status to Writing
  todayRow.status = 'Writing';
  todayRow.writtenBy = 'Agent 2';
  todayRow.lastUpdated = new Date().toISOString();
  await excelManager.saveRow(todayRow);

  const groqKey = process.env.GROQ_API_KEY || process.env.GROQ_KEY;
  if (!groqKey) {
    throw new Error('GROQ_API_KEY or GROQ_KEY is not defined.');
  }

  const groq = new Groq({ apiKey: groqKey });

  // Function to request Groq with standard format
  const write = async (prompt: string): Promise<string> => {
    const response = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages: [
        { role: 'system', content: WRITER_SYSTEM_PROMPT },
        { role: 'user', content: prompt }
      ],
      temperature: 0.7,
    });
    return (response.choices[0]?.message?.content || '').trim();
  };

  // Write content in parallel to save time
  console.log('[Agent 2] Launching generation tasks in parallel...');
  const [linkedin, medium, ig, yt, devto] = await Promise.all([
    write(`Write a hook-driven LinkedIn post (~150-200 words) about: "${topic}". Include technical details, 2-3 bullet points of insights, and appropriate hashtags.`),
    
    write(`Write a comprehensive, deep-dive Medium article (aim for 2500-3000 words, in markdown with headings) about: "${topic}". Include real architectural considerations, code blocks or config structures, and a critical analysis of trade-offs.`),
    
    write(`Write an Instagram script (reel/carousel format) about: "${topic}". Include slide/frame indicators, short spoken lines, visual cues, and hashtags.`),
    
    write(`Write a YouTube video script about: "${topic}". Include an Intro, Body (divided into logical sub-sections with timestamps), and Outro, along with speaker text and visual directions.`),
    
    write(`Write a highly technical, hands-on Dev.to article (aim for 1500-2000 words, in markdown) about: "${topic}". Focus on implementation steps, error handling, config snippets, and clear developer value.`)
  ]);

  todayRow.linkedinPost = linkedin;
  todayRow.mediumArticle = medium;
  todayRow.igScript = ig;
  todayRow.ytScript = yt;
  todayRow.devtoArticle = devto;
  
  // Set status to Imaging
  todayRow.status = 'Imaging';
  todayRow.lastUpdated = new Date().toISOString();

  // Save results back
  await excelManager.saveRow(todayRow);
  console.log('[Agent 2] Writing content completed successfully.');
  return todayRow;
}

// -------------------------------------------------------------
// AGENT 3: Image Generator
// -------------------------------------------------------------
async function generateSingleImage(ai: GoogleGenAI, prompt: string, aspectRatio: '1:1' | '16:9'): Promise<string> {
  // Method 1: Try stable Imagen model via models.generateImages
  try {
    console.log(`[Agent 3] Trying generateImages with 'imagen-3.0-generate-002' (aspect ratio: ${aspectRatio})...`);
    const response = await ai.models.generateImages({
      model: 'imagen-3.0-generate-002',
      prompt: prompt,
      config: {
        numberOfImages: 1,
        aspectRatio: aspectRatio,
      }
    });
    const base64 = response.generatedImages?.[0]?.image?.imageBytes;
    if (base64) return base64;
  } catch (e: any) {
    console.warn(`[Agent 3] imagen-3.0-generate-002 failed: ${e.message || e}`);
  }

  // Method 2: Try gemini-2.5-flash-image via models.generateImages
  try {
    console.log(`[Agent 3] Trying generateImages with 'gemini-2.5-flash-image' (aspect ratio: ${aspectRatio})...`);
    const response = await ai.models.generateImages({
      model: 'gemini-2.5-flash-image',
      prompt: prompt,
      config: {
        numberOfImages: 1,
        aspectRatio: aspectRatio,
      }
    });
    const base64 = response.generatedImages?.[0]?.image?.imageBytes;
    if (base64) return base64;
  } catch (e: any) {
    console.warn(`[Agent 3] gemini-2.5-flash-image generateImages failed: ${e.message || e}`);
  }

  // Method 3: Try multimodal gemini-2.5-flash-image via generateContent
  try {
    console.log(`[Agent 3] Trying generateContent with 'gemini-2.5-flash-image' (aspect ratio: ${aspectRatio})...`);
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash-image',
      contents: prompt,
      config: {
        responseModalities: ['IMAGE'],
        imageConfig: {
          aspectRatio: aspectRatio,
        }
      }
    });

    for (const part of response.candidates?.[0]?.content?.parts || []) {
      if (part.inlineData?.data) {
        return part.inlineData.data;
      }
    }
  } catch (e: any) {
    console.warn(`[Agent 3] Multimodal generateContent failed: ${e.message || e}`);
  }

  throw new Error(`All image generation attempts failed for prompt: "${prompt}"`);
}

export async function runAgent3ImageGenerator(excelManager: ExcelManager): Promise<ContentRow> {
  console.log('[Agent 3] Running Image Generator...');
  const todayStr = getTodayDateString();
  const rows = await excelManager.readRows();
  
  let todayRow = rows.find(r => r.date === todayStr);
  if (!todayRow) {
    throw new Error(`[Agent 3] No row found for today's date (${todayStr}). Run Topic/Content generator first.`);
  }

  const topic = todayRow.topic;
  console.log(`[Agent 3] Generating images for topic: "${topic}"`);

  const geminiKey = process.env.GEMINI_API_KEY || process.env.GEMINI_KEY;
  if (!geminiKey) {
    throw new Error('GEMINI_API_KEY or GEMINI_KEY is not defined in environment variables.');
  }

  const ai = new GoogleGenAI({ apiKey: geminiKey });

  // Create public/images directory if it doesn't exist
  const imagesDir = path.join(process.cwd(), 'public', 'images');
  if (!fs.existsSync(imagesDir)) {
    fs.mkdirSync(imagesDir, { recursive: true });
  }

  const timestamp = Date.now();

  try {
    // Generate the 3 images in parallel
    console.log('[Agent 3] Launching image generation tasks in parallel...');
    
    const [mediumBase64, linkedinBase64, instagramBase64] = await Promise.all([
      // Medium: 16:9
      generateSingleImage(
        ai,
        `A high-quality sleek landscape cover illustration for a tech publication about: "${topic}". Modern abstract digital art, vibrant colors, tech themed.`,
        '16:9'
      ),
      // LinkedIn: 16:9 or 3:2 (using 16:9 for clean landscape)
      generateSingleImage(
        ai,
        `A clean corporate banner landscape graphic for a professional network post about: "${topic}". Minimalist design, high tech infographic elements.`,
        '16:9'
      ),
      // Instagram: 1:1 square
      generateSingleImage(
        ai,
        `A bold, eye-catching square graphic for social media about: "${topic}". Vibrant high contrast design, central visual element.`,
        '1:1'
      )
    ]);

    // Save buffers to files
    const mediumFile = `medium_${timestamp}.png`;
    const linkedinFile = `linkedin_${timestamp}.png`;
    const instagramFile = `instagram_${timestamp}.png`;

    await fs.promises.writeFile(path.join(imagesDir, mediumFile), Buffer.from(mediumBase64, 'base64'));
    await fs.promises.writeFile(path.join(imagesDir, linkedinFile), Buffer.from(linkedinBase64, 'base64'));
    await fs.promises.writeFile(path.join(imagesDir, instagramFile), Buffer.from(instagramBase64, 'base64'));

    todayRow.mediumImage = `/images/${mediumFile}`;
    todayRow.linkedinImage = `/images/${linkedinFile}`;
    todayRow.igImage = `/images/${instagramFile}`;
    
    // Status is complete!
    todayRow.status = 'Done';
    todayRow.lastUpdated = new Date().toISOString();
    todayRow.writtenBy = 'Agent 3';

    await excelManager.saveRow(todayRow);
    console.log('[Agent 3] Image generation and save complete.');
    return todayRow;
  } catch (error: any) {
    console.error('[Agent 3] Error during image generation:', error);
    
    todayRow.status = 'Error';
    todayRow.lastUpdated = new Date().toISOString();
    todayRow.writtenBy = 'Agent 3';
    
    await excelManager.saveRow(todayRow);
    throw error;
  }
}
