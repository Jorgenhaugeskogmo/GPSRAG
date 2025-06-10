import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud } from 'lucide-react';

export const DocumentUpload: React.FC<{ onUpload: (file: File) => void }> = ({ onUpload }) => {
  const onDrop = useCallback((accepted: File[]) => {
    accepted.forEach(onUpload);
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop, 
    accept: { 'application/pdf': ['.pdf'] } 
  });

  return (
    <div
      {...getRootProps()}
      className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-indigo-400 rounded-xl bg-white dark:bg-gray-700 hover:bg-indigo-50 dark:hover:bg-gray-600 transition cursor-pointer"
    >
      <input {...getInputProps()} />
      <UploadCloud className="w-12 h-12 text-indigo-400 mb-4 animate-bounce" />
      <p className="text-gray-600 dark:text-gray-300">
        {isDragActive ? 'Slipp filen her...' : 'Dra og slipp PDF, eller trykk for å velge'}
      </p>
    </div>
  );
}; 