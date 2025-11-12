import React from 'react';

function TestPage() {
  return (
    <div style={{ padding: '2rem' }}>
      <h1>Test Page</h1>
      <p>This is a simple test page to verify the frontend is working.</p>
      <div style={{ marginTop: '2rem' }}>
        <h2>Available Test Links:</h2>
        <ul>
          <li><a href="/admin/patentpulse">PatentPulse Dashboard (Partner Shares)</a></li>
          <li><a href="/share/test-token">Partner Share Page (Test Token)</a></li>
        </ul>
      </div>
    </div>
  );
}

export default TestPage;