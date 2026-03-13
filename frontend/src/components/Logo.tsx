import React from 'react';
import './Logo.css';

interface LogoProps {
  width?: number | string;
  height?: number | string;
  className?: string;
  showText?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ 
  width = 40, 
  height = 'auto', 
  className = '',
  showText = false 
}) => {
  return (
    <div className={`og-logo-container ${className}`}>
      <img 
        src="/og-logo.png" 
        alt="Open Grace Logo" 
        style={{ width, height }} 
        className="og-logo-img"
      />
      {showText && <span className="og-logo-text">Open Grace</span>}
    </div>
  );
};
