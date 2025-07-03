import React from 'react';

export default function Home() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 'bold', color: 'white', marginBottom: '16px' }}>
          AI Personal Trainer
        </h1>
        <p style={{ fontSize: '1.125rem', color: 'rgba(255, 255, 255, 0.8)', marginBottom: '32px' }}>
          Your personalized fitness journey starts here
        </p>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '8px' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: 'white', marginBottom: '12px' }}>
            Workout Plans
          </h2>
          <p style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
            Get AI-generated workout plans tailored to your goals and equipment.
          </p>
        </div>
        
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '8px' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: 'white', marginBottom: '12px' }}>
            Progress Tracking
          </h2>
          <p style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
            Track your fitness journey with detailed analytics and insights.
          </p>
        </div>
      </div>
      
      <div className="glass-panel" style={{ padding: '24px', borderRadius: '8px' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: '500', color: 'white', marginBottom: '8px' }}>
          Features
        </h3>
        <ul style={{ color: 'rgba(255, 255, 255, 0.7)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <li>• AI-powered workout generation</li>
          <li>• Hevy integration for seamless tracking</li>
          <li>• Personalized fitness recommendations</li>
          <li>• Progress email summaries</li>
        </ul>
      </div>
    </div>
  );
}
