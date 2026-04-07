"use client";

import { useState } from "react";
import { User, Bell, Lock, Palette } from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account and preferences
        </p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <nav className="w-48 space-y-1">
          <button
            onClick={() => setActiveTab("profile")}
            className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm ${
              activeTab === "profile"
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            }`}
          >
            <User className="h-4 w-4" />
            Profile
          </button>
          <button
            onClick={() => setActiveTab("notifications")}
            className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm ${
              activeTab === "notifications"
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            }`}
          >
            <Bell className="h-4 w-4" />
            Notifications
          </button>
          <button
            onClick={() => setActiveTab("security")}
            className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm ${
              activeTab === "security"
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            }`}
          >
            <Lock className="h-4 w-4" />
            Security
          </button>
          <button
            onClick={() => setActiveTab("appearance")}
            className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm ${
              activeTab === "appearance"
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            }`}
          >
            <Palette className="h-4 w-4" />
            Appearance
          </button>
        </nav>

        {/* Content */}
        <div className="flex-1 rounded-lg border bg-card p-6">
          {activeTab === "profile" && <ProfileSettings />}
          {activeTab === "notifications" && <NotificationSettings />}
          {activeTab === "security" && <SecuritySettings />}
          {activeTab === "appearance" && <AppearanceSettings />}
        </div>
      </div>
    </div>
  );
}

function ProfileSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Profile Settings</h2>
        <p className="text-sm text-muted-foreground">
          Update your personal information
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Full Name</label>
          <input
            type="text"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            placeholder="John Doe"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Email</label>
          <input
            type="email"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            placeholder="john@example.com"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Currency</label>
          <select className="w-full rounded-md border bg-background px-3 py-2 text-sm">
            <option value="USD">USD - US Dollar</option>
            <option value="EUR">EUR - Euro</option>
            <option value="GBP">GBP - British Pound</option>
          </select>
        </div>
        <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
          Save Changes
        </button>
      </div>
    </div>
  );
}

function NotificationSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Notification Settings</h2>
        <p className="text-sm text-muted-foreground">
          Configure how you receive notifications
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Email Notifications</p>
            <p className="text-sm text-muted-foreground">
              Receive weekly spending summaries
            </p>
          </div>
          <input type="checkbox" defaultChecked className="h-4 w-4" />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Budget Alerts</p>
            <p className="text-sm text-muted-foreground">
              Get notified when approaching budget limits
            </p>
          </div>
          <input type="checkbox" defaultChecked className="h-4 w-4" />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Large Transaction Alerts</p>
            <p className="text-sm text-muted-foreground">
              Notify for transactions over $500
            </p>
          </div>
          <input type="checkbox" className="h-4 w-4" />
        </div>
      </div>
    </div>
  );
}

function SecuritySettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Security Settings</h2>
        <p className="text-sm text-muted-foreground">
          Manage your account security
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Current Password</label>
          <input
            type="password"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">New Password</label>
          <input
            type="password"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Confirm New Password</label>
          <input
            type="password"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
          />
        </div>
        <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
          Update Password
        </button>
      </div>
    </div>
  );
}

function AppearanceSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Appearance Settings</h2>
        <p className="text-sm text-muted-foreground">
          Customize the look and feel
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Theme</label>
          <select className="w-full rounded-md border bg-background px-3 py-2 text-sm">
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System</option>
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Date Format</label>
          <select className="w-full rounded-md border bg-background px-3 py-2 text-sm">
            <option value="MM/DD/YYYY">MM/DD/YYYY</option>
            <option value="DD/MM/YYYY">DD/MM/YYYY</option>
            <option value="YYYY-MM-DD">YYYY-MM-DD</option>
          </select>
        </div>
      </div>
    </div>
  );
}
