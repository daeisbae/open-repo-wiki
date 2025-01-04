'use client'
import Form from 'next/form';
import React, { useState } from 'react';
import { addRepository } from '@/app/add/repositories/addrepository';

export default function Page() {
  const [response, setResponse] = useState(undefined);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const owner: string = formData.get('owner') as string;
    const repo: string = formData.get('repo') as string;
    const result = await addRepository(owner, repo);
    setResponse(result);
  };

  return (
    <div className="flex flex-col items-center justify-center w-full h-full overflow-y-hidden">
      <h1 className="font-bold text-lg sm:text-2xl md:text-3xl pb-4">Add Repository</h1>
      <Form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-md p-6 border rounded-lg shadow-sm">
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
      </Form>
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