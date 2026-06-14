export function extractTextFromAdf(doc: any): string {
  if (!doc) return '';
  if (typeof doc === 'string') return doc;
  if (doc.type === 'text') return doc.text || '';
  
  let text = '';
  if (Array.isArray(doc.content)) {
    text = doc.content.map(extractTextFromAdf).join(' ');
  }
  
  // Add newlines for paragraphs or block quotes
  if (doc.type === 'paragraph' || doc.type === 'heading') {
    text += '\n';
  }
  
  return text;
}

export async function getJiraIssue(issueId: string) {
  // Ensure url ends with / if not present in env
  let baseUrl = process.env.JIRA_URL || '';
  if (!baseUrl.endsWith('/')) baseUrl += '/';
  
  const url = `${baseUrl}rest/api/3/issue/${issueId}`;
  const auth = Buffer.from(`${process.env.JIRA_EMAIL}:${process.env.JIRA_TOKEN}`).toString('base64');

  const response = await fetch(url, {
    headers: {
      'Authorization': `Basic ${auth}`,
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to fetch Jira issue ${issueId}: ${response.status} - ${text}`);
  }

  const data = await response.json();
  
  const descriptionText = extractTextFromAdf(data.fields.description);

  return {
    id: data.key,
    summary: data.fields.summary,
    description: descriptionText.trim(),
  };
}
