"use client";
import { useState } from "react";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_BASE;

interface Claim {
  id: number;
  transcript: string;
  extracted: Record<string, any>;
  classification: Record<string, any>;
  suggestions: Record<string, any>;
  status: string;
  similar: Array<Record<string, any>>;
}

export default function Home() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [claim, setClaim] = useState<Claim | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${API}/claims/`, { transcript: text });
      setClaim(res.data);
    } catch (e: any) {
      setError(e?.message || "Failed to analyze claim");
    } finally {
      setLoading(false);
    }
  };

  const doAction = async (action: "approve" | "deny" | "escalate") => {
    if (!claim) return;
    try {
      await axios.post(`${API}/claims/${claim.id}/action/`, { action });
      const newStatus =
        action === "approve"
          ? "approved"
          : action === "deny"
          ? "denied"
          : "escalated";
      setClaim({ ...claim, status: newStatus });
    } catch (e: any) {
      setError(e?.message || "Failed to perform action");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved":
        return "bg-green-100 text-green-800 border-green-300";
      case "denied":
        return "bg-red-100 text-red-800 border-red-300";
      case "escalated":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "analysed":
        return "bg-blue-100 text-blue-800 border-blue-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getClassificationColor = (label: string) => {
    switch (label) {
      case "valid":
        return "bg-green-500";
      case "invalid":
        return "bg-orange-500";
      case "fraudulent":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <main className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2 py-6">
        <h1 className="text-4xl font-bold text-gray-900">
          Avallon Claims Simulator
        </h1>
        <p className="text-gray-600">
          AI-powered voice claim processing with entity extraction, fraud
          detection, and similarity matching
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
        <label className="block">
          <span className="text-gray-700 font-semibold">
            Claim Transcript (Voice Input Proxy)
          </span>
          <textarea
            className="mt-2 w-full min-h-[160px] border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Paste transcribed call here... e.g., 'Hi, this is Aigerim. My policy number is KZ-AUTO-99812. I was rear-ended on September 2, 2024...'"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </label>
        <button
          onClick={submit}
          disabled={loading || !text.trim()}
          className="w-full px-6 py-3 rounded-lg bg-black text-white font-semibold hover:bg-gray-800 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
        >
          {loading ? "Analyzing..." : "Analyze Claim"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {claim && (
        <section className="space-y-4">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">
                Analysis Results
              </h2>
              <span
                className={`text-sm px-3 py-1 border rounded-full font-medium ${getStatusColor(
                  claim.status
                )}`}
              >
                Status: {claim.status}
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-2">
                <h3 className="font-bold text-lg text-gray-800">
                  Extracted Fields
                </h3>
                <pre className="text-sm bg-gray-50 border border-gray-200 p-4 rounded-lg overflow-auto max-h-80">
                  {JSON.stringify(claim.extracted, null, 2)}
                </pre>
              </div>

              <div className="space-y-2">
                <h3 className="font-bold text-lg text-gray-800 flex items-center gap-2">
                  Classification
                  {claim.classification.label && (
                    <span
                      className={`inline-block w-3 h-3 rounded-full ${getClassificationColor(
                        claim.classification.label
                      )}`}
                    />
                  )}
                </h3>
                <pre className="text-sm bg-gray-50 border border-gray-200 p-4 rounded-lg overflow-auto max-h-80">
                  {JSON.stringify(claim.classification, null, 2)}
                </pre>
              </div>
            </div>

            {claim.similar && claim.similar.length > 0 && (
              <div className="mt-6 space-y-2">
                <h3 className="font-bold text-lg text-gray-800">
                  Similar Past Cases
                </h3>
                <div className="space-y-2">
                  {claim.similar.map((sim, idx) => (
                    <div
                      key={idx}
                      className="bg-gray-50 border border-gray-200 p-3 rounded-lg"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <span className="font-mono text-xs text-gray-500">
                            {sim.id}
                          </span>
                          <p className="text-sm text-gray-700 mt-1">
                            {sim.preview}
                          </p>
                        </div>
                        <div className="ml-4 text-right">
                          <div className="text-xs font-semibold text-blue-600">
                            {(sim.similarity * 100).toFixed(1)}%
                          </div>
                          <div className="text-xs text-gray-500">
                            {sim.label}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="font-bold text-lg text-gray-800 mb-3">
                Actions
              </h3>
              <div className="flex gap-3">
                <button
                  className="px-4 py-2 border border-green-500 text-green-700 rounded-lg hover:bg-green-50 font-medium transition"
                  onClick={() => doAction("approve")}
                >
                  Approve
                </button>
                <button
                  className="px-4 py-2 border border-red-500 text-red-700 rounded-lg hover:bg-red-50 font-medium transition"
                  onClick={() => doAction("deny")}
                >
                  Deny
                </button>
                <button
                  className="px-4 py-2 border border-yellow-500 text-yellow-700 rounded-lg hover:bg-yellow-50 font-medium transition"
                  onClick={() => doAction("escalate")}
                >
                  Escalate
                </button>
              </div>
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
