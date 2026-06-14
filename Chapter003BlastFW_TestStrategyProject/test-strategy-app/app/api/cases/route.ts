import { NextResponse } from 'next/server';
import { getJiraIssue } from '@/lib/jira';
import { generateContent } from '@/lib/groq';
import fs from 'fs';
import path from 'path';

export async function POST(request: Request) {
  try {
    const { jiraId } = await request.json();
    if (!jiraId) {
      return NextResponse.json({ error: 'Jira ID is required' }, { status: 400 });
    }

    // Fetch Jira Issue
    const issue = await getJiraIssue(jiraId);

    // Read RICE POT Prompt
    const promptPath = path.join(process.cwd(), 'lib/RICE-POT-TestCase-Prompt.md');
    const ricePotContent = fs.readFileSync(promptPath, 'utf8');

    const systemPrompt = `You are an expert QA Functional Tester. Follow the RICE-POT prompt rules exactly:
${ricePotContent}

Output the test cases in a clear Markdown format as listed in the RICE-POT instructions. Make sure to map each test case to the given Jira Ticket requirements.`;

    const userPrompt = `Jira Ticket ID: ${issue.id}
Summary: ${issue.summary}
Description:
${issue.description}

Please generate the Test Cases according to the RICE-POT prompt constraints. Use the ticket description as the PRD context.`;

    // Generate via Groq
    const content = await generateContent(systemPrompt, userPrompt);

    return NextResponse.json({ content });
  } catch (error: any) {
    console.error(error);
    return NextResponse.json({ error: error.message || 'An error occurred' }, { status: 500 });
  }
}
