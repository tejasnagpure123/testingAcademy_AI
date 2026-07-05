require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { ingestDocument, queryDocument } = require('./ragService');

const app = express();
const port = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Ingest endpoint
app.post('/api/ingest', async (req, res) => {
    try {
        const result = await ingestDocument();
        res.json({ success: true, message: 'Ingestion completed successfully!', ...result });
    } catch (error) {
        console.error('Ingestion error:', error);
        res.status(500).json({ success: false, message: error.message });
    }
});

// Query endpoint
app.post('/api/query', async (req, res) => {
    const { query } = req.body;
    if (!query) {
        return res.status(400).json({ success: false, message: 'Query is required.' });
    }

    try {
        const result = await queryDocument(query);
        res.json({ success: true, ...result });
    } catch (error) {
        console.error('Query error:', error);
        res.status(500).json({ success: false, message: error.message });
    }
});

app.listen(port, () => {
    console.log(`RAG Backend server listening on port ${port}`);
});
