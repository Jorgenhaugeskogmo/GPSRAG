import { useState } from 'react';
import { Layout } from '../src/components/Layout';
import { ChatInterface } from '../src/components/ChatInterface';
import { DocumentUpload } from '../src/components/DocumentUpload';
import { GPSVisualization } from '../src/components/GPSVisualization';

// Eksempel GPS data
const exampleGPSData = [
  { timestamp: '10:00', latitude: 59.9139, longitude: 10.7522 },
  { timestamp: '10:15', latitude: 59.9140, longitude: 10.7525 },
  { timestamp: '10:30', latitude: 59.9142, longitude: 10.7528 },
  { timestamp: '10:45', latitude: 59.9145, longitude: 10.7530 },
  { timestamp: '11:00', latitude: 59.9148, longitude: 10.7535 },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'gps'>('chat');

  const handleFileUpload = async (file: File) => {
    console.log('Uploaded file:', file.name);
    // TODO: Implementer upload til backend
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Upload success:', result);
      } else {
        console.error('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
    }
  };

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
              Last opp
            </button>
            <button
              onClick={() => setActiveTab('gps')}
              className={`px-6 py-2 rounded-lg font-medium transition-all duration-200 ${
                activeTab === 'gps'
                  ? 'bg-white dark:bg-gray-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100'
              }`}
            >
              GPS Data
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="h-[calc(100vh-16rem)]">
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'upload' && <DocumentUpload onUpload={handleFileUpload} />}
          {activeTab === 'gps' && <GPSVisualization data={exampleGPSData} />}
        </div>
      </div>
    </Layout>
  );
} 