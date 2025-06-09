import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { DocumentArrowUpIcon, XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
}

export default function DocumentUpload() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = async (acceptedFiles: File[]) => {
    setIsUploading(true);
    
    for (const file of acceptedFiles) {
      const fileId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
      const newFile: UploadedFile = {
        id: fileId,
        name: file.name,
        size: file.size,
        status: 'uploading',
        progress: 0
      };

      setUploadedFiles(prev => [...prev, newFile]);

      try {
        // Oppdater UI for å vise at opplasting har startet
        setUploadedFiles(prev => 
            prev.map(f => 
              f.id === fileId 
                ? { ...f, status: 'uploading', progress: 25 }
                : f
            )
          );

        const formData = new FormData();
        formData.append('file', file);

        // Last opp til vårt nye serverless endepunkt
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });
        
        // Oppdater UI til prosesserings-steg
        setUploadedFiles(prev => 
            prev.map(f => 
              f.id === fileId 
                ? { ...f, status: 'processing', progress: 75 }
                : f
            )
          );

        if (response.ok) {
          const result = await response.json();
          console.log('Upload result:', result);
          
          // Sett status til ferdig
          setUploadedFiles(prev => 
            prev.map(f => 
              f.id === fileId 
                ? { ...f, status: 'completed', progress: 100 }
                : f
            )
          );
        } else {
          const errorResult = await response.json();
          console.error('Upload failed on server:', errorResult.error);
          throw new Error(errorResult.error || 'Upload failed');
        }
      } catch (error) {
        console.error('Upload error:', error);
        setUploadedFiles(prev => 
          prev.map(f => 
            f.id === fileId 
              ? { ...f, status: 'error', progress: 0 }
              : f
          )
        );
      }
    }
    
    setIsUploading(false);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploading': return 'text-blue-600';
      case 'processing': return 'text-yellow-600';
      case 'completed': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'uploading': return 'Laster opp...';
      case 'processing': return 'Prosesserer...';
      case 'completed': return 'Ferdig';
      case 'error': return 'Feil';
      default: return 'Ukjent';
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Last opp dokumenter
        </h2>
        <p className="text-gray-600">
          Last opp PDF-filer, Word-dokumenter eller tekstfiler for å legge dem til RAG-systemet
        </p>
      </div>

      {/* Drag and Drop Zone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive 
            ? 'border-primary-400 bg-primary-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${isUploading ? 'opacity-50 pointer-events-none' : ''}
        `}
      >
        <input {...getInputProps()} />
        <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        {isDragActive ? (
          <p className="text-primary-600 font-medium">Slipp filene her...</p>
        ) : (
          <div>
            <p className="text-gray-600 mb-2">
              Dra og slipp filer her, eller <span className="text-primary-600 font-medium">klikk for å velge</span>
            </p>
            <p className="text-sm text-gray-500">
              PDF, DOC, DOCX, TXT (maks 10MB)
            </p>
          </div>
        )}
      </div>

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-4">Opplastede filer</h3>
          <div className="space-y-3">
            {uploadedFiles.map((file) => (
              <div key={file.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <button
                      onClick={() => removeFile(file.id)}
                      className="ml-2 text-gray-400 hover:text-gray-600"
                    >
                      <XMarkIcon className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      {formatFileSize(file.size)}
                    </span>
                    <span className={`text-xs font-medium ${getStatusColor(file.status)}`}>
                      {getStatusText(file.status)}
                    </span>
                  </div>
                  {/* Progress bar */}
                  {file.status !== 'completed' && file.status !== 'error' && (
                    <div className="mt-2 bg-gray-200 rounded-full h-1">
                      <div 
                        className="bg-primary-600 h-1 rounded-full transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  )}
                </div>
                {file.status === 'completed' && (
                  <CheckCircleIcon className="h-5 w-5 text-green-500 ml-3" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">Hvordan det fungerer:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>1. Last opp din u-blox brukermanual (PDF)</li>
          <li>2. Systemet ekstraherer tekst og lager vektorembeddings</li>
          <li>3. Gå til Chat Interface for å stille spørsmål</li>
          <li>4. RAG-systemet finner relevant informasjon fra dokumentet</li>
        </ul>
      </div>
    </div>
  );
} 