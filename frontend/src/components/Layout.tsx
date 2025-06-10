import React, { ReactNode } from 'react';
import { Sun, Moon } from 'lucide-react';

const SatelliteLogo: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
  <svg 
    width={32} 
    height={32} 
    viewBox="0 0 32 32" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <rect x="10" y="12" width="12" height="8" rx="2" fill="currentColor" stroke="currentColor" strokeWidth="1"/>
    <rect x="4" y="14" width="4" height="4" rx="0.5" fill="currentColor" opacity="0.8"/>
    <line x1="4.5" y1="15" x2="7.5" y2="15" stroke="white" strokeWidth="0.3"/>
    <line x1="4.5" y1="16" x2="7.5" y2="16" stroke="white" strokeWidth="0.3"/>
    <line x1="4.5" y1="17" x2="7.5" y2="17" stroke="white" strokeWidth="0.3"/>
    <rect x="24" y="14" width="4" height="4" rx="0.5" fill="currentColor" opacity="0.8"/>
    <line x1="24.5" y1="15" x2="27.5" y2="15" stroke="white" strokeWidth="0.3"/>
    <line x1="24.5" y1="16" x2="27.5" y2="16" stroke="white" strokeWidth="0.3"/>
    <line x1="24.5" y1="17" x2="27.5" y2="17" stroke="white" strokeWidth="0.3"/>
    <circle cx="16" cy="9" r="1.5" fill="currentColor"/>
    <line x1="16" y1="9" x2="16" y2="12" stroke="currentColor" strokeWidth="1"/>
    <path d="M 8 6 Q 16 2 24 6" stroke="currentColor" strokeWidth="1" fill="none" opacity="0.6"/>
    <path d="M 6 8 Q 16 3 26 8" stroke="currentColor" strokeWidth="1" fill="none" opacity="0.4"/>
    <path d="M 4 10 Q 16 4 28 10" stroke="currentColor" strokeWidth="1" fill="none" opacity="0.2"/>
    <circle cx="13" cy="15" r="0.5" fill="white" opacity="0.8"/>
    <circle cx="19" cy="17" r="0.5" fill="white" opacity="0.8"/>
    <rect x="15" y="14" width="2" height="1" rx="0.2" fill="white" opacity="0.6"/>
  </svg>
);

export const Layout: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [dark, setDark] = React.useState(false);
  React.useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-gray-900 transition-colors duration-500">
      <nav className="flex items-center justify-between p-4 bg-gradient-to-r from-indigo-600 to-blue-500 shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
            <SatelliteLogo className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-bold text-white">GPSRAG</h1>
        </div>
        <button
          onClick={() => setDark((prev) => !prev)}
          className="p-2 rounded-full bg-white bg-opacity-20 hover:bg-opacity-30 transition-all duration-200"
        >
          {dark ? <Sun className="w-5 h-5 text-yellow-300" /> : <Moon className="w-5 h-5 text-white" />}
        </button>
      </nav>
      <main className="flex-1 p-6 overflow-auto">{children}</main>
      <footer className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
        &copy; 2025 Tiepoint
      </footer>
    </div>
  );
}; 