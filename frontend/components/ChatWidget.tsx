"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  MessageSquare, X, Send, Mic, MicOff, Volume2, 
  Bot, User, Sparkles, ExternalLink, RefreshCw 
} from "lucide-react";
import ReactMarkdown from "react-markdown";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  matchedProducts?: string[];
  isLeadForm?: boolean;
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hi 👋! I'm your WHMCS AI Assistant. How can I help you today? I can recommend billing modules, help with module configuration, pricing, or guide you to support.",
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [sessionId, setSessionId] = useState("");
  
  // Lead form states
  const [leadName, setLeadName] = useState("");
  const [leadEmail, setLeadEmail] = useState("");
  const [leadBizType, setLeadBizType] = useState("");
  const [leadRequirement, setLeadRequirement] = useState("");
  const [leadSubmitted, setLeadSubmitted] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Initialize Session ID
  useEffect(() => {
    setSessionId("session_" + Math.random().toString(36).substring(2, 11));
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Post Message to Parent Iframe for Resizing
  useEffect(() => {
    if (typeof window !== "undefined" && window.parent) {
      window.parent.postMessage(isOpen ? "expand" : "collapse", "*");
    }
  }, [isOpen]);

  // Web Speech API configuration
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const rec = new SpeechRecognition();
        rec.continuous = false;
        rec.interimResults = false;
        rec.lang = "en-US";
        
        rec.onresult = (event: any) => {
          const speechToText = event.results[0][0].transcript;
          setInputText(speechToText);
          setIsListening(false);
          handleSendMessage(speechToText);
        };

        rec.onerror = (e: any) => {
          console.error("Speech recognition error:", e);
          setIsListening(false);
        };

        rec.onend = () => {
          setIsListening(false);
        };

        recognitionRef.current = rec;
      }
    }
  }, [sessionId]);

  const handleSendMessage = async (textToSend: string) => {
    if (!textToSend.trim()) return;

    const userMsgId = "msg_" + Date.now();
    const userMsg: Message = { id: userMsgId, role: "user", content: textToSend };
    setMessages(prev => [...prev, userMsg]);
    setInputText("");
    setIsTyping(true);

    try {
      const endpoint = voiceEnabled ? "voice-chat" : "chat";
      const res = await fetch(`http://localhost:8000/api/v1/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: textToSend })
      });
      const data = await res.json();
      
      const botMsgId = "msg_bot_" + Date.now();
      const botMsg: Message = {
        id: botMsgId,
        role: "assistant",
        content: data.response || data.text,
        matchedProducts: data.matched_products || []
      };
      
      setMessages(prev => [...prev, botMsg]);

      // If voice enabled, play the TTS audio base64
      if (voiceEnabled && data.audio_base64) {
        const audioSrc = `data:audio/mp3;base64,${data.audio_base64}`;
        const audio = new Audio(audioSrc);
        audio.play().catch(err => console.error("Audio playback failed", err));
      }

      // Automatically append lead generation form if the prompt requests lead info or user asks for human support
      const promptRequiresLead = checkKeywordsForLead(textToSend);
      if (promptRequiresLead) {
        setTimeout(() => {
          setMessages(prev => [...prev, {
            id: "lead_form_" + Date.now(),
            role: "assistant",
            content: "Please fill in your details below so our representative can get back to you:",
            isLeadForm: true
          }]);
        }, 800);
      }

    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        id: "err_" + Date.now(),
        role: "assistant",
        content: "Oops! I encountered an error connecting to my backend. Please verify that the local FastAPI server is running."
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const checkKeywordsForLead = (text: string) => {
    const keywords = ["quote", "contact human", "talk to human", "enterprise", "custom development", "hire developer", "custom module"];
    return keywords.some(kw => text.toLowerCase().includes(kw));
  };

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMessage(suggestion);
  };

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert("Speech Recognition API is not supported in this browser. Please use Chrome/Safari.");
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const submitLead = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadName || !leadEmail) return;

    try {
      await fetch("http://localhost:8000/api/v1/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: leadName,
          email: leadEmail,
          business_type: leadBizType,
          requirement: leadRequirement || "Inquired via chat widget"
        })
      });
      
      setLeadSubmitted(true);
      setMessages(prev => [...prev, {
        id: "lead_success_" + Date.now(),
        role: "assistant",
        content: `Thank you, **${leadName}**! Your lead details have been collected successfully. An agent will contact you at **${leadEmail}** shortly.`
      }]);
    } catch (err) {
      console.error("Lead submit error", err);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 font-sans">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="w-96 h-[540px] rounded-2xl glass shadow-2xl flex flex-col overflow-hidden border border-slate-200/80 dark:border-slate-800/80 mb-4"
          >
            {/* Widget Header */}
            <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-700 text-white flex items-center justify-between shadow-md">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center">
                  <Bot size={18} className="text-blue-100" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm leading-tight">WHMCS AI Assistant</h3>
                  <span className="text-[10px] text-blue-200 flex items-center gap-1">
                    <Sparkles size={8} /> Online & Product-Aware
                  </span>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {/* Voice Toggle */}
                <button 
                  onClick={() => setVoiceEnabled(!voiceEnabled)}
                  className={`p-1.5 rounded-lg hover:bg-white/10 transition-colors ${voiceEnabled ? 'text-green-300' : 'text-blue-200'}`}
                  title={voiceEnabled ? "Voice Enabled" : "Enable Voice Assistant"}
                >
                  <Volume2 size={16} />
                </button>
                {/* Close Button */}
                <button 
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-white/10 transition-colors text-blue-200"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Conversation Area */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/50 dark:bg-slate-900/30">
              {messages.map((msg) => (
                <div key={msg.id} className="space-y-1.5">
                  <div className={`flex items-start gap-2.5 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    {msg.role === "assistant" && (
                      <div className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
                        <Bot size={13} className="text-slate-600 dark:text-slate-300" />
                      </div>
                    )}
                    
                    <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-xs shadow-sm leading-relaxed ${
                      msg.role === "user" 
                        ? "bg-blue-600 text-white rounded-tr-none" 
                        : "bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 border border-slate-100 dark:border-slate-800 rounded-tl-none"
                    }`}>
                      {msg.isLeadForm && !leadSubmitted ? (
                        <form onSubmit={submitLead} className="space-y-2 mt-2 text-slate-800 dark:text-slate-200">
                          <div>
                            <label className="block text-[10px] font-semibold uppercase text-slate-400">Full Name</label>
                            <input 
                              type="text" 
                              required 
                              value={leadName} 
                              onChange={(e) => setLeadName(e.target.value)}
                              className="w-full p-1.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" 
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold uppercase text-slate-400">Email Address</label>
                            <input 
                              type="email" 
                              required 
                              value={leadEmail} 
                              onChange={(e) => setLeadEmail(e.target.value)}
                              className="w-full p-1.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" 
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold uppercase text-slate-400">Business Type</label>
                            <input 
                              type="text" 
                              placeholder="e.g. IPTV Reseller, Web Hosting" 
                              value={leadBizType} 
                              onChange={(e) => setLeadBizType(e.target.value)}
                              className="w-full p-1.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" 
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold uppercase text-slate-400">Requirements</label>
                            <textarea 
                              rows={2} 
                              value={leadRequirement} 
                              onChange={(e) => setLeadRequirement(e.target.value)}
                              className="w-full p-1.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                            ></textarea>
                          </div>
                          <button 
                            type="submit" 
                            className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-bold transition-all text-xs"
                          >
                            Submit Requirements
                          </button>
                        </form>
                      ) : (
                        <div className="prose prose-slate dark:prose-invert prose-xs">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      )}
                    </div>

                    {msg.role === "user" && (
                      <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
                        <User size={13} className="text-white" />
                      </div>
                    )}
                  </div>
                  
                  {/* Action/Product Suggestions */}
                  {msg.matchedProducts && msg.matchedProducts.length > 0 && (
                    <div className="pl-8 flex flex-wrap gap-1.5">
                      {msg.matchedProducts.map((prodName) => (
                        <span 
                          key={prodName}
                          onClick={() => handleSuggestionClick(`Tell me more about ${prodName}`)}
                          className="px-2.5 py-1 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-900/60 rounded-full text-[10px] cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/80 transition-colors flex items-center gap-1 font-medium"
                        >
                          <Sparkles size={8} /> {prodName} <ExternalLink size={8} />
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              
              {isTyping && (
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
                    <Bot size={13} className="text-slate-600 dark:text-slate-300" />
                  </div>
                  <div className="bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 border border-slate-100 dark:border-slate-800 px-4 py-2.5 rounded-2xl rounded-tl-none flex items-center gap-1">
                    <span className="w-1.5 h-1.5 bg-slate-400 dark:bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                    <span className="w-1.5 h-1.5 bg-slate-400 dark:bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                    <span className="w-1.5 h-1.5 bg-slate-400 dark:bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Quick Action Chips */}
            <div className="px-4 py-2 border-t border-slate-100 dark:border-slate-800 bg-white/40 dark:bg-slate-900/20 flex gap-1.5 overflow-x-auto whitespace-nowrap scrollbar-none">
              <button 
                onClick={() => handleSuggestionClick("Find a Module")}
                className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full text-[10px] transition-colors border border-slate-200/60 dark:border-slate-700/60"
              >
                🔍 Find Product
              </button>
              <button 
                onClick={() => handleSuggestionClick("Show Stripe Module")}
                className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full text-[10px] transition-colors border border-slate-200/60 dark:border-slate-700/60"
              >
                💳 Payment Gateways
              </button>
              <button 
                onClick={() => handleSuggestionClick("How do I install WHMCS modules?")}
                className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full text-[10px] transition-colors border border-slate-200/60 dark:border-slate-700/60"
              >
                🚀 Installation
              </button>
              <button 
                onClick={() => handleSuggestionClick("Talk to human support agent")}
                className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full text-[10px] transition-colors border border-slate-200/60 dark:border-slate-700/60"
              >
                🙋 Live Agent
              </button>
            </div>

            {/* Input Bar */}
            <div className="p-3 border-t border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-slate-900 flex items-center gap-2">
              {/* Mic Input */}
              <button 
                onClick={toggleListening}
                className={`p-2 rounded-xl transition-all duration-200 ${
                  isListening 
                    ? "bg-red-500 text-white animate-pulse" 
                    : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                {isListening ? <MicOff size={16} /> : <Mic size={16} />}
              </button>

              <input 
                type="text" 
                placeholder={isListening ? "Listening..." : "Type your query here..."}
                value={inputText}
                disabled={isListening}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage(inputText)}
                className="flex-1 min-w-0 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3.5 py-2 rounded-xl text-xs border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
              />

              <button 
                onClick={() => handleSendMessage(inputText)}
                className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-md shadow-blue-500/20 transition-all active:scale-95"
              >
                <Send size={15} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Launcher Bubble */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xl flex items-center justify-center relative hover:from-blue-700 hover:to-indigo-700 transition-all border border-blue-500/30"
      >
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.div
              key="close"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <X size={24} />
            </motion.div>
          ) : (
            <motion.div
              key="chat"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="flex items-center justify-center"
            >
              <MessageSquare size={24} />
              <span className="absolute -top-1 -right-1 w-4.5 h-4.5 bg-green-500 border-2 border-white rounded-full flex items-center justify-center"></span>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
}
