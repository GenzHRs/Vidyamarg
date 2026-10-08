"use client";
import React, { useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "@/store/authStore";

function SessionQueries({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: {
    staleTime: 30000, gcTime: 300000, refetchOnWindowFocus: false,
  } } }));
  useEffect(() => () => { client.clear(); }, [client]);
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

export default function Providers({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(state => state.token);
  useEffect(() => { localStorage.removeItem("REACT_QUERY_OFFLINE_CACHE"); }, []);
  return <SessionQueries key={token || "anonymous"}>{children}</SessionQueries>;
}
