"use client";

import React, { useEffect } from "react";
import dynamic from "next/dynamic";

const ChatWidget = dynamic(() => import("@/components/ChatWidget"), {
  ssr: false,
});

export default function ChatEmbed() {
  // Let the host window know this widget is loaded
  useEffect(() => {
    if (window.parent) {
      window.parent.postMessage("widget_ready", "*");
    }
  }, []);

  return (
    <div className="bg-transparent w-full h-full flex items-end justify-end">
      {/* Renders only the chat widget balloon */}
      <ChatWidget />
    </div>
  );
}
