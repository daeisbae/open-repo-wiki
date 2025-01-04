'use client';
import React, { useState, JSX } from 'react';

interface CollapsibleHeaderProps {
    heading: number;
    children: React.ReactNode;
    level: number;
    open?: boolean;
}

export default function CollapsibleHeader({ heading, children, level, open = false } : CollapsibleHeaderProps): JSX.Element {
  const [isOpen, setIsOpen] = useState(open);

  const toggle = () => setIsOpen(!isOpen);

  const HeadingTag = `h${level}`;

  return (
    <div>
      <HeadingTag
        onClick={toggle}
        className='cursor-pointer flex items-center'
      >
        <span className={`ml-0 md:ml-1 text-sm ${isOpen ? 'rotate-90' : 'rotate-0'} transition-transform ${level < 6 ? 'mr-3' : 'mr-1'}`}>
        <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="2"
                        stroke="currentColor"
                        className="w-3 h-3"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M9 5l7 7-7 7"
                        />
                    </svg>
        </span>
        {heading}
      </HeadingTag>
      {isOpen && <div className={`${heading < 6 ? 'ml-0 md:ml-2' : 'ml-5'}`}>{children}</div>}
    </div>
  );
}