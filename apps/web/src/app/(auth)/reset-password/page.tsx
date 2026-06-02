'use client';

import React, { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/hooks/useAuth';
import { toast } from '@/hooks/useToast';

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const { forgotPassword, resetPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [resetDone, setResetDone] = useState(false);

  const handleForgot = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await forgotPassword(email);
      setSent(true);
      toast({ title: 'Email sent', description: 'Check your inbox for the reset link.', variant: 'success' });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to send reset email';
      toast({ title: 'Error', description: message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast({ title: 'Passwords do not match', variant: 'destructive' });
      return;
    }
    if (newPassword.length < 8) {
      toast({ title: 'Password too short', description: 'Must be at least 8 characters.', variant: 'destructive' });
      return;
    }
    setIsLoading(true);
    try {
      await resetPassword(token!, newPassword);
      setResetDone(true);
      toast({ title: 'Password reset!', variant: 'success' });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to reset password';
      toast({ title: 'Error', description: message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  // If there's a token, show the reset form
  if (token) {
    if (resetDone) {
      return (
        <div className="text-center space-y-4">
          <CheckCircle className="h-12 w-12 text-green-500 mx-auto" />
          <h1 className="text-2xl font-bold">Password reset!</h1>
          <p className="text-muted-foreground">Your password has been updated successfully.</p>
          <Button asChild className="mt-4">
            <Link href="/login">Sign in</Link>
          </Button>
        </div>
      );
    }

    return (
      <div>
        <h1 className="text-2xl font-bold text-center mb-1">Set new password</h1>
        <p className="text-center text-muted-foreground mb-6">Enter your new password below.</p>
        <form onSubmit={handleReset} className="space-y-4">
          <Input
            label="New Password"
            type="password"
            placeholder="••••••••"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            autoComplete="new-password"
          />
          <Input
            label="Confirm Password"
            type="password"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
          />
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Resetting...' : 'Reset Password'}
          </Button>
        </form>
      </div>
    );
  }

  // No token — show the forgot password form
  if (sent) {
    return (
      <div className="text-center space-y-4">
        <CheckCircle className="h-12 w-12 text-green-500 mx-auto" />
        <h1 className="text-2xl font-bold">Check your email</h1>
        <p className="text-muted-foreground">
          We sent a password reset link to <strong>{email}</strong>.
        </p>
        <Button variant="outline" asChild className="mt-4">
          <Link href="/login">Back to Login</Link>
        </Button>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-center mb-1">Forgot password?</h1>
      <p className="text-center text-muted-foreground mb-6">
        Enter your email and we&apos;ll send you a reset link.
      </p>
      <form onSubmit={handleForgot} className="space-y-4">
        <Input
          label="Email"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
        />
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send Reset Link'}
        </Button>
      </form>
      <p className="text-center text-sm text-muted-foreground mt-4">
        Remember your password?{' '}
        <Link href="/login" className="text-primary hover:underline font-medium">
          Sign in
        </Link>
      </p>
    </div>
  );
}
