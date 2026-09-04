import type { Metadata } from 'next';
import { AuthProvider } from '@/hooks/useAuth';
import { AppShell } from '@/hooks/AppShell';
import './globals.css';

export const metadata: Metadata = {
  title: 'SwarmVault',
  description: 'AI-powered conversation memory and retrieval',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">
        <AuthProvider>
          <AppShell>
            {children}
          </AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
