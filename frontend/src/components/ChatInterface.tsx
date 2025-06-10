import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<{ id: string; text: string; user: boolean }[]>([]);
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text: string, byUser = true) => {
    setMessages((m) => [...m, { id: `${Date.now()}`, text, user: byUser }]);
    setInput('');
    
    // API call to backend
    if (byUser) {
      try {
        const response = await fetch('/api/chat/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: text,
            session_id: 'default-session',
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setMessages((m) => [...m, { 
            id: `${Date.now() + 1}`, 
            text: data.response || 'Beklager, jeg kunne ikke prosessere forespørselen din.', 
            user: false 
          }]);
        } else {
          throw new Error('Failed to get response');
        }
      } catch (error) {
        console.error('Chat error:', error);
        setMessages((m) => [...m, { 
          id: `${Date.now() + 1}`, 
          text: 'Beklager, det oppstod en feil. Sørg for at backend-tjenestene kjører og prøv igjen.', 
          user: false 
        }]);
      }
    }
  };

  const formatTime = (date: Date) => {
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
    setInput(question);
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden">
      <div className="flex-1 p-4 space-y-4 overflow-y-auto scrollbar-thin scrollbar-thumb-blue-400 scrollbar-track-transparent">
        <AnimatePresence>
          {messages.map(({ id, text, user }) => (
            <motion.div
              key={id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`max-w-[70%] px-4 py-2 rounded-xl break-words ${
                user
                  ? 'self-end bg-blue-500 text-white'
                  : 'self-start bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100'
              }`}
            >
              {text}
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={endRef} />
      </div>
      <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (input.trim()) send(input);
          }}
          className="flex items-center space-x-2"
        >
          <input
            className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
            placeholder="Skriv melding..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full transition">
            Send
          </button>
        </form>
      </div>
    </div>
  );
}; 