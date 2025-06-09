import React, { ReactNode } from 'react';
import { Sun, Moon } from 'lucide-react';
import { SatelliteLogo } from './icons/SatelliteLogo';

export const Layout: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [dark, setDark] = React.useState(false);
  React.useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900 transition-colors duration-500">
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
      <main className="flex-1 p-6 overflow-auto bg-gray-50 dark:bg-gray-900">{children}</main>
      <footer className="p-4 text-center text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
        &copy; 2025 NLAT og EMT
      </footer>
    </div>
  );
}; 