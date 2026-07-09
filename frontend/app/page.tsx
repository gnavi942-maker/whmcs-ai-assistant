"use client";

import React from "react";
import Link from "next/link";
import { Bot, Sparkles, Layout, Zap, ArrowRight, ShieldCheck, HelpCircle, Code } from "lucide-react";
import dynamic from "next/dynamic";

const ChatWidget = dynamic(() => import("@/components/ChatWidget"), {
  ssr: false,
});

// Simple wrapper for Framer Motion to prevent load failures on server render
const motion = {
  div: ({ children, className, ...props }: any) => <div className={className} {...props}>{children}</div>,
  button: ({ children, className, ...props }: any) => <button className={className} {...props}>{children}</button>
};

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans relative overflow-hidden">
      {/* Background radial effects */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-500/10 blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-500/10 blur-[120px] pointer-events-none"></div>

      {/* Header Navigation */}
      <header className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between border-b border-slate-900 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <Bot size={20} />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight">WHMCS AI Assistant Pro</h1>
            <span className="text-[10px] text-slate-400">Enterprise Sales & Support</span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-semibold">
          <Link href="/dashboard" className="px-4.5 py-2.5 bg-slate-900 hover:bg-slate-800 rounded-xl border border-slate-800 transition-all flex items-center gap-1.5">
            <Layout size={14} /> Open Admin Dashboard <ArrowRight size={12} />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 py-20 text-center relative z-10 flex flex-col items-center">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-3xl space-y-6"
        >
          <span className="px-3.5 py-1.5 bg-blue-600/10 text-blue-400 border border-blue-500/20 rounded-full text-xs font-semibold flex items-center gap-2 w-fit mx-auto">
            <Sparkles size={13} /> Next-Gen AI Agent for WHMCS Marketplaces
          </span>
          <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight">
            Automate WHMCS Module Sales & Customer Support Instantly
          </h2>
          <p className="text-base text-slate-400 max-w-xl mx-auto">
            Integrate an intelligent, RAG-powered chatbot trained directly on your product catalog, setup docs, and FAQs. Capture leads, recommend modules, and resolve technical issues.
          </p>
          <div className="flex items-center justify-center gap-3 pt-4">
            <button 
              onClick={() => alert("Please click the floating bubble in the bottom right corner of this page to experience the live AI agent!")}
              className="px-6 py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/15 transition-all text-sm flex items-center gap-2"
            >
              Test Chatbot Widget <ArrowRight size={15} />
            </button>
            <Link href="/dashboard" className="px-6 py-3.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 rounded-xl font-bold transition-all text-sm">
              Explore Admin Control Console
            </Link>
          </div>
        </motion.div>

        {/* Feature Cards Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-24">
          <div className="bg-slate-900/40 border border-slate-850/60 p-6 rounded-2xl text-left space-y-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Zap size={18} />
            </div>
            <h3 className="font-bold text-sm">Semantic RAG Retrieval</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Finds setup files, pricing sheets, and compatibility docs within milliseconds. Uses vector store embeddings for unmatched precision.
            </p>
          </div>
          <div className="bg-slate-900/40 border border-slate-850/60 p-6 rounded-2xl text-left space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <ShieldCheck size={18} />
            </div>
            <h3 className="font-bold text-sm">Automatic Sales Funnels</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Detects buyer intent to capture leads (Name, Email, requirements) automatically when queries involve custom module quotes or pricing requests.
            </p>
          </div>
          <div className="bg-slate-900/40 border border-slate-850/60 p-6 rounded-2xl text-left space-y-3">
            <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
              <Code size={18} />
            </div>
            <h3 className="font-bold text-sm">Voice & Multi-Language</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Includes native speech-to-text, text-to-speech audio outputs, and multilingual support for English, Hindi, Punjabi, and Arabic.
            </p>
          </div>
        </section>

        {/* Integration Instructions */}
        <section className="mt-24 text-left w-full max-w-4xl bg-slate-900/20 border border-slate-900 p-8 rounded-2xl space-y-6">
          <div>
            <h3 className="font-bold text-base tracking-tight">Deploying Chat Widget to Your Site</h3>
            <p className="text-xs text-slate-400 mt-1">To inject this floating chatbot into any client website, embed this script tag prior to body close:</p>
          </div>
          <pre className="p-4 bg-slate-950 border border-slate-800 rounded-xl overflow-x-auto text-[10px] text-blue-400 font-mono">
{`<!-- WHMCS AI Assistant Pro Widget -->
<script 
  src="http://localhost:3000/widget.js" 
  data-session-id="auto"
  async>
</script>`}
          </pre>
        </section>
      </main>

      {/* Floating Chat Widget Embed */}
      <ChatWidget />
    </div>
  );
}


