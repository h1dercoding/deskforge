'use client';

import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  message?: string;
  className?: string;
  size?: number;
}

export function LoadingSpinner({ message, className, size = 24 }: LoadingSpinnerProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-2', className)}>
      <Loader2 className="animate-spin text-muted-foreground" size={size} />
      {message && <p className="text-sm text-muted-foreground">{message}</p>}
    </div>
  );
}
