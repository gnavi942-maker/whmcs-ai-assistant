"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  LineChart, Line, CartesianGrid 
} from "recharts";
import { 
  Bot, Users, MessageSquare, AlertTriangle, Send, 
  RefreshCw, LogOut, CheckCircle, Mail, Database, ShieldAlert, Sparkles
} from "lucide-react";

export default function Dashboard() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  
  // Analytics data
  const [stats, setStats] = useState<any>({
    total_conversations: 0,
    total_leads: 0,
    total_queries: 0,
    failed_queries_count: 0,
    daily_analytics: [],
    top_products: [],
    failed_queries: []
  });

  // Leads list
  const [leads, setLeads] = useState<any[]>([]);
  const [scrapingStatus, setScrapingStatus] = useState("");
  const [activeTab, setActiveTab] = useState("overview");

  // Check existing token
  useEffect(() => {
    const savedToken = localStorage.getItem("whmcs_admin_token");
    if (savedToken) {
      setToken(savedToken);
      setIsLoggedIn(true);
      fetchAnalytics(savedToken);
      fetchLeads(savedToken);
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      if (res.status === 401) {
        setErrorMsg("Invalid username or password.");
        return;
      }
      const data = await res.json();
      if (data.access_token) {
        localStorage.setItem("whmcs_admin_token", data.access_token);
        setToken(data.access_token);
        setIsLoggedIn(true);
        fetchAnalytics(data.access_token);
        fetchLeads(data.access_token);
      }
    } catch (err) {
      setErrorMsg("Failed to connect to backend server.");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("whmcs_admin_token");
    setToken("");
    setIsLoggedIn(false);
  };

  const fetchAnalytics = async (authToken: string) => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/analytics", {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (res.status === 401) {
        handleLogout();
        return;
      }
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchLeads = async (authToken: string) => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/leads", {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (res.status === 200) {
        const data = await res.json();
        setLeads(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const triggerIngestion = async () => {
    setScrapingStatus("syncing");
    try {
      const res = await fetch("http://localhost:8000/api/v1/scrape", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.status === 200) {
        setScrapingStatus("success");
        setTimeout(() => {
          setScrapingStatus("");
          fetchAnalytics(token);
        }, 3000);
      } else {
        setScrapingStatus("error");
      }
    } catch (err) {
      setScrapingStatus("error");
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-slate-100 font-sans p-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md bg-slate-900/60 border border-slate-800 rounded-2xl p-8 backdrop-blur-xl shadow-2xl"
        >
          <div className="flex flex-col items-center gap-2 mb-8">
            <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              <Bot size={24} />
            </div>
            <h2 className="text-xl font-bold tracking-tight">WHMCS AI Assistant</h2>
            <p className="text-xs text-slate-400">Admin Control Panel Login</p>
          </div>

          {errorMsg && (
            <div className="mb-4 p-3 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-400 flex items-center gap-2">
              <ShieldAlert size={14} /> {errorMsg}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-300 mb-1.5">Username</label>
              <input 
                type="text" 
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder:text-slate-600"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-300 mb-1.5">Password</label>
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="adminpassword123"
                className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder:text-slate-600"
              />
            </div>
            <button 
              type="submit"
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold tracking-wide transition-all shadow-md shadow-blue-500/20 active:scale-95 text-xs"
            >
              Sign In to Dashboard
            </button>
          </form>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans">
      {/* Sidebar navigation */}
      <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col p-6 gap-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/10">
            <Bot size={20} />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight">AI Assistant Pro</h1>
            <span className="text-[10px] text-slate-400">Admin Control</span>
          </div>
        </div>

        <nav className="flex-1 space-y-1.5 text-xs">
          <button 
            onClick={() => setActiveTab("overview")}
            className={`w-full text-left p-3 rounded-xl transition-all flex items-center gap-2.5 font-medium ${activeTab === "overview" ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"}`}
          >
            <Database size={16} /> Dashboard Overview
          </button>
          <button 
            onClick={() => setActiveTab("leads")}
            className={`w-full text-left p-3 rounded-xl transition-all flex items-center gap-2.5 font-medium ${activeTab === "leads" ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"}`}
          >
            <Users size={16} /> Leads Collected
          </button>
          <button 
            onClick={() => setActiveTab("unresolved")}
            className={`w-full text-left p-3 rounded-xl transition-all flex items-center gap-2.5 font-medium ${activeTab === "unresolved" ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"}`}
          >
            <AlertTriangle size={16} /> Unresolved Queries
          </button>
        </nav>

        <div className="border-t border-slate-800 pt-4 flex flex-col gap-2">
          <button 
            onClick={triggerIngestion}
            disabled={scrapingStatus === "syncing"}
            className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            <RefreshCw size={14} className={scrapingStatus === "syncing" ? "animate-spin" : ""} />
            {scrapingStatus === "syncing" ? "Crawling Site..." : "Trigger Knowledge Sync"}
          </button>
          
          <button 
            onClick={handleLogout}
            className="w-full py-2.5 bg-red-950/20 hover:bg-red-950/40 text-red-400 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all border border-red-900/30"
          >
            <LogOut size={14} /> Logout
          </button>
        </div>
      </div>

      {/* Main dashboard content */}
      <main className="flex-1 p-8 overflow-y-auto space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight">System Console</h2>
            <p className="text-xs text-slate-400">Monitoring website scraping, chat analytics, and user requests</p>
          </div>
          <div className="flex items-center gap-2.5 text-xs bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-xl">
            <span className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse"></span>
            <span className="font-semibold text-slate-300">API Connection Active</span>
          </div>
        </header>

        {scrapingStatus === "success" && (
          <div className="p-4 bg-emerald-950/40 border border-emerald-800/60 text-emerald-400 rounded-2xl flex items-center gap-3 text-xs">
            <CheckCircle size={18} /> Ingestion pipeline successfully synced. Recalculating embeddings in the background...
          </div>
        )}

        {scrapingStatus === "error" && (
          <div className="p-4 bg-red-950/40 border border-red-800/60 text-red-400 rounded-2xl flex items-center gap-3 text-xs">
            <AlertTriangle size={18} /> Ingestion failed. Please verify scraper configurations in backend variables.
          </div>
        )}

        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Stat Cards */}
            <div className="grid grid-cols-4 gap-5">
              <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-5 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Total Queries Logged</span>
                  <p className="text-2xl font-bold mt-1">{stats.total_queries}</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400 border border-blue-500/20">
                  <Send size={18} />
                </div>
              </div>
              <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-5 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Active Conversations</span>
                  <p className="text-2xl font-bold mt-1">{stats.total_conversations}</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center text-violet-400 border border-violet-500/20">
                  <MessageSquare size={18} />
                </div>
              </div>
              <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-5 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Captured Leads</span>
                  <p className="text-2xl font-bold mt-1">{stats.total_leads}</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center text-green-400 border border-green-500/20">
                  <Users size={18} />
                </div>
              </div>
              <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-5 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Failed Queries Rate</span>
                  <p className="text-2xl font-bold mt-1">
                    {stats.total_queries > 0 ? ((stats.failed_queries_count / stats.total_queries) * 100).toFixed(1) : 0}%
                  </p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 border border-amber-500/20">
                  <AlertTriangle size={18} />
                </div>
              </div>
            </div>

            {/* Graphs Grid */}
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-slate-900/40 border border-slate-850 rounded-2xl p-6">
                <h3 className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-4">Chat Engagement (Last 7 Days)</h3>
                <div className="h-64">
                  {stats.daily_analytics && stats.daily_analytics.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={stats.daily_analytics}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="date" stroke="#64748b" style={{ fontSize: 9 }} />
                        <YAxis stroke="#64748b" style={{ fontSize: 9 }} />
                        <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b" }} />
                        <Line type="monotone" dataKey="queries" stroke="#2563eb" strokeWidth={2.5} activeDot={{ r: 6 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-xs text-slate-600">No session metrics logged yet.</div>
                  )}
                </div>
              </div>

              <div className="bg-slate-900/40 border border-slate-850 rounded-2xl p-6">
                <h3 className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-4">Top Modules Recommended</h3>
                <div className="h-64">
                  {stats.top_products && stats.top_products.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={stats.top_products}>
                        <XAxis dataKey="name" stroke="#64748b" style={{ fontSize: 8 }} />
                        <YAxis stroke="#64748b" style={{ fontSize: 9 }} />
                        <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b" }} />
                        <Bar dataKey="count" fill="#35b956" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-xs text-slate-600">No product recommendations calculated yet.</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "leads" && (
          <div className="bg-slate-900/40 border border-slate-850 rounded-2xl p-6">
            <h3 className="text-sm font-bold tracking-tight mb-4 flex items-center gap-2">
              <Users size={18} className="text-blue-500" /> Active Leads Registry
            </h3>
            <div className="overflow-x-auto text-xs">
              {leads.length > 0 ? (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-3 px-4">Name</th>
                      <th className="py-3 px-4">Email</th>
                      <th className="py-3 px-4">Industry/Business</th>
                      <th className="py-3 px-4">Requirements</th>
                      <th className="py-3 px-4">Date Collected</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leads.map((lead) => (
                      <tr key={lead.id} className="border-b border-slate-800/50 hover:bg-slate-800/10">
                        <td className="py-3 px-4 font-semibold text-slate-200">{lead.name}</td>
                        <td className="py-3 px-4 text-blue-400 flex items-center gap-1.5">
                          <Mail size={12} /> {lead.email}
                        </td>
                        <td className="py-3 px-4 text-slate-300">{lead.business_type || "N/A"}</td>
                        <td className="py-3 px-4 text-slate-400 max-w-xs truncate">{lead.requirement}</td>
                        <td className="py-3 px-4 text-slate-500">{new Date(lead.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="py-12 text-center text-slate-500">No sales leads collected yet. Prompt the AI chatbot regarding pricing to trigger.</div>
              )}
            </div>
          </div>
        )}

        {activeTab === "unresolved" && (
          <div className="bg-slate-900/40 border border-slate-850 rounded-2xl p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-bold tracking-tight flex items-center gap-2">
                <AlertTriangle size={18} className="text-amber-500" /> Failed & Unresolved Inquiries
              </h3>
              <span className="text-[10px] bg-slate-800 text-slate-400 px-3 py-1 rounded-full">Knowledge Gaps Tracker</span>
            </div>
            <div className="space-y-3 text-xs">
              {stats.failed_queries && stats.failed_queries.length > 0 ? (
                stats.failed_queries.map((q: any, i: number) => (
                  <div key={i} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-200">{q.query}</p>
                      <span className="text-[10px] text-slate-500 mt-1 block">Logged: {new Date(q.date).toLocaleString()}</span>
                    </div>
                    <button 
                      onClick={() => alert("Please add the missing content/FAQ on your WHMCS site and trigger Knowledge Sync.")}
                      className="px-3 py-1.5 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 rounded-lg font-semibold border border-blue-500/20 transition-all"
                    >
                      Resolve Gap
                    </button>
                  </div>
                ))
              ) : (
                <div className="py-12 text-center text-slate-500">Zero knowledge gaps detected! The RAG retrieval is answering all queries with high confidence.</div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
