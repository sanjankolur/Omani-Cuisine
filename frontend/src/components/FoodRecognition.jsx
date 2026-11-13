import { useState } from 'react';
import { recognizeFood } from '../services/api';

const SAMPLE_DISHES = [
  { name: 'Mishkak', file: '/dishes/mishkak.jpg' },
  { name: 'Omani Halwa', file: '/dishes/omani_halwa.jpg' },
  { name: 'Luqaimat', file: '/dishes/luqaimat.jpg' },
  { name: 'Omani Shuwa', file: '/dishes/omani_shuwa.jpg' },
  { name: 'Majboos', file: '/dishes/majboos.jpg' },
];

export default function FoodRecognition() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function handleFileChange(selectedFile) {
    if (!selectedFile) return;
    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
    setResult(null);
    setError('');
  }

  async function testSample(sample) {
    try {
      setLoading(true);
      setError('');
      setResult(null);
      const res = await fetch(sample.file);
      const blob = await res.blob();
      const sampleFile = new File([blob], `${sample.name.toLowerCase().replace(/\s+/g, '_')}.jpg`, { type: 'image/jpeg' });
      setFile(sampleFile);
      setPreviewUrl(sample.file);
      const recognitionResult = await recognizeFood(sampleFile);
      setResult(recognitionResult);
    } catch (err) {
      setError(err.message || 'Sample recognition failed');
    } finally {
      setLoading(false);
    }
  }

  async function submit(event) {
    if (event) event.preventDefault();
    if (!file) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const recognitionResult = await recognizeFood(file);
      setResult(recognitionResult);
    } catch (err) {
      setError(err.message || 'Image recognition failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-orange-800 to-amber-700 p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-700/60 text-orange-100 border border-orange-500/30 mb-2">
              Deep Learning Vision Model
            </span>
            <h2 className="text-xl font-bold tracking-tight">Omani Food Recognition</h2>
            <p className="text-xs text-orange-100/90 mt-1">
              Fine-tuned EfficientNet-B0 trained on verified Omani cuisine datasets
            </p>
          </div>
          <span className="text-3xl">🍲</span>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Sample Try-It-Out Quick Bar */}
        <div>
          <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">
            Try with sample dishes:
          </label>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_DISHES.map((sample) => (
              <button
                key={sample.name}
                type="button"
                onClick={() => testSample(sample)}
                disabled={loading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 hover:bg-orange-50 hover:text-orange-800 text-slate-700 border border-slate-200 transition-colors disabled:opacity-50"
              >
                <span>📷</span> {sample.name}
              </button>
            ))}
          </div>
        </div>

        {/* Upload Zone */}
        <form onSubmit={submit} className="space-y-4">
          <div className="border-2 border-dashed border-slate-200 hover:border-orange-500 rounded-xl p-4 text-center transition-colors">
            {previewUrl ? (
              <div className="space-y-3">
                <img
                  src={previewUrl}
                  alt="Upload preview"
                  className="mx-auto h-48 w-full max-w-xs object-cover rounded-lg shadow-sm border"
                />
                <div className="flex justify-center gap-3">
                  <label className="cursor-pointer text-xs text-orange-700 hover:underline font-medium">
                    Change image
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="hidden"
                      onChange={(e) => handleFileChange(e.target.files?.[0])}
                    />
                  </label>
                </div>
              </div>
            ) : (
              <label className="cursor-pointer block py-6">
                <span className="text-4xl block mb-2">📸</span>
                <span className="text-sm font-medium text-slate-700 block">
                  Click or drag food image here
                </span>
                <span className="text-xs text-slate-400 block mt-1">
                  Supports JPG, PNG, or WEBP (up to 10MB)
                </span>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => handleFileChange(e.target.files?.[0])}
                />
              </label>
            )}
          </div>

          <button
            type="submit"
            disabled={!file || loading}
            className="w-full py-2.5 px-4 rounded-xl bg-orange-800 hover:bg-orange-700 text-white font-medium text-sm transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Classifying dish with Neural Network…
              </>
            ) : (
              '🔍 Recognize Dish'
            )}
          </button>
        </form>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs">
            {error}
          </div>
        )}

        {/* Prediction Results Card */}
        {result && (
          <div className="space-y-4 pt-2 border-t border-slate-100">
            <div className="bg-orange-50/70 border border-orange-200/80 rounded-xl p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-orange-700">
                    Top Detection
                  </span>
                  <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                    {result.dish_name}
                  </h3>
                  {result.matched_dish?.name_ar && (
                    <span className="text-base text-slate-500 font-arabic">
                      {result.matched_dish.name_ar}
                    </span>
                  )}
                </div>
                <div className="text-right">
                  <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-bold ${
                    result.confidence === 'high'
                      ? 'bg-orange-100 text-orange-800'
                      : result.confidence === 'medium'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-slate-100 text-slate-700'
                  }`}>
                    {result.confidence_percentage ? `${result.confidence_percentage}% Match` : result.confidence}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-700 mt-2.5 leading-relaxed">
                {result.description}
              </p>

              {result.likely_ingredients && result.likely_ingredients.length > 0 && (
                <div className="mt-3">
                  <span className="text-xs font-semibold text-slate-700 block mb-1.5">
                    Key Ingredients:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {result.likely_ingredients.map((ing, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-white text-slate-700 rounded text-xs border border-orange-200/60 shadow-2xs"
                      >
                        {ing}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {result.matched_dish && (
                <div className="mt-3 pt-3 border-t border-orange-200/60 text-xs text-slate-600 flex items-center justify-between">
                  <span>Category: <b>{result.matched_dish.category || 'Traditional'}</b></span>
                  <span>Region: <b>{result.matched_dish.region || 'Oman'}</b></span>
                </div>
              )}
            </div>

            {/* Top 3 Model Predictions */}
            {result.top3_predictions && result.top3_predictions.length > 1 && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                <span className="text-xs font-semibold text-slate-600 block mb-2 uppercase tracking-wider">
                  Model Probability Distribution (Top-3):
                </span>
                <div className="space-y-2">
                  {result.top3_predictions.map((pred) => (
                    <div key={pred.key} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="font-medium text-slate-700">{pred.dish_name}</span>
                        <span className="font-bold text-slate-600">{pred.probability}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-orange-600 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, Math.max(2, pred.probability))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="text-2xs text-slate-400 text-center">
              {result.notes}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
