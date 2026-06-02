import Link from 'next/link';
import { Wrench, Zap, Database, Share2, Shield, ArrowRight, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const features = [
  {
    icon: Zap,
    title: 'AI-Powered Generation',
    description: 'Describe your tool in plain English. Our AI generates a fully functional app in seconds.',
  },
  {
    icon: Database,
    title: 'Connect Any Data',
    description: 'Upload CSVs, connect Google Sheets, or link PostgreSQL/MySQL databases directly.',
  },
  {
    icon: Share2,
    title: 'Share Instantly',
    description: 'Share your tools with a link. No deployment needed. Works on any device.',
  },
  {
    icon: Shield,
    title: 'Secure by Default',
    description: 'Tools run in sandboxed iframes. Your data never leaves your control.',
  },
];

const pricingPlans = [
  {
    name: 'Free',
    price: '$0',
    description: 'Perfect for trying out DeskForge',
    features: ['3 tools', '3 team members', '2 data sources', 'Community support'],
  },
  {
    name: 'Starter',
    price: '$49',
    description: 'For small teams getting started',
    features: ['Unlimited tools', 'Unlimited team members', '5 data sources', 'Priority support'],
    popular: true,
  },
  {
    name: 'Pro',
    price: '$149',
    description: 'For growing teams with more needs',
    features: ['Unlimited tools', 'Unlimited team members', 'Unlimited data sources', 'Database connections', 'Dedicated support'],
  },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto flex items-center justify-between h-16 px-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Wrench className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">DeskForge</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <Button variant="ghost" asChild>
              <Link href="/login">Sign in</Link>
            </Button>
            <Button asChild>
              <Link href="/signup">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="flex-1 flex items-center justify-center py-20 px-4 bg-gradient-to-b from-background via-background to-primary/5">
        <div className="text-center max-w-3xl mx-auto">
          <Badge variant="secondary" className="mb-4">AI-Powered Internal Tools</Badge>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
            Describe it.{' '}
            <span className="text-primary">Get it.</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Build internal tools, dashboards, and data apps by describing what you need in plain English.
            No coding required. Connect your data and share instantly.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/signup">
                Start Building Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="#features">See How It Works</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4 bg-muted/30">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">Everything you need</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              From data connection to sharing, DeskForge handles the entire workflow.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <Card key={feature.title} className="text-center">
                  <CardHeader>
                    <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                      <Icon className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 px-4">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">Simple, transparent pricing</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Start free, upgrade when you need more.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {pricingPlans.map((plan) => (
              <Card key={plan.name} className={plan.popular ? 'border-primary shadow-lg relative' : ''}>
                {plan.popular && (
                  <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">Most Popular</Badge>
                )}
                <CardHeader>
                  <CardTitle>{plan.name}</CardTitle>
                  <div className="mt-2">
                    <span className="text-3xl font-bold">{plan.price}</span>
                    {plan.price !== '$0' && <span className="text-muted-foreground">/mo</span>}
                  </div>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-primary shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Button className="w-full" variant={plan.popular ? 'default' : 'outline'} asChild>
                    <Link href="/signup">
                      {plan.price === '$0' ? 'Get Started' : 'Start Free Trial'}
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 px-4">
        <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Wrench className="h-5 w-5 text-primary" />
            <span className="font-semibold">DeskForge</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} DeskForge. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
