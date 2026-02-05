export interface ApiError extends Error {
    status?: number;
    statusReasonCode?: string;
    detail?: string;
    errorBody?: unknown;
    isRetryable?: boolean;
}

export interface ApiClientConfig {
    baseUrl?: string;
    maxRetries?: number;
    retryDelay?: number;
    timeout?: number;
}

const DEFAULT_CONFIG: Required<ApiClientConfig> = {
    baseUrl: import.meta.env.VITE_API_BASE || "/api",
    maxRetries: 3,
    retryDelay: 1000,
    timeout: 30000,
};

const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504];

function isRetryableError(error: ApiError): boolean {
    if (error.status && RETRYABLE_STATUS_CODES.includes(error.status)) {
        return true;
    }
    if (error.message.includes("fetch") || error.message.includes("network")) {
        return true;
    }
    return false;
}

async function delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

export function createApiError(
    message: string,
    status?: number,
    errorBody?: unknown
): ApiError {
    const error = new Error(message) as ApiError;
    error.status = status;
    error.errorBody = errorBody;

    if (errorBody && typeof errorBody === "object") {
        const body = errorBody as Record<string, unknown>;
        error.statusReasonCode = (body.statusReasonCode || body.error) as string;
        error.detail = (body.message || body.detail) as string;
    }

    error.isRetryable = status ? RETRYABLE_STATUS_CODES.includes(status) : false;
    return error;
}

export async function fetchWithRetry<T>(
    url: string,
    options?: RequestInit,
    config?: ApiClientConfig
): Promise<T> {
    const { baseUrl, maxRetries, retryDelay, timeout } = {
        ...DEFAULT_CONFIG,
        ...config,
    };

    const fullUrl = url.startsWith("http") ? url : `${baseUrl}${url}`;
    let lastError: ApiError | null = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);

            const response = await fetch(fullUrl, {
                ...options,
                signal: controller.signal,
                headers: {
                    "Content-Type": "application/json",
                    ...options?.headers,
                },
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                let errorBody = null;
                try {
                    errorBody = await response.json();
                } catch {
                    // Ignore JSON parse errors
                }

                const error = createApiError(
                    `API Error: ${response.status} ${response.statusText}`,
                    response.status,
                    errorBody
                );

                if (isRetryableError(error) && attempt < maxRetries) {
                    lastError = error;
                    const backoffDelay = retryDelay * Math.pow(2, attempt);
                    console.warn(
                        `Request failed with ${response.status}, retrying in ${backoffDelay}ms (attempt ${attempt + 1}/${maxRetries})`
                    );
                    await delay(backoffDelay);
                    continue;
                }

                throw error;
            }

            return response.json();
        } catch (error) {
            if (error instanceof Error && error.name === "AbortError") {
                const timeoutError = createApiError("Request timeout", 408);
                if (attempt < maxRetries) {
                    lastError = timeoutError;
                    const backoffDelay = retryDelay * Math.pow(2, attempt);
                    console.warn(
                        `Request timed out, retrying in ${backoffDelay}ms (attempt ${attempt + 1}/${maxRetries})`
                    );
                    await delay(backoffDelay);
                    continue;
                }
                throw timeoutError;
            }

            if (error instanceof Error && !("status" in error)) {
                const networkError = createApiError(
                    `Network error: ${error.message}`
                );
                networkError.isRetryable = true;

                if (attempt < maxRetries) {
                    lastError = networkError;
                    const backoffDelay = retryDelay * Math.pow(2, attempt);
                    console.warn(
                        `Network error, retrying in ${backoffDelay}ms (attempt ${attempt + 1}/${maxRetries})`
                    );
                    await delay(backoffDelay);
                    continue;
                }
                throw networkError;
            }

            throw error;
        }
    }

    throw lastError || createApiError("Max retries exceeded");
}

export function formatApiError(error: unknown): string {
    if (error instanceof Error) {
        const apiError = error as ApiError;
        if (apiError.statusReasonCode) {
            return `${apiError.statusReasonCode}: ${apiError.detail || apiError.message}`;
        }
        if (apiError.detail) {
            return apiError.detail;
        }
        return apiError.message;
    }
    return "An unexpected error occurred";
}

export function getErrorSeverity(
    error: unknown
): "warning" | "error" | "critical" {
    if (error instanceof Error) {
        const apiError = error as ApiError;
        if (apiError.isRetryable) {
            return "warning";
        }
        if (apiError.status && apiError.status >= 500) {
            return "critical";
        }
    }
    return "error";
}
