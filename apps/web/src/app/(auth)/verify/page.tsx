'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';

export default function VerifyPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const { verifyEmail } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'no-token'>(
    token ? 'loading' : 'no-token'
  );

  useEffect(() => {
    if (token) {
      verifyEmail(token)
        .then(() => setStatus('success'))
        .catch(() => setStatus('error'));
    }
  }, [token, verifyEmail]);

  return (
    <div className="text-center space-y-4">
      {status === 'loading' && (
        <>
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <h1 className="text-2xl font-bold">Verifying your email...</h1>
          <p className="text-muted-foreground">Please wait a moment.</p>
        </>
      )}

      {status === 'success' && (
        <>
          <CheckCircle className="h-12 w-12 text-green-500 mx-auto" />
          <h1 className="text-2xl font-bold">Email verified!</h1>
          <p className="text-muted-foreground">
            Your email has been verified successfully. You can now access all features.
          </p>
          <Button asChild className="mt-4">
            <Link href="/">Go to Dashboard</Link>
          </Button>
        </>
      )}

      {status === 'error' && (
        <>
          <XCircle className="h-12 w-12 text-destructive mx-auto" />
          <h1 className="text-2xl font-bold">Verification failed</h1>
          <p className="text-muted-foreground">
            The verification link is invalid or has expired.
          </p>
          <Button variant="outline" asChild className="mt-4">
            <Link href="/login">Back to Login</Link>
          </Button>
        </>
      )}

      {status === 'no-token' && (
        <>
          <h1 className="text-2xl font-bold">Check your email</h1>
          <p className="text-muted-foreground">
            We sent a verification link to your email address. Click the link to verify your account.
          </p>
          <p className="text-sm text-muted-foreground mt-4">
            Didn&apos;t receive the email? Check your spam folder.
          </p>
        </>
      )}
    </div>
  );
}
