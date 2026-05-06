import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { ChatPage } from '../pages/ChatPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        {/* Public / Core Routes */}
        <Route path="/" element={<ChatPage />} />
        <Route path="/chat/:chatId" element={<ChatPage />} />
        
        {/* Future Protected Routes (Settings, Profile, etc.) will be injected here */}
      </Route>
    </Routes>
  );
}
