import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { Loader2, TrendingUp, Target, CalendarDays, BrainCircuit, AlertTriangle, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const COLORS = ['#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b'];

const Analytics = () => {
  const [overview, setOverview] = useState(null);
  const [compareData, setCompareData] = useState([]);
  const [retentionData, setRetentionData] = useState([]);
  const [stabilityData, setStabilityData] = useState([]);
  const [responseTimeData, setResponseTimeData] = useState([]);
  const [activityData, setActivityData] = useState([]);
  const [distributionData, setDistributionData] = useState([]);
  const [weakConcepts, setWeakConcepts] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [ovRes, compRes, retRes, stabRes, respRes, actRes, distRes, weakRes] = await Promise.all([
          api.get('/analytics/overview'),
          api.get('/analytics/compare'),
          api.get('/analytics/retention'),
          api.get('/analytics/stability'),
          api.get('/analytics/response-time'),
          api.get('/analytics/activity'),
          api.get('/analytics/distribution'),
          api.get('/analytics/weak-concepts')
        ]);
        
        setOverview(ovRes.data);
        
        // Format compare data for Recharts
        const formattedCompare = compRes.data.map(item => ({
          name: item.algorithm.toUpperCase(),
          Accuracy: item.accuracy,
          'Interval (Days)': item.avg_interval_days,
          'Stability': item.avg_stability || 0,
          rmse: item.rmse,
          log_loss: item.log_loss
        }));
        setCompareData(formattedCompare);
        
        setRetentionData(retRes.data);
        setStabilityData(stabRes.data);
        setResponseTimeData(respRes.data);
        setActivityData(actRes.data);
        setDistributionData(distRes.data);
        setWeakConcepts(weakRes.data);
      } catch (err) {
        console.error("Failed to load analytics", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-purple-400" size={48} /></div>;
  }

  return (
    <div className="p-8 max-w-6xl w-full">
      <h1 className="text-4xl font-bold mb-2">Performance Analytics</h1>
      <p className="text-slate-400 mb-8">Compare scheduling algorithm efficiency and track your cognitive retention.</p>
      
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <div className="glass p-6 rounded-2xl flex items-start gap-4">
          <div className="p-3 bg-purple-500/20 rounded-xl text-purple-400"><BrainCircuit size={24} /></div>
          <div>
            <p className="text-sm font-medium text-slate-400">Total Concepts</p>
            <p className="text-3xl font-bold text-white mt-1">{overview?.total_concepts}</p>
          </div>
        </div>
        <div className="glass p-6 rounded-2xl flex items-start gap-4">
          <div className="p-3 bg-blue-500/20 rounded-xl text-blue-400"><Target size={24} /></div>
          <div>
            <p className="text-sm font-medium text-slate-400">Total Reviews</p>
            <p className="text-3xl font-bold text-white mt-1">{overview?.total_reviews}</p>
          </div>
        </div>
        <div className="glass p-6 rounded-2xl flex items-start gap-4">
          <div className="p-3 bg-green-500/20 rounded-xl text-green-400"><TrendingUp size={24} /></div>
          <div>
            <p className="text-sm font-medium text-slate-400">Accuracy</p>
            <p className="text-3xl font-bold text-white mt-1">{overview?.overall_accuracy}%</p>
          </div>
        </div>
        <div className="glass p-6 rounded-2xl flex items-start gap-4">
          <div className="p-3 bg-pink-500/20 rounded-xl text-pink-400"><CalendarDays size={24} /></div>
          <div>
            <p className="text-sm font-medium text-slate-400">Due Today</p>
            <p className="text-3xl font-bold text-white mt-1">{overview?.due_today}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Comparison Chart */}
        <div className="glass p-8 rounded-3xl border border-white/10 shadow-2xl">
          <h2 className="text-2xl font-bold mb-6">Algorithm Efficiency</h2>
          {compareData.length === 0 ? (
            <p className="text-slate-500 text-center py-12">Not enough review data to compare algorithms yet.</p>
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={compareData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
                  <XAxis dataKey="name" stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="left" orientation="left" stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#ffffff2a', borderRadius: '16px' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }}/>
                  <Bar yAxisId="left" dataKey="Accuracy" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  <Bar yAxisId="right" dataKey="Interval (Days)" fill="#ec4899" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          
          {/* Predictive Performance Metrics Table */}
          {compareData.length > 0 && compareData.some(d => d.rmse !== null) && (
            <div className="mt-8 border-t border-white/10 pt-6">
              <h3 className="text-lg font-semibold text-white mb-4">Predictive Accuracy (Log-Loss & RMSE)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-white/10 text-slate-400 text-sm">
                      <th className="pb-2 font-medium">Algorithm</th>
                      <th className="pb-2 font-medium">RMSE ↓</th>
                      <th className="pb-2 font-medium">Log-Loss ↓</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compareData.map((d) => (
                      <tr key={d.name} className="border-b border-white/5 last:border-0">
                        <td className="py-3 font-mono text-slate-200">{d.name}</td>
                        <td className="py-3 text-slate-300">
                          {d.rmse !== null ? d.rmse.toFixed(4) : '-'}
                        </td>
                        <td className="py-3 text-slate-300">
                          {d.log_loss !== null ? d.log_loss.toFixed(4) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-slate-400 mt-3">
                * Lower values indicate the algorithm's predictions closer match reality (true memory retention).
              </p>
            </div>
          )}
        </div>

        {/* Algorithm Distribution */}
        <div className="glass p-8 rounded-3xl border border-white/10 shadow-2xl">
          <h2 className="text-2xl font-bold mb-6">Knowledge Base Distribution</h2>
          {distributionData.length === 0 ? (
            <p className="text-slate-500 text-center py-12">No concepts in your knowledge base yet.</p>
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={distributionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={80}
                    outerRadius={110}
                    paddingAngle={5}
                    dataKey="count"
                    nameKey="algorithm"
                  >
                    {distributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#ffffff2a', borderRadius: '16px' }}
                    itemStyle={{ color: '#fff' }}
                    formatter={(value, name) => [value, name.toUpperCase()]}
                  />
                  <Legend formatter={(value) => value.toUpperCase()} wrapperStyle={{ paddingTop: '20px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="text-center text-sm text-slate-400 mt-4">Algorithms actively managing your concepts.</p>
        </div>

        {/* Retention / Forgetting Curve */}
        <div className="glass p-8 rounded-3xl border border-white/10 shadow-2xl">
          <h2 className="text-2xl font-bold mb-6">Forgetting Curve</h2>
          {retentionData.length === 0 ? (
            <p className="text-slate-500 text-center py-12">Complete multiple reviews on a concept to track retention decay.</p>
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={retentionData.slice(0, 50)} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
                  <XAxis dataKey="day" stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} label={{ value: 'Review Attempt (Nth Time)', position: 'insideBottom', offset: -10, fill: '#94a3b8' }} />
                  <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} domain={[0, 1.2]} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#ffffff2a', borderRadius: '16px' }}
                    labelFormatter={() => ''}
                  />
                  <Line type="monotone" dataKey="retrievability" stroke="#3b82f6" strokeWidth={4} dot={{ fill: '#3b82f6', r: 4 }} activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="text-center text-sm text-slate-400 mt-4">Predicted baseline memory retention across successive reviews.</p>
        </div>

        {/* Cognitive Fluency (Response Time) */}
        <div className="glass p-8 rounded-3xl border border-white/10 shadow-2xl">
          <h2 className="text-2xl font-bold mb-6">Cognitive Fluency</h2>
          {responseTimeData.length === 0 ? (
            <p className="text-slate-500 text-center py-12">No response time data available yet.</p>
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={responseTimeData.slice(0, 50)} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
                  <XAxis dataKey="review_number" stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} label={{ value: 'Review Attempt', position: 'insideBottom', offset: -10, fill: '#94a3b8' }} />
                  <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} label={{ value: 'Seconds', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#ffffff2a', borderRadius: '16px' }}
                    labelFormatter={(val) => `Review #${val}`}
                  />
                  <Line type="monotone" dataKey="avg_response_time_sec" stroke="#f59e0b" strokeWidth={4} dot={{ fill: '#f59e0b', r: 4 }} activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="text-center text-sm text-slate-400 mt-4">Average response time (speed of recall) over time.</p>
        </div>

        {/* Daily Activity */}
        <div className="glass p-8 rounded-3xl border border-white/10 shadow-2xl lg:col-span-2">
          <h2 className="text-2xl font-bold mb-6">Daily Review Volume (Last 14 Days)</h2>
          {activityData.length === 0 ? (
            <p className="text-slate-500 text-center py-12">No recent review activity.</p>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={activityData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
                  <XAxis dataKey="date" stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                  <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#ffffff2a', borderRadius: '16px' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Reviews Completed" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Stability Growth */}
        <div className="glass p-8 rounded-3xl border border-white/10 shadow-2xl lg:col-span-2">
          <h2 className="text-2xl font-bold mb-6">Stability Growth Evolution</h2>
          {stabilityData.length === 0 ? (
            <p className="text-slate-500 text-center py-12">Complete multiple reviews to see how your memory stability grows.</p>
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stabilityData.slice(0, 50)} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
                  <XAxis dataKey="review_number" stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} label={{ value: 'Total Reviews Completed', position: 'insideBottom', offset: -10, fill: '#94a3b8' }} />
                  <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} label={{ value: 'Stability (Days)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#ffffff2a', borderRadius: '16px' }}
                    labelFormatter={(val) => `Review #${val}`}
                  />
                  <Line type="monotone" dataKey="stability" stroke="#10b981" strokeWidth={4} dot={{ fill: '#10b981', r: 4 }} activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="text-center text-sm text-slate-400 mt-4">The average interval (in days) your memory can sustain a concept before forgetting.</p>
        </div>

        {/* Weak Concepts Table */}
        <div className="glass p-8 rounded-3xl border border-white/10 shadow-2xl lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <AlertTriangle className="text-amber-500" />
              At-Risk Knowledge
            </h2>
            <button 
              onClick={() => navigate('/study')}
              className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2"
            >
              <Play size={16} /> Study Now
            </button>
          </div>
          
          {weakConcepts.length === 0 ? (
            <p className="text-slate-500 text-center py-12">Your memory state is perfect! No weak concepts detected.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="p-4 text-slate-400 font-medium">Concept</th>
                    <th className="p-4 text-slate-400 font-medium">Retrievability (R)</th>
                    <th className="p-4 text-slate-400 font-medium">Stability (Days)</th>
                    <th className="p-4 text-slate-400 font-medium">Algorithm</th>
                  </tr>
                </thead>
                <tbody>
                  {weakConcepts.map((concept) => (
                    <tr key={concept.concept_id} className="border-b border-white/5 hover:bg-white/5 transition">
                      <td className="p-4 font-medium text-white">{concept.title}</td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden max-w-[100px]">
                            <div 
                              className={`h-full ${concept.retrievability < 0.5 ? 'bg-red-500' : concept.retrievability < 0.8 ? 'bg-amber-500' : 'bg-green-500'}`}
                              style={{ width: `${Math.max(5, concept.retrievability * 100)}%` }}
                            />
                          </div>
                          <span className="text-xs text-slate-400">{(concept.retrievability * 100).toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="p-4 text-slate-300">{concept.stability.toFixed(1)} d</td>
                      <td className="p-4">
                        <span className="bg-slate-800 text-slate-300 px-2 py-1 rounded-md text-xs font-mono">
                          {concept.algorithm}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-center text-sm text-slate-400 mt-4">Concepts with the highest probability of being forgotten if not reviewed soon.</p>
        </div>

      </div>
    </div>
  );
};

export default Analytics;
