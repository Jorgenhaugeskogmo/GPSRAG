import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, UserIcon, CpuChipIcon, DocumentIcon } from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: DocumentSource[];
}

interface DocumentSource {
  filename: string;
  page?: number;
  relevance_score: number;
  excerpt: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hei! Jeg er din AI-assistent for GPS-data og dokumentanalyse. Last opp dine u-blox manualer eller andre dokumenter, så kan jeg hjelpe deg med å finne informasjon og analysere GPS-data.',
      timestamp: new Date(),
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const startTime = Date.now();
      setIsLoading(true);

      const response = await fetch(`/api/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          session_id: 'default-session',
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response || 'Beklager, jeg kunne ikke prosessere forespørselen din.',
          timestamp: new Date(),
          sources: data.sources || [],
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      
      // Fallback respons
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Beklager, det oppstod en feil. Sørg for at backend-tjenestene kjører og prøv igjen.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  const formatTime = (date: Date) => {
    if (!isMounted) {
      return '';
    }
    return date.toLocaleTimeString('no-NO', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const exampleQuestions = [
    "Hva er forskjellen mellom GPS og GNSS?",
    "Hvordan konfigurerer jeg u-blox mottakeren for høy nøyaktighet?", 
    "Hvilke NMEA-meldinger støtter u-blox modulene?",
    "Hva er Cold Start vs Warm Start i GPS?",
    "Hvordan aktiverer jeg RTK-modus på u-blox?"
  ];

  const askExampleQuestion = (question: string) => {
    setInputMessage(question);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl px-4 py-3 rounded-lg ${
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  {message.role === 'user' ? (
                    <UserIcon className="h-5 w-5 mt-0.5" />
                  ) : (
                    <CpuChipIcon className="h-5 w-5 mt-0.5" />
                  )}
                </div>
                <div className="flex-1">
                  <ReactMarkdown className="prose prose-sm max-w-none">
                    {message.content}
                  </ReactMarkdown>
                  
                  {/* Document Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 border-t pt-3">
                      <p className="text-xs text-gray-600 mb-2">Kilder:</p>
                      <div className="space-y-2">
                        {message.sources.map((source, index) => (
                          <div key={index} className="bg-white border rounded p-2">
                            <div className="flex items-center space-x-2 mb-1">
                              <DocumentIcon className="h-4 w-4 text-gray-500" />
                              <span className="text-xs font-medium text-gray-700">
                                {source.filename}
                              </span>
                              {source.page && (
                                <span className="text-xs text-gray-500">
                                  Side {source.page}
                                </span>
                              )}
                              <span className="text-xs text-green-600">
                                {Math.round(source.relevance_score * 100)}% match
                              </span>
                            </div>
                            <p className="text-xs text-gray-600 italic">
                              "{source.excerpt}"
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <p className="text-xs mt-2 opacity-70">
                    {formatTime(message.timestamp)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 px-4 py-3 rounded-lg">
              <div className="flex items-center space-x-3">
                <CpuChipIcon className="h-5 w-5 animate-pulse" />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Example Questions */}
      {messages.length === 1 && (
        <div className="p-4 border-t bg-gray-50">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Eksempelspørsmål:</h4>
          <div className="flex flex-wrap gap-2">
            {exampleQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => askExampleQuestion(question)}
                className="text-sm bg-white border border-gray-300 rounded-full px-3 py-1 hover:bg-gray-100 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message Input */}
      <form onSubmit={sendMessage} className="p-4 border-t bg-white">
        <div className="flex space-x-3">
          <div className="flex-1">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Still et spørsmål om GPS, u-blox eller dine opplastede dokumenter..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={isLoading}
            />
          </div>
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </div>
      </form>
    </div>
  );
} 