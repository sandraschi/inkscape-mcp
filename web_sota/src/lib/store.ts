import { create } from "zustand";

interface BackendState {
  online: boolean | null;
  lastChecked: number | null;
  setOnline: (v: boolean) => void;
}

export const useBackendStore = create<BackendState>((set) => ({
  online: null,
  lastChecked: null,
  setOnline: (v) => set({ online: v, lastChecked: Date.now() }),
}));
