'use client';
import React, { useState } from 'react';

export default function Page() {
    const [response, setResponse] = useState(null);
  
    async function handleSubmit(event) {
      event.preventDefault();
      const formData = new FormData(event.target);
      const data = {
        owner: formData.get('owner'),
        repo: formData.get('repo'),
      };
  
      try {
        const res = await fetch('/api/repository', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });
  
        const result = await res.json();
        setResponse(result);
      } catch (error) {
        console.error(error);
        setResponse({ success: false, error: 'An error occurred while adding the repository.' });
      }
    }
  

  return (
    <div className="flex flex-col items-center justify-center w-full h-full overflow-y-hidden">
      <h1 className="font-bold text-lg sm:text-2xl md:text-3xl pb-4">Add Repository</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-md p-6 border rounded-lg shadow-sm">
        <div className="flex flex-col gap-4">
          <input
            className="p-4 border rounded-md text-center"
            type="text"
            name="owner"
            placeholder="GitHub Owner"
            required
          />
          <input
            className="p-4 border rounded-md text-center"
            type="text"
            name="repo"
            placeholder="Repository Name"
            required
          />
        </div>
        <button
          type="submit"
          className="bg-black hover:bg-slate-900 text-white font-bold py-4 px-6 rounded-md transition-colors"
        >
          Add Repository
        </button>
      </form>
      {response && (
        <div
          className={`p-4 my-4 text-sm rounded-lg ${
            response.success ? 'text-green-800 bg-green-50' : 'text-red-800 bg-red-50'
          }`}
          role="alert"
        >
          <span className="font-medium">{response.success ? 'Success:' : 'Error:'} </span>
          {response.message || response.error}
        </div>
      )}
    </div>
  );
}