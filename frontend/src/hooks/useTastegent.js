import { useState, useEffect, useRef } from 'react';
import { getMenu, chat } from '../services/api';

export function useTastegent() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "晚上好，我是您的专属寻味助理。今晚想体验怎样的味觉之旅？" }
  ]);
  const [menu, setMenu] = useState([]);
  const [isLoadingMenu, setIsLoadingMenu] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);

  // Fetch Menu
  useEffect(() => {
    const fetchMenu = async () => {
      try {
        const data = await getMenu();
        if (Array.isArray(data)) {
          // Normalize tags to be title case for consistent grouping
          const normalizedMenu = data.map(item => ({
            ...item,
            tags: item.tags ? item.tags.map(t => t.charAt(0).toUpperCase() + t.slice(1)) : []
          }));
          setMenu(normalizedMenu);
        } else {
          console.error('Invalid menu format:', data);
          setMenu([]);
        }
      } catch (err) {
        setError('Failed to load menu');
        console.error(err);
      } finally {
        setIsLoadingMenu(false);
      }
    };

    fetchMenu();
  }, []);

  // Send Message
  const sendMessage = async (text, storeId) => {
    if (!text.trim()) return;

    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const botMessage = await chat([...messages, userMsg], storeId);
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "抱歉，我遇到了一些问题，请稍后再试。"
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  // Group Menu Logic
  const groupedMenu = menu.reduce((acc, item) => {
    const category = item.tags && item.tags.length > 0 ? item.tags[0] : 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(item);
    return acc;
  }, {});

  const menuCategories = Object.keys(groupedMenu).map(key => ({
    id: key,
    title: key,
    items: groupedMenu[key]
  }));

  return {
    messages,
    menuCategories,
    isLoadingMenu,
    isTyping,
    sendMessage,
    error
  };
}
