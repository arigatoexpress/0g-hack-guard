export type NativePreflightDecision = "allow" | "review" | "deny";

export type NativePreflightPayload = {
  surface: string;
  operation: string;
  chain?: string;
  sourceProject?: string;
  liveSigning?: boolean;
  target?: string;
  messageHex?: string;
  intentText?: string;
  intent?: Record<string, unknown>;
  config?: Record<string, unknown>;
};

export type NativePreflightResult = {
  schema: "0guard.native_preflight.v1";
  decision: NativePreflightDecision;
  receipt?: {
    hash?: string;
    algorithm?: string;
    zeroGChainReady?: boolean;
    zeroGStorageReady?: boolean;
  };
  recommendedNextStep?: string;
  safety?: Record<string, boolean>;
};

export async function nativePreflight(
  baseUrl: string,
  payload: NativePreflightPayload,
): Promise<NativePreflightResult> {
  const response = await fetch(`${baseUrl.replace(/\/$/, "")}/api/native-preflight`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`0guard preflight failed with HTTP ${response.status}`);
  }
  return (await response.json()) as NativePreflightResult;
}

export async function requireReceiptBeforeSign<T>(
  baseUrl: string,
  payload: NativePreflightPayload,
  continueWithAppSigner: (preflightedPayload: NativePreflightPayload) => Promise<T>,
): Promise<T> {
  const result = await nativePreflight(baseUrl, payload);
  if (result.decision !== "allow") {
    throw new Error(
      `0guard blocked signer access: ${result.decision} ${result.receipt?.hash ?? ""}`,
    );
  }
  return continueWithAppSigner(payload);
}

export const readOnlyBaseStatusPayload: NativePreflightPayload = {
  surface: "evm",
  operation: "read_status",
  chain: "eip155:8453",
  intent: { mode: "preview" },
};
