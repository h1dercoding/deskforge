"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { api } from "@/lib/api";

interface UsageData {
  tools: { used: number; limit: number | null };
  members: { used: number; limit: number | null };
  datasources: { used: number; limit: number | null };
}

const PLANS = [
  { id: "starter", name: "Starter", price: "$49/mo", features: ["Unlimited tools", "Unlimited members", "5 data sources"] },
  { id: "pro", name: "Pro", price: "$149/mo", features: ["Everything in Starter", "Unlimited data sources", "Custom theming", "90-day audit log"] },
  { id: "enterprise", name: "Enterprise", price: "$499/mo", features: ["Everything in Pro", "365-day audit log", "Priority support", "SLA"] },
];

export default function BillingPage() {
  const [plan, setPlan] = useState("free");
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/billing/subscription").then((r) => r.data),
      api.get("/billing/usage").then((r) => r.data),
    ]).then(([sub, u]) => {
      setPlan(sub.plan || "free");
      setUsage(u);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleUpgrade = async (planId: string) => {
    try {
      const res = await api.post("/billing/checkout", { plan: planId });
      if (res.data.checkout_url) window.location.href = res.data.checkout_url;
    } catch (e) {
      console.error("Checkout failed:", e);
    }
  };

  const handlePortal = async () => {
    const res = await api.post("/billing/portal");
    if (res.data.portal_url) window.location.href = res.data.portal_url;
  };

  if (loading) return <LoadingSpinner message="Loading billing..." />;

  return (
    <div className="max-w-4xl space-y-8">
      <h1 className="text-2xl font-bold">Billing & Usage</h1>

      <Card>
        <CardHeader>
          <CardTitle>Current Plan: <Badge className="ml-2">{plan.toUpperCase()}</Badge></CardTitle>
          {plan !== "free" && <Button variant="outline" size="sm" onClick={handlePortal} className="mt-2">Manage Subscription</Button>}
        </CardHeader>
        {usage && (
          <CardContent className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold">{usage.tools.used}</p>
              <p className="text-sm text-gray-500">Tools {usage.tools.limit ? `/ ${usage.tools.limit}` : ""}</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold">{usage.members.used}</p>
              <p className="text-sm text-gray-500">Members {usage.members.limit ? `/ ${usage.members.limit}` : ""}</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold">{usage.datasources.used}</p>
              <p className="text-sm text-gray-500">Data Sources {usage.datasources.limit ? `/ ${usage.datasources.limit}` : ""}</p>
            </div>
          </CardContent>
        )}
      </Card>

      {plan === "free" && (
        <div className="grid md:grid-cols-3 gap-6">
          {PLANS.map((p) => (
            <Card key={p.id} className={p.id === "pro" ? "border-blue-500 shadow-lg" : ""}>
              <CardHeader>
                <CardTitle>{p.name}</CardTitle>
                <CardDescription className="text-2xl font-bold">{p.price}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <ul className="space-y-2">
                  {p.features.map((f) => (
                    <li key={f} className="text-sm flex items-center gap-2">
                      <span className="text-green-500">✓</span> {f}
                    </li>
                  ))}
                </ul>
                <Button className="w-full" variant={p.id === "pro" ? "default" : "outline"} onClick={() => handleUpgrade(p.id)}>
                  Upgrade
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
