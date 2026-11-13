import { useState, useEffect } from 'react';
import FoodAssistant from './components/FoodAssistant';
import FoodRecognition from './components/FoodRecognition';
import { getDishes, getDish, getNutrition, getAnalytics, getRecommendations, apiRequest } from './services/api';

const DISH_IMAGE_MAP = {
  'omani shuwa': '/dishes/omani_shuwa.jpg',
  shuwa: '/dishes/omani_shuwa.jpg',
  majboos: '/dishes/majboos.jpg',
  harees: '/dishes/harees.jpg',
  'omani halwa': '/dishes/omani_halwa.jpg',
  halwa: '/dishes/omani_halwa.jpg',
  mashuai: '/dishes/mashuai.jpg',
  mishkak: '/dishes/mishkak.jpg',
  madrouba: '/dishes/madrouba.jpg',
  'khubz ragag': '/dishes/khubz_ragag.jpg',
  luqaimat: '/dishes/luqaimat.jpg',
  'omani luqaimat': '/dishes/luqaimat.jpg',
  marqooq: '/dishes/marqooq.jpg',
  'omani marqooq': '/dishes/marqooq.jpg',
};

const FEATURED_DISHES = [
  { name: 'Omani Shuwa', accent: 'Slow-cooked feast', emoji: '🔥' },
  { name: 'Majboos', accent: 'Rice & spice tradition', emoji: '🍛' },
  { name: 'Luqaimat', accent: 'Sweet celebration bite', emoji: '🍯' },
  { name: 'Mishkak', accent: 'Charcoal grilled favorite', emoji: '🍢' },
];

const RECOMMENDATION_TAGS = ['vegetarian', 'high protein', 'sweet', 'festive', 'seafood', 'comfort food'];
const REGION_OPTIONS = ['All regions', 'Musandam', 'Batinah', 'Dhofar', 'Muscat', 'Al Sharqiya', 'Interior'];

