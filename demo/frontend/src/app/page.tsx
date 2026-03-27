"use client";

import { useState, useEffect, useCallback } from "react";

const API = "http://localhost:8000";

const PIZZA_MENU = [
  { name: "Pepperoni", price: 18, emoji: "🍕" },
  { name: "Margherita", price: 15, emoji: "🧀" },
  { name: "BBQ Chicken", price: 22, emoji: "🍗" },
  { name: "Hawaiian", price: 17, emoji: "🍍" },
];

const STAGES = ["received", "charging", "kitchen", "delivering", "complete"];

const STAGE_LABELS: Record<string, string> = {
  received: "Order Received",
  charging: "Payment Processing",
  kitchen: "In the Kitchen",
  delivering: "Out for Delivery",
  complete: "Delivered!",
  failed: "Failed",
  unknown: "...",
};

const STAGE_ICONS: Record<string, string> = {
  received: "📋",
  charging: "💳",
  kitchen: "👨‍🍳",
  delivering: "🛵",
  complete: "✅",
  failed: "❌",
  unknown: "⏳",
};

interface Order {
  workflow_id: string;
  customer_name: string;
  pizza_type: string;
  address: string;
  amount: number;
  stage: string;
  status: string;
}

interface ChargeEntry {
  line: string;
  amount: number;
  order_id: string | null;
}

interface ChargesData {
  entries: ChargeEntry[];
  total: number;
  count: number;
}

