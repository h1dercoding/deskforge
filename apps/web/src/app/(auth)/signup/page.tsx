import { SignupForm } from '@/components/auth/signup-form';

export default function SignupPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-center mb-1">Create an account</h1>
      <p className="text-center text-muted-foreground mb-6">
        Start building tools in minutes
      </p>
      <SignupForm />
    </div>
  );
}
