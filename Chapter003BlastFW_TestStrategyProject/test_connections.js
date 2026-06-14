const fs = require('fs');
const https = require('https');

// Simple script to test Jira Connection
const env = fs.readFileSync('.env', 'utf8');
const envVars = {};
env.split('\n').forEach(line => {
  const match = line.match(/^([^=]+)=(.*)$/);
  if (match) {
    envVars[match[1]] = match[2].replace(/^["'](.*)["']$/, '$1'); // remove quotes
  }
});

const url = new URL('rest/api/3/myself', envVars.JIRA_URL);

const options = {
  hostname: url.hostname,
  path: url.pathname,
  method: 'GET',
  headers: {
    'Authorization': 'Basic ' + Buffer.from(envVars.JIRA_EMAIL + ':' + envVars.JIRA_TOKEN).toString('base64'),
    'Accept': 'application/json'
  }
};

const req = https.request(options, res => {
  console.log(`Jira API Status Code: ${res.statusCode}`);
  res.on('data', d => {
    // console.log(d.toString());
  });
});

req.on('error', error => {
  console.error(error);
});

req.end();

// Test Groq API Connection
const groqOptions = {
  hostname: 'api.groq.com',
  path: '/openai/v1/models',
  method: 'GET',
  headers: {
    'Authorization': 'Bearer ' + envVars.GROQ_KEY,
    'Accept': 'application/json'
  }
};

const groqReq = https.request(groqOptions, res => {
  console.log(`Groq API Status Code: ${res.statusCode}`);
});

groqReq.on('error', error => {
  console.error(error);
});

groqReq.end();