function StageProgress({ currentStage }: { currentStage: string }) {
  const currentIdx = STAGES.indexOf(currentStage);
  return (
    <div className="flex items-center gap-1 mt-3">
      {STAGES.map((stage, i) => {
        const isActive = i <= currentIdx && currentIdx >= 0;
        const isCurrent = stage === currentStage;
        return (
          <div key={stage} className="flex items-center gap-1 flex-1">
            <div className="flex flex-col items-center flex-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all duration-500 ${
                  isCurrent
                    ? "bg-orange-500 text-white scale-110 shadow-lg shadow-orange-200"
                    : isActive
                    ? "bg-green-500 text-white"
                    : "bg-stone-200 text-stone-400"
                }`}
              >
                {isActive ? STAGE_ICONS[stage] : i + 1}
              </div>
              <span
                className={`text-[10px] mt-1 text-center leading-tight ${
                  isCurrent
                    ? "text-orange-600 font-semibold"
                    : isActive
                    ? "text-green-600"
                    : "text-stone-400"
                }`}
              >
                {STAGE_LABELS[stage]}
              </span>
            </div>
            {i < STAGES.length - 1 && (
              <div
                className={`h-0.5 w-full min-w-2 mt-[-16px] transition-colors duration-500 ${
                  i < currentIdx ? "bg-green-400" : "bg-stone-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function OrderCard({ order }: { order: Order }) {
  const isFailed = order.stage === "failed";
  const isComplete = order.stage === "complete";

  return (
    <div
      className={`rounded-xl border p-4 transition-all duration-300 ${
        isFailed
          ? "border-red-300 bg-red-50"
          : isComplete
          ? "border-green-300 bg-green-50"
          : "border-orange-200 bg-white shadow-sm"
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-stone-900">
            {order.customer_name}
          </h3>
          <p className="text-sm text-stone-500 font-mono">
            {order.workflow_id}
          </p>
        </div>
        <span
          className={`text-xs font-medium px-2.5 py-1 rounded-full ${
            isFailed
              ? "bg-red-100 text-red-700"
              : isComplete
              ? "bg-green-100 text-green-700"
              : "bg-orange-100 text-orange-700 animate-pulse"
          }`}
        >
          {STAGE_ICONS[order.stage] || "⏳"} {STAGE_LABELS[order.stage] || order.stage}
        </span>
      </div>
      {!isFailed && <StageProgress currentStage={order.stage} />}
    </div>
  );
}

function ChargeLedger({ charges }: { charges: ChargesData }) {
  if (charges.entries.length === 0) return null;

  const hasDuplicates = charges.entries.some((e) => !e.order_id);
  const uniqueOrderIds = new Set(charges.entries.filter((e) => e.order_id).map((e) => e.order_id));
  const expectedTotal = charges.entries.length > 0
    ? (uniqueOrderIds.size > 0 ? charges.entries.filter((e) => e.order_id).reduce((sum, e, _, arr) => {
        const first = arr.find((a) => a.order_id === e.order_id);
        return first === e ? sum + e.amount : sum;
      }, 0) : charges.entries[0].amount)
    : 0;
  const overcharged = hasDuplicates && charges.count > 1;

  return (
    <div className={`rounded-2xl border p-5 transition-all ${
      overcharged ? "border-red-300 bg-red-50" : "border-stone-200 bg-white shadow-sm"
    }`}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-bold text-stone-900">
          Payment Ledger
        </h2>
        {overcharged && (
          <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-red-100 text-red-700 animate-pulse">
            DUPLICATE CHARGES
          </span>
        )}
      </div>

      <div className="space-y-1.5 mb-3">
        {charges.entries.map((entry, i) => (
          <div
            key={i}
            className={`flex items-center justify-between text-sm px-3 py-2 rounded-lg ${
              !entry.order_id
                ? "bg-red-100 text-red-800 border border-red-200"
                : "bg-stone-50 text-stone-700"
            }`}
          >
            <span className="font-mono text-xs flex-1 truncate mr-2">
              {entry.order_id
                ? `Order ${entry.order_id.slice(0, 8)}...`
                : `Charge #${i + 1} (no order ID)`}
            </span>
            <span className="font-semibold tabular-nums">${entry.amount}</span>
          </div>
        ))}
      </div>

      <div className={`flex items-center justify-between pt-3 border-t text-sm font-bold ${
        overcharged ? "border-red-200 text-red-700" : "border-stone-200 text-stone-900"
      }`}>
        <span>Total Charged</span>
        <span className="tabular-nums text-base">
          ${charges.total}
          {overcharged && (
            <span className="text-xs font-normal ml-1.5 text-red-500">
              (should be ${expectedTotal})
            </span>
          )}
        </span>
      </div>
    </div>
  );
}

export default function Home() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [charges, setCharges] = useState<ChargesData>({ entries: [], total: 0, count: 0 });
  const [customerName, setCustomerName] = useState("");
  const [pizzaType, setPizzaType] = useState(PIZZA_MENU[0].name);
  const [address, setAddress] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const fetchOrders = useCallback(async () => {
    try {
      const res = await fetch(`${API}/orders`);
      if (res.ok) {
        setOrders(await res.json());
      }
    } catch {
      // backend not ready yet
    }
  }, []);

  const fetchCharges = useCallback(async () => {
    try {
      const res = await fetch(`${API}/charges`);
      if (res.ok) {
        setCharges(await res.json());
      }
    } catch {
      // backend not ready yet
    }
  }, []);

  useEffect(() => {
    fetchOrders();
    fetchCharges();
    const interval = setInterval(() => {
      fetchOrders();
      fetchCharges();
    }, 2000);
    return () => clearInterval(interval);
  }, [fetchOrders, fetchCharges]);

  const selectedPizza = PIZZA_MENU.find((p) => p.name === pizzaType)!;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const res = await fetch(`${API}/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_name: customerName,
          pizza_type: pizzaType,
          address,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to place order");
      }

      setCustomerName("");
      setAddress("");
      fetchOrders();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  const activeOrders = orders.filter(
    (o) => o.stage !== "complete" && o.stage !== "failed"
  );
  const completedOrders = orders.filter(
    (o) => o.stage === "complete" || o.stage === "failed"
  );

  return (
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <header className="bg-orange-600 text-white py-4 px-6 shadow-md">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold tracking-tight">
            🍕 Temporal Pizza Co.
          </h1>
          <span className="text-orange-200 text-sm font-mono">
            Powered by Temporal
          </span>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full p-6 grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-8">
        {/* Order Form + Charge Ledger */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-stone-200 shadow-sm p-6">
            <h2 className="text-lg font-bold text-stone-900 mb-4">
              Place an Order
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-stone-700 mb-1">
                  Your Name
                </label>
                <input
                  type="text"
                  required
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Alice"
                  className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700 mb-1">
                  Pizza
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {PIZZA_MENU.map((pizza) => (
                    <button
                      key={pizza.name}
                      type="button"
                      onClick={() => setPizzaType(pizza.name)}
                      className={`rounded-lg border p-3 text-left text-sm transition-all ${
                        pizzaType === pizza.name
                          ? "border-orange-500 bg-orange-50 ring-2 ring-orange-500"
                          : "border-stone-200 hover:border-stone-300"
                      }`}
                    >
                      <span className="text-lg">{pizza.emoji}</span>
                      <div className="font-medium text-stone-900">
                        {pizza.name}
                      </div>
                      <div className="text-stone-500">${pizza.price}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700 mb-1">
                  Delivery Address
                </label>
                <input
                  type="text"
                  required
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="123 Main Street"
                  className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
              </div>

              {error && (
                <p className="text-red-600 text-sm bg-red-50 rounded-lg p-2">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-orange-600 text-white font-semibold rounded-lg py-2.5 hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting
                  ? "Placing order..."
                  : `Order ${selectedPizza.emoji} ${selectedPizza.name} — $${selectedPizza.price}`}
              </button>
            </form>
          </div>

          {/* Payment Ledger */}
          <ChargeLedger charges={charges} />
        </div>

        {/* Order Tracker */}
        <div className="space-y-6">
          {/* Active Orders */}
          <div>
            <h2 className="text-lg font-bold text-stone-900 mb-3">
              Active Orders{" "}
              {activeOrders.length > 0 && (
                <span className="text-orange-500 font-mono text-sm ml-1">
                  ({activeOrders.length})
                </span>
              )}
            </h2>
            {activeOrders.length === 0 ? (
              <div className="text-stone-400 text-sm bg-white rounded-xl border border-dashed border-stone-300 p-8 text-center">
                No active orders. Place one to get started!
              </div>
            ) : (
              <div className="space-y-3">
                {activeOrders.map((order) => (
                  <OrderCard key={order.workflow_id} order={order} />
                ))}
              </div>
            )}
          </div>

          {/* Completed Orders */}
          {completedOrders.length > 0 && (
            <div>
              <h2 className="text-lg font-bold text-stone-900 mb-3">
                Completed
              </h2>
              <div className="space-y-3">
                {completedOrders.map((order) => (
                  <OrderCard key={order.workflow_id} order={order} />
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
