import { useState } from "react";
import { useAuthStore } from "../store/authStore";
import { API_BASE } from "../api/client";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "₹0",
    period: "forever",
    badge: null,
    features: ["3 compliance audits / month", "10 Q&A queries / month", "DPDP 2023 rules", "Indian Contract Act rules", "PDF & DOCX support"],
    cta: "Current Plan",
    disabled: true,
  },
  {
    id: "pro",
    name: "Pro",
    price: "₹999",
    period: "per month",
    badge: "Most Popular",
    features: ["50 compliance audits / month", "Unlimited Q&A queries", "Multilingual Q&A", "Priority processing", "Export reports as PDF"],
    cta: "Upgrade to Pro",
    disabled: false,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "₹4,999",
    period: "per month",
    badge: null,
    features: ["Unlimited audits", "Unlimited Q&A", "Admin dashboard", "Team management", "Dedicated support", "Custom rule sets"],
    cta: "Upgrade to Enterprise",
    disabled: false,
  },
];

declare global {
  interface Window {
    Razorpay: new (options: Record<string, unknown>) => { open: () => void };
  }
}

export default function PricingPage() {
  const { token, user } = useAuthStore();
  const [loading, setLoading] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  async function handleUpgrade(planId: string) {
    if (!token) {
      window.location.href = "/signup";
      return;
    }
    setLoading(planId);
    setMessage("");

    try {
      // Create Razorpay order
      const orderRes = await fetch(`${API_BASE}/api/payments/create-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ plan: planId }),
      });
      if (!orderRes.ok) {
        const err = await orderRes.json();
        throw new Error(err.detail || "Failed to create order");
      }
      const order = await orderRes.json();

      // Load Razorpay script if not present
      if (!window.Razorpay) {
        await new Promise<void>((resolve) => {
          const script = document.createElement("script");
          script.src = "https://checkout.razorpay.com/v1/checkout.js";
          script.onload = () => resolve();
          document.body.appendChild(script);
        });
      }

      // Open Razorpay checkout
      const rzp = new window.Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: "LexAudit",
        description: `Upgrade to ${planId} plan`,
        order_id: order.order_id,
        prefill: { email: user?.email },
        theme: { color: "#6366f1" },
        handler: async (response: Record<string, string>) => {
          // Verify payment
          const verifyRes = await fetch(`${API_BASE}/api/payments/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              plan: planId,
            }),
          });
          if (verifyRes.ok) {
            setMessage(`🎉 Successfully upgraded to ${planId} plan!`);
          } else {
            setMessage("⚠️ Payment verification failed. Contact support.");
          }
        },
      });
      rzp.open();
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(null);
    }
  }

  const currentPlan = user?.plan ?? "free";

  return (
    <div className="pricing-page">
      <div className="pricing-hero">
        <h1>Simple, Transparent Pricing</h1>
        <p>Start free. Upgrade when you need more.</p>
      </div>

      {message && <div className="pricing-message">{message}</div>}

      <div className="pricing-grid">
        {PLANS.map((plan) => (
          <div
            key={plan.id}
            className={`pricing-card ${plan.badge ? "pricing-card--featured" : ""} ${currentPlan === plan.id ? "pricing-card--current" : ""}`}
          >
            {plan.badge && <div className="pricing-badge">{plan.badge}</div>}
            <div className="pricing-header">
              <h2>{plan.name}</h2>
              <div className="pricing-price">
                <span className="price-amount">{plan.price}</span>
                <span className="price-period">/{plan.period}</span>
              </div>
            </div>
            <ul className="pricing-features">
              {plan.features.map((f) => (
                <li key={f}>
                  <span className="feature-check">✓</span> {f}
                </li>
              ))}
            </ul>
            <button
              className={`btn-pricing ${plan.badge ? "btn-primary" : "btn-secondary"}`}
              disabled={plan.disabled || currentPlan === plan.id || loading === plan.id}
              onClick={() => handleUpgrade(plan.id)}
            >
              {currentPlan === plan.id
                ? "Current Plan"
                : loading === plan.id
                ? "Processing…"
                : plan.cta}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
