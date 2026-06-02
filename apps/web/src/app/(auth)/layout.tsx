import { Wrench } from 'lucide-react';
import Link from 'next/link';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 via-background to-primary/10 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <Wrench className="h-6 w-6 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold">DeskForge</span>
          </Link>
        </div>
        <div className="bg-card border rounded-xl shadow-sm p-8">
          {children}
        </div>
      </div>
    </div>
  );
}
