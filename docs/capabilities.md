# Mini RAG System Capabilities

## Overview
The Mini RAG (Retrieval-Augmented Generation) system is an AI-powered document assistant that can help you with various tasks related to document analysis and question answering.

## Core Capabilities

### Document Processing
- **File Upload**: Supports PDF, Markdown (.md), and Text (.txt) files
- **Document Indexing**: Automatically processes and indexes uploaded documents
- **Text Chunking**: Breaks down documents into manageable chunks for better retrieval
- **Vector Search**: Uses semantic search to find relevant information

### Question Answering
- **Natural Language Queries**: Answer questions in conversational style
- **Context-Aware Responses**: Uses relevant document sections to provide accurate answers
- **Source Attribution**: References specific documents and sections
- **Streaming Responses**: Real-time answer generation for better user experience

### Information Retrieval
- **Semantic Search**: Find information based on meaning, not just keywords
- **Multi-Document Search**: Search across multiple uploaded documents
- **Relevance Ranking**: Returns most relevant information first
- **Context Preservation**: Maintains document context in responses

### User Interface
- **Web Interface**: Modern, responsive web UI for easy interaction
- **Authentication**: Secure login system with role-based access
- **File Management**: Upload, organize, and manage documents
- **Chat Interface**: Interactive Q&A with streaming responses

### Technical Features
- **Local AI Models**: Uses Ollama with llama3.1:8b for text generation
- **Vector Database**: Qdrant for persistent document storage
- **API Access**: RESTful API for programmatic access
- **Docker Support**: Easy deployment with Docker Compose

## Use Cases

### Business Applications
- **Document Analysis**: Analyze contracts, reports, and business documents
- **Knowledge Management**: Create searchable knowledge bases
- **Research Assistance**: Help with research and information gathering
- **Content Creation**: Generate content based on existing documents

### Educational Applications
- **Study Assistant**: Help students understand course materials
- **Research Support**: Assist with academic research and writing
- **Document Summarization**: Create summaries of long documents
- **Question Answering**: Answer questions about course content

### Personal Applications
- **Personal Knowledge Base**: Organize and search personal documents
- **Reading Assistant**: Help understand complex documents
- **Information Retrieval**: Quickly find specific information
- **Content Organization**: Organize and categorize documents

## System Requirements
- **AI Models**: Ollama with llama3.1:8b and nomic-embed-text
- **Storage**: Qdrant vector database for document embeddings
- **Web Server**: FastAPI with Uvicorn
- **Authentication**: JWT-based security system

## Getting Started
1. Upload documents using the web interface
2. Wait for automatic indexing to complete
3. Start asking questions about your documents
4. Use streaming mode for real-time responses
5. Access API endpoints for programmatic use

## Security Features
- **User Authentication**: Secure login with JWT tokens
- **Role-Based Access**: Admin and user roles with different permissions
- **Local Processing**: All data stays on your local machine
- **Encrypted Storage**: Secure document and user data storage