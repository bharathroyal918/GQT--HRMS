import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { MobileDrawer } from "./MobileDrawer";
import { Footer } from "./Footer";

export const AppShell: React.FC = () => {
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col bg-brand-surface">
      <Header onToggleSidebar={() => setMobileDrawerOpen(true)} />

      <div className="flex flex-1">
        {/* Desktop Sidebar */}
        <div className="hidden md:block">
          <Sidebar />
        </div>

        {/* Mobile Navigation Drawer */}
        <MobileDrawer
          isOpen={mobileDrawerOpen}
          onClose={() => setMobileDrawerOpen(false)}
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-x-hidden p-4 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>

      <Footer />
    </div>
  );
};
