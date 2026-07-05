const fs = require('fs');
const path = require('path');
const { PDFLoader } = require('@langchain/community/document_loaders/fs/pdf');
const { Document } = require('@langchain/core/documents');
const { RecursiveCharacterTextSplitter } = require('@langchain/textsplitters');
const { OllamaEmbeddings } = require('@langchain/ollama');
const { Chroma } = require('@langchain/community/vectorstores/chroma');
const { ChatGroq } = require('@langchain/groq');
const { PromptTemplate } = require('@langchain/core/prompts');
const { StringOutputParser } = require('@langchain/core/output_parsers');

// Initialize Ollama Embeddings
const embeddings = new OllamaEmbeddings({
    model: 'nomic-embed-text', // Ensure you have this model pulled in Ollama (ollama pull nomic-embed-text)
});

// Configure local Chroma vector store
const collectionName = 'vwo_prd_collection';
let vectorStore;

async function getVectorStore() {
    if (!vectorStore) {
        vectorStore = new Chroma(embeddings, {
            collectionName: collectionName,
            url: "http://localhost:8000" // We'll assume chroma is running locally or we'll just let it create a local dir?
        });
    }
    return vectorStore;
}

async function ingestDocument() {
    const dataPath = path.resolve(__dirname, '../data/Product Requirements Document_(PRD)_VWO.com.pdf');
    
    // 1. Read PDF using LangChain's PDFLoader
    const loader = new PDFLoader(dataPath);
    const docs = await loader.load();

    // 2. Split into chunks
    const splitter = new RecursiveCharacterTextSplitter({
        chunkSize: 1000,
        chunkOverlap: 200,
    });
    const output = await splitter.splitDocuments(docs);

    // Sanitize metadata (ChromaDB doesn't accept complex nested objects like the 'pdf' object from PDFLoader)
    const sanitizedOutput = output.map(doc => {
        const cleanMetadata = {};
        for (const [key, value] of Object.entries(doc.metadata)) {
            if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
                cleanMetadata[key] = value;
            }
        }
        return new Document({
            pageContent: doc.pageContent,
            metadata: cleanMetadata
        });
    });

    // 3 & 4. Generate Embeddings and Store in ChromaDB
    const store = new Chroma(embeddings, {
        collectionName: collectionName
    });
    
    // Let's add documents
    await Chroma.fromDocuments(sanitizedOutput, embeddings, {
        collectionName: collectionName,
    });

    return {
        chunks: output.length,
        message: `Successfully ingested ${output.length} chunks.`
    };
}

async function queryDocument(query) {
    const store = new Chroma(embeddings, {
        collectionName: collectionName
    });

    // 5. Query Interface - retrieve top 4 chunks
    const results = await store.similaritySearch(query, 4);
    const chunks = results.map(doc => doc.pageContent);

    // 6. Generate final answer with Groq
    const llm = new ChatGroq({
        apiKey: process.env.GROQ_API_KEY,
        model: 'llama-3.3-70b-versatile', // Using a currently supported model on Groq
        temperature: 0.1,
    });

    const prompt = PromptTemplate.fromTemplate(`
    You are a helpful assistant that answers questions based on the provided context.
    If you don't know the answer based on the context, say so.
    
    Context:
    {context}
    
    Question: {question}
    
    Answer:
    `);

    const chain = prompt.pipe(llm).pipe(new StringOutputParser());
    
    const context = chunks.join('\n\n---\n\n');
    const answer = await chain.invoke({
        context: context,
        question: query
    });

    return {
        answer,
        retrievedChunks: chunks
    };
}

module.exports = {
    ingestDocument,
    queryDocument
};
