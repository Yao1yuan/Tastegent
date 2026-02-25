import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Send, Sparkles, Utensils, Wine, Leaf, Clock, Menu, X, ChevronDown, ChevronUp } from 'lucide-react';
import { useTastegent } from '../hooks/useTastegent';
import { cn } from '../lib/utils';
import { API_URL } from '../services/api';

// --- UI Components ---

const MessageBubble = ({ role, content }) => {
  const isUser = role === 'user';
  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] sm:max-w-[70%] p-5 rounded-2xl leading-relaxed tracking-wide text-sm sm:text-base animate-in fade-in zoom-in duration-300",
          isUser
            ? "bg-blue-600 text-white shadow-md rounded-br-sm"
            : "bg-white/80 border border-white shadow-sm text-slate-700 rounded-bl-sm"
        )}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-3 text-blue-600">
            <Sparkles size={14} />
            <span className="text-xs uppercase tracking-widest font-semibold">Taste AI</span>
          </div>
        )}
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  );
};

const TypingIndicator = () => (
  <div className="flex justify-start w-full">
    <div className="bg-white/80 border border-white shadow-sm p-5 rounded-2xl rounded-bl-sm flex items-center gap-2">
      {[0, 150, 300].map((delay) => (
        <div
          key={delay}
          className="w-2 h-2 bg-blue-500/60 rounded-full animate-bounce"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  </div>
);

const QuickActionButton = ({ icon, label, onClick }) => (
  <button
    onClick={onClick}
    className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/70 border border-white hover:bg-blue-50 hover:border-blue-200 hover:text-blue-600 transition-all duration-300 text-xs sm:text-sm text-slate-500 tracking-wider shadow-sm"
  >
    {icon}
    {label}
  </button>
);

const MenuCategory = ({ category, isExpanded, onToggle, onAskDish }) => (
  <div className="bg-white/60 border border-white rounded-2xl overflow-hidden shadow-sm transition-all duration-300">
    <button
      onClick={onToggle}
      className="w-full px-5 py-4 flex justify-between items-center hover:bg-white/40 transition-colors"
    >
      <span className="font-medium text-slate-700 tracking-wider">{category.title}</span>
      {isExpanded ? <ChevronUp size={18} className="text-blue-500" /> : <ChevronDown size={18} className="text-slate-400" />}
    </button>

    <div
      className={cn(
        "transition-all duration-500 ease-in-out origin-top",
        isExpanded ? "max-h-[1000px] opacity-100" : "max-h-0 opacity-0"
      )}
    >
      <div className="px-5 pb-5 flex flex-col gap-4 border-t border-white/50 pt-4">
        {category.items.map((item) => (
          <div key={item.id} className="group relative">
            <div className="flex gap-4">
              <div className="flex-1">
                <div className="flex justify-between items-start mb-1">
                  <h3 className="font-medium text-slate-800 text-sm sm:text-base pr-4">{item.name}</h3>
                  <span className="font-semibold text-blue-600 text-sm whitespace-nowrap">${item.price.toFixed(2)}</span>
                </div>
                <p className="text-xs sm:text-sm text-slate-500 pr-12 leading-relaxed">{item.description}</p>
              </div>
              {item.imageUrl && (
                <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-lg overflow-hidden shrink-0">
                  <img src={`${API_URL}${item.imageUrl}`} alt={item.name} className="w-full h-full object-cover" />
                </div>
              )}
            </div>
            <button
              onClick={() => onAskDish(item.name)}
              className="absolute right-0 top-0 p-1.5 rounded-full text-blue-400 hover:text-white hover:bg-blue-500 transition-all opacity-0 group-hover:opacity-100 shadow-sm"
              title="Ask AI about this dish"
            >
              <Sparkles size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  </div>
);

// --- Main Page Component ---

export default function CustomerPage() {
  const { messages, menuCategories, isTyping, sendMessage } = useTastegent();
  const [inputValue, setInputValue] = useState('');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [expandedCategory, setExpandedCategory] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = () => {
    sendMessage(inputValue, new URLSearchParams(window.location.search).get('store_id'));
    setInputValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAskDish = (dishName) => {
    setIsMenuOpen(false);
    // Slight delay to allow drawer to close smoothly
    setTimeout(() => {
        sendMessage(`Tell me more about the ${dishName}.`, new URLSearchParams(window.location.search).get('store_id'));
    }, 300);
  };

  const quickActions = [
    { icon: <Sparkles size={16} />, label: "Chef's Recommendation", query: "What do you recommend?" },
    { icon: <Leaf size={16} />, label: "Vegetarian Options", query: "Do you have vegetarian dishes?" },
    { icon: <Wine size={16} />, label: "Wine Pairing", query: "What wine goes well with this?" },
  ];

  return (
    <div className="relative flex flex-col min-h-screen bg-[#f8fafc] text-slate-800 font-sans selection:bg-blue-500/20">
      {/* Background Ambience */}
      <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-radial-gradient from-blue-400/30 to-transparent blur-[80px] animate-aurora pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[60vw] h-[60vw] rounded-full bg-radial-gradient from-blue-500/20 to-transparent blur-[80px] animate-aurora-reverse pointer-events-none" />

      {/* Main Content */}
     {/* Main Content */}
      <div className="relative z-10 flex flex-col items-center min-h-screen w-full p-0 sm:p-6 md:p-10">
        <div className="w-full min-h-screen sm:rounded-3xl flex flex-col relative bg-white/60 backdrop-blur-xl border-0 sm:border border-white/80 sm:shadow-2xl">

          {/* Header */}
          <header className="sticky top-0 px-6 sm:px-8 py-5 sm:py-6 border-b border-white/60 flex items-center justify-between z-50 bg-white/80 backdrop-blur-md shrink-0">
            <div className="flex items-center gap-3 sm:gap-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30 shrink-0">
                <Utensils className="text-white w-5 h-5 sm:w-6 sm:h-6" />
              </div>
              <div>
                <h1 className="text-lg sm:text-xl font-medium tracking-widest text-slate-800">TASTE <span className="text-blue-600 font-light">AI</span></h1>
                <p className="text-[10px] sm:text-xs text-slate-500 tracking-wider mt-0.5 flex items-center gap-1">
                  <Clock size={10} /> OPEN • Personal Concierge
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsMenuOpen(true)}
              className="flex items-center gap-2 px-3 py-2 sm:px-4 sm:py-2 rounded-full bg-white/50 border border-white hover:bg-white/80 hover:shadow-md hover:text-blue-600 transition-all duration-300 text-slate-600 shadow-sm shrink-0"
            >
              <Menu size={18} />
              <span className="text-xs sm:text-sm font-medium tracking-widest">MENU</span>
            </button>
          </header>

          {/* Chat Area */}
          <div className="flex-1 min-h-0 p-6 sm:p-8 flex flex-col gap-6">
            {messages.map((msg, index) => (
              <MessageBubble key={index} role={msg.role} content={msg.content} />
            ))}
            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="sticky bottom-0 z-50 px-4 pt-4 pb-[calc(1rem+env(safe-area-inset-bottom))] sm:p-6 bg-white/90 backdrop-blur-md border-t border-white/60 shrink-0">
            <div className="flex flex-wrap gap-3 mb-4">
              {quickActions.map((action, idx) => (
                <QuickActionButton
                  key={idx}
                  icon={action.icon}
                  label={action.label}
                  onClick={() => {
                      sendMessage(action.query, new URLSearchParams(window.location.search).get('store_id'));
                  }}
                />
              ))}
            </div>

            <div className="relative flex items-end gap-2 bg-white/80 border border-white rounded-2xl p-2 transition-all duration-300 focus-within:border-blue-300 focus-within:ring-4 focus-within:ring-blue-100 shadow-sm">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about the menu..."
                className="w-full bg-transparent border-none outline-none text-slate-800 placeholder-slate-400 resize-none max-h-32 min-h-[44px] px-4 py-3 text-sm sm:text-base scrollbar-hide leading-relaxed"
                rows={1}
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isTyping}
                className={cn(
                  "p-3 rounded-xl flex items-center justify-center transition-all duration-300",
                  inputValue.trim() && !isTyping
                    ? "bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-500/30"
                    : "bg-slate-100 text-slate-300 cursor-not-allowed"
                )}
              >
                <Send size={20} className={cn(inputValue.trim() && !isTyping && "translate-x-0.5 -translate-y-0.5")} />
              </button>
            </div>
            <div className="text-center mt-4 text-[10px] text-slate-400 uppercase tracking-widest">
              Powered by Tastegent AI
            </div>
          </div>
        </div>
      </div>

      {/* Menu Drawer */}
      {isMenuOpen && createPortal(
        <div className="fixed inset-0 z-[9999] h-[100dvh] w-screen overflow-hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-slate-900/20 backdrop-blur-sm animate-in fade-in duration-300"
            onClick={() => setIsMenuOpen(false)}
          />

          {/* Drawer Panel */}
          <div className="absolute top-0 right-0 bottom-0 w-full sm:w-[400px] bg-white/90 backdrop-blur-xl border-l border-white shadow-2xl flex flex-col h-full animate-in slide-in-from-right duration-300">
            <div className="px-6 py-6 border-b border-white flex justify-between items-center bg-white/50 shrink-0">
              <div>
                <h2 className="text-xl font-semibold tracking-widest text-slate-800">MENU</h2>
                <p className="text-xs text-slate-500 tracking-wider mt-1 uppercase">Tasting Selection</p>
              </div>
              <button
                onClick={() => setIsMenuOpen(false)}
                className="p-2 rounded-full bg-white/50 border border-white hover:bg-slate-100 hover:text-blue-600 transition-all shadow-sm"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 sm:p-6 scrollbar-hide flex flex-col gap-3">
              {menuCategories.length === 0 ? (
                  <div className="text-center text-slate-500 mt-10 animate-pulse">Loading menu...</div>
              ) : (
                  menuCategories.map(category => (
                    <MenuCategory
                      key={category.id}
                      category={category}
                      isExpanded={expandedCategory === category.id}
                      onToggle={() => setExpandedCategory(expandedCategory === category.id ? null : category.id)}
                      onAskDish={handleAskDish}
                    />
                  ))
              )}
            </div>
            <div className="p-6 bg-white/50 border-t border-white text-center text-xs text-slate-500 shrink-0">
              * Menu items subject to seasonal availability.
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
