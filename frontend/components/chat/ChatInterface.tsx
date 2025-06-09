'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { PaperAirplaneIcon, LightBulbIcon } from '@heroicons/react/24/outline';
import { SatelliteLogo } from '../icons/SatelliteLogo';

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

const suggestions = [
  'Hva er forskjellen mellom GPS og GNSS?',
  'Hvordan konfigurerer jeg u-blox for høy nøyaktighet?',
  'Hvilke NMEA-meldinger støttes?',
  'Hva er Cold vs Warm Start i GPS?',
  'Hvordan aktiverer jeg RTK-modus?'
];

// Funksjon for å generere UUID
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      id: generateUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage: Message = {
          id: generateUUID(),
          role: 'assistant',
          content: data.response || 'Beklager, jeg kunne ikke behandle forespørselen din.',
          timestamp: new Date(),
          sources: data.sources || [],
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('API-feil');
      }
    } catch (error) {
      const errorMessage: Message = {
        id: generateUUID(),
        role: 'assistant',
        content: 'Beklager, det oppstod en feil. Prøv igjen senere.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700">
      {/* Welcome Screen */}
      {messages.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            className="text-center max-w-2xl"
          >
            {/* Logo */}
            <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-xl">
              <SatelliteLogo className="w-12 h-12 text-white" />
            </div>

            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">
              Hvordan kan jeg hjelpe deg?
            </h1>
            
            <p className="text-gray-600 dark:text-gray-400 mb-8">
              Din KI-assistent under arbeidet med GPS-nettverket
            </p>

            {/* Suggestion Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl">
              {suggestions.map((suggestion, index) => (
                <motion.button
                  key={suggestion}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + index * 0.1 }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="group p-4 bg-white dark:bg-gray-700 rounded-xl border border-gray-200 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-500 transition-all duration-200 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-start space-x-3">
                    <LightBulbIcon className="w-5 h-5 text-indigo-500 group-hover:text-indigo-600 transition-colors flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">
                      {suggestion}
                    </p>
                  </div>
                </motion.button>
              ))}
            </div>
          </motion.div>
        </div>
      )}

      {/* Messages */}
      {messages.length > 0 && (
        <div className="flex-1 p-4 space-y-4 overflow-y-auto scrollbar-thin scrollbar-thumb-indigo-400 scrollbar-track-transparent">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[70%] px-4 py-3 rounded-2xl break-words shadow-sm ${
                  message.role === 'user'
                    ? 'bg-indigo-500 text-white'
                    : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-600'
                }`}>
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      transition={{ delay: 0.2 }}
                      className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600"
                    >
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">Kilder:</p>
                      <div className="space-y-2">
                        {message.sources.slice(0, 2).map((source, index) => (
                          <div key={index} className="p-2 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
                            <p className="text-xs font-medium text-gray-700 dark:text-gray-300">📄 {source.filename}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              Relevans: {(source.relevance_score * 100).toFixed(1)}%
                            </p>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Loading indicator */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-2xl px-4 py-3 shadow-sm">
                <div className="flex space-x-1">
                  <motion.div
                    animate={{ y: [0, -4, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                    className="w-2 h-2 bg-indigo-400 rounded-full"
                  />
                  <motion.div
                    animate={{ y: [0, -4, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                    className="w-2 h-2 bg-indigo-400 rounded-full"
                  />
                  <motion.div
                    animate={{ y: [0, -4, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                    className="w-2 h-2 bg-indigo-400 rounded-full"
                  />
                </div>
              </div>
            </motion.div>
          )}
          
          <div ref={endRef} />
        </div>
      )}

      {/* Input Area */}
      <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <form onSubmit={handleSubmit} className="flex items-center space-x-2">
          <input
            className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-400 transition-all duration-200 placeholder-gray-500 dark:placeholder-gray-400"
            placeholder="Skriv melding..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <button 
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-full transition-all duration-200 shadow-sm hover:shadow-md"
          >
            <PaperAirplaneIcon className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
} 