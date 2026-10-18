import type { Metadata } from 'next';
import { AuthProvider } from '@/hooks/useAuth';
import { ThemeProvider } from '@/hooks/useTheme';
import { AppShell } from '@/hooks/AppShell';
import './globals.css';

export const metadata: Metadata = {
  title: 'SwarmVault',
  description: 'AI-powered conversation memory and retrieval',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(() => { try { const t = localStorage.getItem('sv_theme'); if (t === 'light') document.documentElement.setAttribute('data-theme', 'light'); } catch {} })();`,
          }}
        />
      </head>
      <body className="antialiased">
        <ThemeProvider>
          <AuthProvider>
            <AppShell>
              {children}
            </AppShell>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
