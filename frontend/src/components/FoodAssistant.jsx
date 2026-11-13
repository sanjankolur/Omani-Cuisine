import { useState } from 'react';
import { askFoodAssistant } from '../services/api';

const QUICK_PROMPTS = [
  'What is the most iconic Omani dish?',
  'Suggest a festive meal for guests.',
  'What ingredients are in Majboos?',
  'What is the difference between Shuwa and Harees?',
  'What should I serve with Luqaimat?',
];

export default function FoodAssistant() {
  const [message, setMessage] = useState('');
  const [answer, setAnswer] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    const text = message.trim();
    if (!text) return;
    setLoading(true);
    setError('');
    setAnswer('');
    try {
      const data = await askFoodAssistant(text);
      setAnswer(data.answer);
    } catch (err) {
      setError(err.message || 'The assistant could not answer right now.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-[28px] border border-orange-200 bg-white p-5 shadow-sm md:p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-orange-700">Chef’s guide</p>
          <h2 className="mt-2 text-2xl font-black text-slate-900">Ask about Omani cuisine</h2>
        </div>
        <span className="text-3xl">🍽️</span>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {QUICK_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => setMessage(prompt)}
            className="rounded-full border border-orange-200 bg-orange-50 px-3 py-1.5 text-xs font-medium text-orange-800 transition hover:border-orange-300 hover:bg-orange-100"
          >
            {prompt}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="mt-5 flex flex-col gap-3 sm:flex-row">
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask about a dish, ingredient, or Omani food tradition…"
          className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
        />
        <button
          type="submit"
          disabled={loading || !message.trim()}
          className="rounded-2xl bg-orange-600 px-5 py-3 text-sm font-bold text-white transition hover:bg-orange-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Thinking…' : 'Ask AI'}
        </button>
      </form>

      {error && <p className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      {answer && (
        <div className="mt-5 rounded-2xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-800">Answer</p>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{answer}</p>
        </div>
      )}
    </section>
  );
}
