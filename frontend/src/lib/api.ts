const apiUrl = process.env.REACT_APP_API_URL;

export type ApiResponse = Promise<{
  success: boolean;
  data?: any;
  error?: string;
}>;

async function makeRequest(
  url: string,
  method: string = "GET",
  body?: any,
  headers?: any
): Promise<ApiResponse> {
  const allHeaders =
    headers !== undefined
      ? headers
      : {
          "Content-Type": "application/json",
        };
  //   if (userSession.value) {
  //     allHeaders["Authorization"] = `Bearer ${userSession.value.access_token}`;
  //   }

  let response = await fetch(url, {
    method,
    headers: allHeaders,
    body,
  });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 403 && data.detail === "Limit exceeded") {
      //   showSubscriptionDialog.value = true;
    } else {
      //   addErrorAlert(data?.detail);
    }
    return {
      success: false,
      error: response.statusText,
    };
  }

  return {
    success: true,
    data,
  };
}

export async function initiate_oauth(): Promise<ApiResponse> {
  return await makeRequest(`${apiUrl}/oauth/login`);
}

export async function initiate_oauth_facebook(): Promise<ApiResponse> {
  return await makeRequest(`${apiUrl}/facebook/oauth/login`);
}

