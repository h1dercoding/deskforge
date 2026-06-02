import { LoginForm } from '@/components/auth/login-form';

export default function LoginPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-center mb-1">Welcome back</h1>
      <p className="text-center text-muted-foreground mb-6">
        Sign in to your account to continue
      </p>
      <LoginForm />
    </div>
  );
}
