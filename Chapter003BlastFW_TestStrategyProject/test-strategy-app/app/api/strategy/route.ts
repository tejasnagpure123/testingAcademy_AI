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

    // Read Template
    const templatePath = path.join(process.cwd(), 'lib/Strategy_Template.txt');
    const templateContent = fs.readFileSync(templatePath, 'utf8');

    const systemPrompt = `You are an expert QA Manager. You need to create a Test Strategy for a given Jira ticket.
Please use the following template structure:
${templateContent}

Use markdown formatting to make the strategy look professional and easy to read.`;

    const userPrompt = `Jira Ticket ID: ${issue.id}
Summary: ${issue.summary}
Description:
${issue.description}

Please generate the Test Strategy according to the template provided in the system prompt. Do not include any placeholder text, fill in the details based on the ticket context.`;

    // Generate via Groq
    const content = await generateContent(systemPrompt, userPrompt);

    return NextResponse.json({ content });
  } catch (error: any) {
    console.error(error);
    return NextResponse.json({ error: error.message || 'An error occurred' }, { status: 500 });
  }
}
