import React, { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div style={{ minHeight: '100vh', padding: '32px' }}>
      <div style={{ maxWidth: '1024px', margin: '0 auto' }}>
        <div className="glass-card" style={{ padding: '48px', minHeight: '80vh' }}>
          {children}
        </div>
      </div>
    </div>
  );
}