export default function App() {
  const [activeTab, setActiveTab] = useState('catalogue');
  const [dishes, setDishes] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [regionFilter, setRegionFilter] = useState('All regions');
  const [selectedDish, setSelectedDish] = useState(null);
  const [dishNutrition, setDishNutrition] = useState(null);
  const [healthStatus, setHealthStatus] = useState('checking');
  const [analyticsData, setAnalyticsData] = useState(null);
  const [recGoal, setRecGoal] = useState('');
  const [recAvoid, setRecAvoid] = useState('');
  const [recPreferences, setRecPreferences] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [recLoading, setRecLoading] = useState(false);
  const [recMsg, setRecMsg] = useState('');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authMsg, setAuthMsg] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  const tabItems = [
    { id: 'catalogue', label: 'Dish Catalogue', icon: '🍲' },
    { id: 'recognition', label: 'AI Recognition', icon: '📸' },
    { id: 'recommendations', label: 'Recommendations', icon: '✨' },
    { id: 'analytics', label: 'Analytics', icon: '📊' },
    { id: 'auth', label: 'Profile', icon: '👤' },
    { id: 'assistant', label: 'AI Assistant', icon: '🤖' },
  ];

  useEffect(() => {
    fetch('http://localhost:8001/health')
      .then((res) => res.json())
      .then((data) => setHealthStatus(data.status === 'ok' ? 'online' : 'error'))
      .catch(() => setHealthStatus('offline'));

    loadDishes('');
  }, []);

  useEffect(() => {
    if (activeTab === 'analytics') {
      loadAnalytics();
    }
  }, [activeTab]);

  const loadDishes = async (q = '', region = regionFilter) => {
    try {
      const data = await getDishes(q, region === 'All regions' ? '' : region);
      setDishes(data.items || []);
    } catch {
      setDishes([]);
    }
  };

  const loadAnalytics = async () => {
    try {
      const data = await getAnalytics();
      setAnalyticsData(data);
    } catch (e) {
      console.error(e);
    }
  };

  const viewDishDetails = async (dish) => {
    setSelectedDish(dish);
    setDishNutrition(null);
    try {
      const fullDish = await getDish(dish.id);
      setSelectedDish(fullDish);
      const nut = await getNutrition(dish.id);
      setDishNutrition(nut);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRecommendations = async (e) => {
    e.preventDefault();
    setRecLoading(true);
    setRecMsg('');
    try {
      const avoidList = recAvoid.split(',').map((s) => s.trim()).filter(Boolean);
      const res = await getRecommendations({
        dietary_preferences: recPreferences,
        avoid_ingredients: avoidList,
        goal: recGoal,
        limit: 6,
      });
      setRecommendations(res.items || []);
      if (res.items?.length === 0) {
        setRecMsg('No dishes matched your specific criteria. Try relaxing your filters.');
      }
    } catch (err) {
      setRecMsg(err.message || 'Failed to fetch recommendations');
    } finally {
      setRecLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthMsg('');
    setAuthMsg('Login is disabled. The app now works without a token system.');
    setAuthLoading(false);
  };

  const togglePreference = (tag) => {
    setRecPreferences((current) =>
      current.includes(tag)
        ? current.filter((item) => item !== tag)
        : [...current, tag],
    );
  };

  const displayDishes = dishes.slice(0, 9);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      <header className="sticky top-0 z-30 border-b border-orange-100 bg-white/75 backdrop-blur-xl shadow-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-700 to-amber-500 text-2xl shadow-md">🇴🇲</div>
            <div>
              <h1 className="text-xl font-black tracking-tight text-orange-950">
                Oman Food Intelligence
              </h1>
              <p className="text-[11px] text-slate-500">Heritage • Nutrition • AI</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-3 text-sm">
            <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700">
              <span className={`inline-block h-2.5 w-2.5 rounded-full ${healthStatus === 'online' ? 'bg-orange-500' : healthStatus === 'checking' ? 'bg-amber-400 animate-pulse' : 'bg-red-500'}`} />
              <span>Backend {healthStatus}</span>
            </div>

            <button onClick={() => setActiveTab('auth')} className="rounded-full bg-orange-800 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-orange-900">
              Open guide
            </button>
          </div>
        </div>

        <nav className="mx-auto max-w-6xl overflow-x-auto px-4 pb-2">
          <div className="flex min-w-max gap-2">
            {tabItems.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 rounded-t-xl border-b-2 px-4 py-3 text-sm font-medium transition ${
                  activeTab === tab.id
                    ? 'border-orange-700 bg-orange-50 text-orange-900'
                    : 'border-transparent text-slate-600 hover:border-slate-200 hover:text-orange-800'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </nav>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-8">
        {activeTab === 'catalogue' && (
          <div className="space-y-6">
            <section className="overflow-hidden rounded-[28px] bg-gradient-to-br from-orange-900 via-orange-800 to-amber-700 p-6 text-white shadow-xl shadow-orange-900/20">
              <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
                <div className="max-w-2xl">
                  <span className="inline-flex rounded-full border border-orange-300/40 bg-white/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-orange-100">
                    Omani culinary atlas
                  </span>
                  <h2 className="mt-4 text-3xl font-black leading-tight md:text-4xl">Discover the flavors of Oman's table.</h2>
                  <p className="mt-3 max-w-xl text-sm text-orange-50/80">
                    Explore signature dishes, regional specialties, traditional preparation rituals, and nutrition-rich favorites from across the Sultanate.
                  </p>
                </div>

                <div className="w-full max-w-md rounded-2xl border border-white/15 bg-white/5 p-3 backdrop-blur-sm">
                  <label className="mb-2 block text-[10px] font-semibold uppercase tracking-[0.2em] text-orange-100/80">
                    Quick search
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && loadDishes(searchQuery, regionFilter)}
                      placeholder="Search dishes, ingredients or cuisines..."
                      className="w-full rounded-xl border border-orange-300/30 bg-white/10 px-3 py-2.5 text-sm text-white placeholder:text-orange-100/60 outline-none ring-0 focus:border-orange-200"
                    />
                    <button
                      onClick={() => loadDishes(searchQuery, regionFilter)}
                      className="rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-orange-900 transition hover:bg-orange-50"
                    >
                      Search
                    </button>
                  </div>
                </div>
              </div>
            </section>

            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {[
                { label: 'Dish records', value: dishes.length || '10+', tone: 'orange' },
                { label: 'Regional specialties', value: '6', tone: 'amber' },
                { label: 'AI recognition', value: '10 classes', tone: 'sky' },
                { label: 'Heritage stories', value: '100%', tone: 'rose' },
              ].map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className={`mb-3 inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.2em] ${
                    stat.tone === 'orange' ? 'bg-orange-100 text-orange-800' :
                    stat.tone === 'amber' ? 'bg-amber-100 text-amber-800' :
                    stat.tone === 'sky' ? 'bg-sky-100 text-sky-800' : 'bg-rose-100 text-rose-800'
                  }`}>
                    {stat.label}
                  </div>
                  <p className="text-2xl font-black text-slate-900">{stat.value}</p>
                </div>
              ))}
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Curated highlights</h3>
                  <p className="text-xs text-slate-500">Most beloved Omani dishes to start exploring</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {REGION_OPTIONS.map((option) => (
                    <button
                      key={option}
                      onClick={() => {
                        setRegionFilter(option);
                        loadDishes(searchQuery, option);
                      }}
                      className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                        regionFilter === option
                          ? 'bg-orange-800 text-white shadow-sm'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                {FEATURED_DISHES.map((dish) => (
                  <button
                    key={dish.name}
                    onClick={() => {
                      const term = dish.name.split(' ')[1] || dish.name;
                      setSearchQuery(term);
                      loadDishes(term, regionFilter);
                    }}
                    className="group rounded-2xl border border-slate-200 bg-gradient-to-br from-amber-50 to-orange-50 p-4 text-left transition hover:-translate-y-0.5 hover:border-orange-300 hover:shadow-md"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-2xl">{dish.emoji}</span>
                      <span className="rounded-full bg-white/80 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-orange-800">Featured</span>
                    </div>
                    <h4 className="text-base font-bold text-slate-900">{dish.name}</h4>
                    <p className="mt-1 text-xs text-slate-600">{dish.accent}</p>
                  </button>
                ))}
              </div>
            </section>

            {displayDishes.length === 0 ? (
              <div className="rounded-2xl bg-white p-10 text-center shadow-sm ring-1 ring-slate-200">
                <p className="text-lg font-bold text-slate-900">No dishes found</p>
                <button onClick={() => { setSearchQuery(''); setRegionFilter('All regions'); loadDishes('', 'All regions'); }} className="mt-3 text-sm font-semibold text-orange-700 underline">
                  Reset filters
                </button>
              </div>
            ) : (
              <section className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {displayDishes.map((dish) => {
                  const imgUrl = DISH_IMAGE_MAP[dish.name.toLowerCase()];
                  return (
                    <article key={dish.id} className="group overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-xl">
                      {imgUrl ? (
                        <div className="relative h-48 overflow-hidden bg-slate-100">
                          <img src={imgUrl} alt={dish.name} className="h-full w-full object-cover transition duration-500 group-hover:scale-105" />
                          <span className="absolute right-3 top-3 rounded-full bg-black/55 px-2.5 py-1 text-[10px] font-semibold text-white backdrop-blur-sm">
                            {dish.category || 'Traditional'}
                          </span>
                        </div>
                      ) : (
                        <div className="flex h-48 items-center justify-center bg-gradient-to-br from-orange-50 to-amber-50 text-4xl">🍽️</div>
                      )}

                      <div className="space-y-3 p-5">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h4 className="text-xl font-black text-slate-900">{dish.name}</h4>
                            {dish.name_ar && <p className="text-sm font-medium text-orange-800">{dish.name_ar}</p>}
                          </div>
                          <span className="rounded-full bg-orange-50 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.15em] text-orange-700">
                            {dish.region || 'Across Oman'}
                          </span>
                        </div>

                        <p className="text-sm leading-relaxed text-slate-600 line-clamp-3">{dish.description}</p>

                        {dish.ingredients_summary && (
                          <p className="border-t border-slate-100 pt-3 text-xs text-slate-500">
                            <span className="font-bold text-slate-700">Key ingredients:</span> {dish.ingredients_summary}
                          </p>
                        )}

                        <button
                          onClick={() => viewDishDetails(dish)}
                          className="mt-2 w-full rounded-xl bg-gradient-to-r from-orange-700 to-orange-800 px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:from-orange-800 hover:to-orange-900"
                        >
                          View full details
                        </button>
                      </div>
                    </article>
                  );
                })}
              </section>
            )}

            {selectedDish && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
                <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[26px] bg-white p-6 shadow-2xl">
                  <div className="mb-4 flex items-start justify-between gap-4 border-b border-slate-200 pb-4">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-orange-700">Dish profile</p>
                      <h3 className="mt-2 text-3xl font-black text-slate-900">{selectedDish.name}</h3>
                      {selectedDish.name_ar && <p className="text-lg font-medium text-slate-500">{selectedDish.name_ar}</p>}
                    </div>
                    <button onClick={() => setSelectedDish(null)} className="rounded-full bg-slate-100 px-3 py-1.5 text-xl text-slate-500 transition hover:bg-slate-200 hover:text-slate-800">
                      ×
                    </button>
                  </div>

                  <div className="space-y-4 text-sm text-slate-700">
                    <div>
                      <h5 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Description</h5>
                      <p className="mt-2 leading-relaxed">{selectedDish.description}</p>
                    </div>

                    {selectedDish.cooking_method && (
                      <div>
                        <h5 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Preparation</h5>
                        <p className="mt-2 leading-relaxed">{selectedDish.cooking_method}</p>
                      </div>
                    )}

                    {selectedDish.cultural_notes && (
                      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900">
                        <h5 className="text-[10px] font-bold uppercase tracking-[0.2em]">Cultural significance</h5>
                        <p className="mt-2 text-sm leading-relaxed">{selectedDish.cultural_notes}</p>
                      </div>
                    )}

                    {dishNutrition && (
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <div className="mb-3 flex items-center justify-between">
                          <h5 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Nutrition estimate</h5>
                          <span className="text-[11px] italic text-slate-500">({dishNutrition.serving_description || 'per serving'})</span>
                        </div>
                        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                          <div className="rounded-xl bg-white p-3 text-center shadow-sm ring-1 ring-slate-200">
                            <p className="text-[10px] text-slate-500">Calories</p>
                            <p className="mt-1 text-lg font-black text-orange-900">{dishNutrition.calories_kcal || 0}</p>
                          </div>
                          <div className="rounded-xl bg-white p-3 text-center shadow-sm ring-1 ring-slate-200">
                            <p className="text-[10px] text-slate-500">Protein</p>
                            <p className="mt-1 text-lg font-black text-orange-900">{dishNutrition.protein_g || 0}g</p>
                          </div>
                          <div className="rounded-xl bg-white p-3 text-center shadow-sm ring-1 ring-slate-200">
                            <p className="text-[10px] text-slate-500">Carbs</p>
                            <p className="mt-1 text-lg font-black text-orange-900">{dishNutrition.carbohydrates_g || 0}g</p>
                          </div>
                          <div className="rounded-xl bg-white p-3 text-center shadow-sm ring-1 ring-slate-200">
                            <p className="text-[10px] text-slate-500">Fat</p>
                            <p className="mt-1 text-lg font-black text-orange-900">{dishNutrition.fat_g || 0}g</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <button onClick={() => setSelectedDish(null)} className="mt-6 w-full rounded-xl bg-slate-100 px-4 py-2.5 text-sm font-bold text-slate-800 transition hover:bg-slate-200">
                    Close details
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="mx-auto max-w-4xl space-y-6">
            <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-2xl font-black text-slate-900">Smart Omani meal planner</h2>
              <p className="mt-2 text-sm text-slate-500">Find dishes that match your goals, dietary restrictions, and cravings.</p>

              <form onSubmit={handleRecommendations} className="mt-6 space-y-4">
                <div>
                  <label className="mb-2 block text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Dietary goal</label>
                  <input
                    value={recGoal}
                    onChange={(e) => setRecGoal(e.target.value)}
                    placeholder="e.g. festive, high-protein, comforting, vegetarian..."
                    className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none transition focus:border-orange-500 focus:ring-2 focus:ring-orange-100"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Preferred flavors</label>
                  <div className="flex flex-wrap gap-2">
                    {RECOMMENDATION_TAGS.map((tag) => {
                      const active = recPreferences.includes(tag);
                      return (
                        <button
                          key={tag}
                          type="button"
                          onClick={() => togglePreference(tag)}
                          className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                            active
                              ? 'bg-orange-800 text-white shadow-sm'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                          }`}
                        >
                          {tag}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <label className="mb-2 block text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Avoid ingredients</label>
                  <input
                    value={recAvoid}
                    onChange={(e) => setRecAvoid(e.target.value)}
                    placeholder="e.g. lamb, nuts, fish, garlic"
                    className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none transition focus:border-orange-500 focus:ring-2 focus:ring-orange-100"
                  />
                </div>

                <button type="submit" disabled={recLoading} className="w-full rounded-xl bg-orange-800 px-4 py-3 text-sm font-bold text-white transition hover:bg-orange-900 disabled:cursor-not-allowed disabled:opacity-60">
                  {recLoading ? 'Calculating matches...' : 'Find recommended dishes'}
                </button>

                {recMsg && <p className="rounded-xl bg-amber-50 p-3 text-xs text-amber-800">{recMsg}</p>}
              </form>
            </div>

            {recommendations.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-xl font-black text-slate-900">Recommended for you</h3>
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  {recommendations.map((dish) => (
                    <div key={dish.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                      <h4 className="text-lg font-bold text-slate-900">{dish.name}</h4>
                      <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.15em] text-orange-700">{dish.category} • {dish.region}</p>
                      <p className="mt-3 text-sm text-slate-600 line-clamp-3">{dish.description}</p>
                      <button onClick={() => viewDishDetails(dish)} className="mt-4 text-sm font-bold text-orange-700 hover:underline">
                        View details →
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="mx-auto max-w-5xl space-y-6">
            <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-2xl font-black text-slate-900">Regional and catalogue analytics</h2>
              <p className="mt-2 text-sm text-slate-500">Overview of Omani cuisine records stored in the live data layer.</p>

              {analyticsData ? (
                <div className="mt-6 space-y-6">
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="rounded-2xl border border-orange-200 bg-orange-50 p-4">
                      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-orange-800">Total dishes</p>
                      <p className="mt-2 text-3xl font-black text-orange-950">{analyticsData.total_dishes}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-600">Categories</p>
                      <p className="mt-2 text-3xl font-black text-slate-900">{Object.keys(analyticsData.categories || {}).length}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-600">Regions</p>
                      <p className="mt-2 text-3xl font-black text-slate-900">{Object.keys(analyticsData.regions || {}).length}</p>
                    </div>
                  </div>

                  <div className="grid gap-4 lg:grid-cols-2">
                    <div className="rounded-2xl border border-slate-200 p-4">
                      <h3 className="mb-3 text-sm font-bold uppercase tracking-[0.2em] text-slate-500">Dishes by category</h3>
                      <ul className="space-y-2 text-sm">
                        {Object.entries(analyticsData.categories || {}).map(([cat, count]) => (
                          <li key={cat} className="flex items-center justify-between border-b border-slate-100 pb-2">
                            <span>{cat}</span>
                            <span className="rounded-full bg-slate-100 px-2 py-0.5 font-bold text-slate-700">{count}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="rounded-2xl border border-slate-200 p-4">
                      <h3 className="mb-3 text-sm font-bold uppercase tracking-[0.2em] text-slate-500">Dishes by region</h3>
                      <ul className="space-y-2 text-sm">
                        {Object.entries(analyticsData.regions || {}).map(([reg, count]) => (
                          <li key={reg} className="flex items-center justify-between border-b border-slate-100 pb-2">
                            <span>{reg}</span>
                            <span className="rounded-full bg-slate-100 px-2 py-0.5 font-bold text-slate-700">{count}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-400">Loading analytics...</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'auth' && (
          <div className="mx-auto max-w-xl space-y-6">
            <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-2xl font-black text-slate-900">Guide</h3>
              <p className="mt-2 text-sm text-slate-500">Token login is turned off for this demo. All features work without sign-in so the experience stays smooth and simple.</p>

              <div className="mt-6 space-y-4 rounded-2xl border border-orange-200 bg-orange-50 p-4 text-sm text-orange-900">
                <p><strong>Available now:</strong> browsing, AI recognition, recommendations, analytics, and assistant chat.</p>
                <p><strong>No login required:</strong> the app is designed for instant use and easier testing.</p>
              </div>

              {authMsg && <p className="mt-4 text-sm text-slate-700">{authMsg}</p>}
            </div>
          </div>
        )}

        {activeTab === 'recognition' && (
          <div className="mx-auto w-full max-w-3xl">
            <FoodRecognition />
          </div>
        )}

        {activeTab === 'assistant' && (
          <div className="mx-auto w-full max-w-4xl space-y-5">
            <div className="rounded-[28px] border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-4 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-800">Knowledge enabled</p>
                  <p className="mt-2 text-sm text-amber-900">Ask about ingredients, preparation, cultural context, and food pairing ideas.</p>
                </div>
                <span className="text-3xl">🧠</span>
              </div>
            </div>
            <FoodAssistant />
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl flex-col justify-between gap-2 px-4 py-4 text-xs text-slate-500 md:flex-row md:items-center">
          <span>🇴🇲 Oman Food AI — Traditional cuisine intelligence platform</span>
          <a href="http://localhost:8001/docs" target="_blank" rel="noreferrer" className="font-semibold text-orange-700 underline">
            Open API docs
          </a>
        </div>
      </footer>
    </div>
  );
}
