/**
 * Centralized error formatting for API responses.
 * Maps backend error responses to user-friendly messages.
 */

export interface FormattedError {
  title: string;
  message: string;
}

const HTTP_STATUS_MESSAGES: Record<number, { title: string; message: string }> = {
  400: { title: 'Bad Request', message: 'The request was malformed. Please check your input and try again.' },
  401: { title: 'Unauthorized', message: 'Your session has expired. Please log in again.' },
  403: { title: 'Forbidden', message: 'You don\'t have permission to perform this action.' },
  404: { title: 'Not Found', message: 'The requested resource was not found.' },
  409: { title: 'Conflict', message: 'This action conflicts with an existing resource or state.' },
  422: { title: 'Validation Error', message: 'The data provided was invalid. Please check the fields and try again.' },
  429: { title: 'Rate Limited', message: 'Too many requests. Please wait a moment and try again.' },
  500: { title: 'Server Error', message: 'Something went wrong on our end. Please try again later.' },
  502: { title: 'Bad Gateway', message: 'The server is temporarily unavailable. Please try again later.' },
  503: { title: 'Service Unavailable', message: 'The service is temporarily unavailable. Please try again later.' },
};

const DETAIL_CODE_MESSAGES: Record<string, string> = {
  not_found: 'The requested resource was not found.',
  already_exists: 'A resource with this identifier already exists.',
  invalid_credentials: 'The email or password is incorrect.',
  token_expired: 'Your session has expired. Please log in again.',
  rate_limit_exceeded: 'Too many requests. Please wait a moment.',
  validation_error: 'The data provided was invalid. Please check the fields.',
  permission_denied: 'You don\'t have permission to perform this action.',
  internal_error: 'An unexpected error occurred. Please try again.',
  upload_failed: 'The file upload failed. Please try again.',
  ingest_error: 'Failed to process the uploaded file.',
  project_not_found: 'The project was not found or you don\'t have access to it.',
};

export function formatApiError(err: unknown): FormattedError {
  if (!err) {
    return { title: 'Unknown Error', message: 'An unexpected error occurred.' };
  }

  // Extracted Error with status
  if (typeof err === 'object' && err !== null && 'status' in err) {
    const status = (err as { status?: number }).status;
    if (status && HTTP_STATUS_MESSAGES[status]) {
      return { ...HTTP_STATUS_MESSAGES[status] };
    }
  }

  // Standard Error
  if (err instanceof Error) {
    const message = err.message;
    const lowerMessage = message.toLowerCase();

    // Match known error codes
    for (const [code, friendly] of Object.entries(DETAIL_CODE_MESSAGES)) {
      if (lowerMessage.includes(code)) {
        return { title: code.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()), message: friendly };
      }
    }

    // Check for HTTP status pattern
    const statusMatch = message.match(/HTTP (\d{3})/);
    if (statusMatch) {
      const status = parseInt(statusMatch[1], 10);
      if (HTTP_STATUS_MESSAGES[status]) {
        return { ...HTTP_STATUS_MESSAGES[status] };
      }
    }

    return { title: 'Error', message };
  }

  return { title: 'Unknown Error', message: 'An unexpected error occurred.' };
}

/**
 * Check if an error is a network/connection error.
 */
export function isNetworkError(err: unknown): boolean {
  if (err instanceof Error) {
    return err.message.includes('Failed to fetch') || err.message.includes('NetworkError') || err.message.includes('Network request failed');
  }
  return false;
}

/**
 * Check if an error is an authentication error.
 */
export function isAuthError(err: unknown): boolean {
  if (typeof err === 'object' && err !== null && 'status' in err) {
    return (err as { status?: number }).status === 401;
  }
  if (err instanceof Error) {
    return err.message.toLowerCase().includes('token') || err.message.toLowerCase().includes('unauthorized') || err.message.toLowerCase().includes('authentication');
  }
  return false;
}
