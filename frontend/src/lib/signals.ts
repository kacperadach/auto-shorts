import { signal, effect, computed } from "@preact/signals-react";
import { Session } from "@supabase/supabase-js";
import { v4 as uuidv4 } from "uuid";
import { Repurposer, RepurposerRun, SocialMediaAccount } from "./types";
import { fetchRepurposerRuns, fetchRepurposers, fetchSocialMediaAccounts } from "./api";

export type AlertMessage = {
  id: string;
  message: string;
  type: "success" | "error";
  createdAt: number;
  dismissed: boolean;
};

export const alerts = signal<AlertMessage[]>([]);

export const addErrorAlert = (message: string) => {
  alerts.value = [
    {
      id: uuidv4(),
      message,
      type: "error",
      createdAt: Date.now(),
      dismissed: false,
    },
    ...alerts.value,
  ];
};

export const addSuccessAlert = (message: string) => {
  alerts.value = [
    {
      id: uuidv4(),
      message,
      type: "success",
      createdAt: Date.now(),
      dismissed: false,
    },
    ...alerts.value,
  ];
};

export const userSession = signal<Session | null>(null);
export const repurposers = signal<Repurposer[]>([]);
export const isCreatingRepurposer = signal<boolean>(false);
export const repurposerRuns = signal<RepurposerRun[]>([]);
export const repurposerMenu = signal<
  "details" | "history" | "channels" | "accounts"
>("details");
export const socialMediaAccounts = signal<SocialMediaAccount[]>([]);

export const getRepurposers = async () => {
  const response = await fetchRepurposers();
  if (response.success) {
    repurposers.value = [
      ...repurposers.value.filter(
        (r1) => !response.data.find((r2: Repurposer) => r1.id === r2.id)
      ),
      ...response.data,
    ];
  }
};

export const getSocialMediaAccounts = async () => {
  const response = await fetchSocialMediaAccounts();
  if (response.success) {
    socialMediaAccounts.value = [
      ...response.data,
      ...socialMediaAccounts.value.filter(
        (r1) => !response.data.find((r2: SocialMediaAccount) => r1.id === r2.id)
      ),
    ];
  }
};

export const getRepurposerRuns = async (repurposerId: string) => {
  const response = await fetchRepurposerRuns(repurposerId);
  if (response.success) {
    repurposerRuns.value = [
      ...repurposerRuns.value.filter(
        (r1) => !response.data.find((r2: RepurposerRun) => r1.id === r2.id)
      ),
      ...response.data,
    ];
  }
}
