import { useState } from 'react';
import { Layout } from '../components/Layout';
import ChatInterface from '../components/chat/ChatInterface';
import DocumentUpload from '../components/upload/DocumentUpload';
import { DocumentTextIcon } from '@heroicons/react/24/outline';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'upload'>('chat');

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        {/* Tab Navigation */}
        <div className="flex justify-center mb-6">
          <div className="flex bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-6 py-2 rounded-lg font-medium transition-all duration-200 ${
                activeTab === 'chat'
                  ? 'bg-white dark:bg-gray-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100'
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-6 py-2 rounded-lg font-medium transition-all duration-200 ${
                activeTab === 'upload'
                  ? 'bg-white dark:bg-gray-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100'
              }`}
            >
              Last opp dokumenter
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="h-[calc(100vh-16rem)]">
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'upload' && <DocumentUpload />}
        </div>
      </div>
    </Layout>
  );
} 