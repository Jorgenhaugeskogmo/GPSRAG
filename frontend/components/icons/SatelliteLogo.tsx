import React from 'react';

interface SatelliteLogoProps {
  className?: string;
  size?: number;
}

export const SatelliteLogo: React.FC<SatelliteLogoProps> = ({ 
  className = "w-6 h-6", 
  size = 32 
}) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 32 32" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Satellitt kropp */}
      <rect x="10" y="12" width="12" height="8" rx="2" fill="currentColor" stroke="currentColor" strokeWidth="1"/>
      
      {/* Solpanel venstre */}
      <rect x="4" y="14" width="4" height="4" rx="0.5" fill="currentColor" opacity="0.8"/>
      <line x1="4.5" y1="15" x2="7.5" y2="15" stroke="white" strokeWidth="0.3"/>
      <line x1="4.5" y1="16" x2="7.5" y2="16" stroke="white" strokeWidth="0.3"/>
      <line x1="4.5" y1="17" x2="7.5" y2="17" stroke="white" strokeWidth="0.3"/>
      
      {/* Solpanel høyre */}
      <rect x="24" y="14" width="4" height="4" rx="0.5" fill="currentColor" opacity="0.8"/>
      <line x1="24.5" y1="15" x2="27.5" y2="15" stroke="white" strokeWidth="0.3"/>
      <line x1="24.5" y1="16" x2="27.5" y2="16" stroke="white" strokeWidth="0.3"/>
      <line x1="24.5" y1="17" x2="27.5" y2="17" stroke="white" strokeWidth="0.3"/>
      
      {/* Antenne */}
      <circle cx="16" cy="9" r="1.5" fill="currentColor"/>
      <line x1="16" y1="9" x2="16" y2="12" stroke="currentColor" strokeWidth="1"/>
      
      {/* Signal linjer */}
      <path d="M 8 6 Q 16 2 24 6" stroke="currentColor" strokeWidth="1" fill="none" opacity="0.6"/>
      <path d="M 6 8 Q 16 3 26 8" stroke="currentColor" strokeWidth="1" fill="none" opacity="0.4"/>
      <path d="M 4 10 Q 16 4 28 10" stroke="currentColor" strokeWidth="1" fill="none" opacity="0.2"/>
      
      {/* Små detaljer på satellitt */}
      <circle cx="13" cy="15" r="0.5" fill="white" opacity="0.8"/>
      <circle cx="19" cy="17" r="0.5" fill="white" opacity="0.8"/>
      <rect x="15" y="14" width="2" height="1" rx="0.2" fill="white" opacity="0.6"/>
    </svg>
  );
}; 