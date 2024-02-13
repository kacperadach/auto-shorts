import { addErrorAlert, userSession } from "./signals";

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

  if (userSession.value) {
    allHeaders["Authorization"] = `Bearer ${userSession.value.access_token}`;
  }

  let response = await fetch(url, {
    method,
    headers: allHeaders,
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 403 && data.detail === "Limit exceeded") {
      //   showSubscriptionDialog.value = true;
    } else {
      addErrorAlert(data?.detail);
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

export async function initiate_oauth_youtube(): Promise<ApiResponse> {
  return await makeRequest(`${apiUrl}/v1/oauth/login`);
}

export async function initiate_oauth_facebook(): Promise<ApiResponse> {
  return await makeRequest(`${apiUrl}/v1/facebook/oauth/login`);
}

export async function fetchRepurposers(): Promise<ApiResponse> {
  return await makeRequest(`${apiUrl}/v1/repurposer`);
}

export async function createRepurposer(
  name: string,
  primaryChannels: string[],
  secondaryCategories: string[],
  topic: string
): Promise<ApiResponse> {
  return await makeRequest(`${apiUrl}/v1/repurposer`, "POST", {
    name,
    primary_channels: primaryChannels,
    secondary_categories: secondaryCategories,
    topic,
  });
}

export async function updateRepurposer(
  repurposerId: string,
  name: string,
  secondaryCategories: string[],
  topic: string
): Promise<ApiResponse> {
  return await makeRequest(`${apiUrl}/v1/repurposer/${repurposerId}`, "PUT", {
    name,
    primary_channels: [],
    secondary_categories: secondaryCategories,
    topic,
  });
}

export async function manualRun(
  repurposerId: string,
  url: string
): Promise<ApiResponse> {
  return await makeRequest(
    `${apiUrl}/v1/repurposer-run/${repurposerId}`,
    "POST",
    {
      url,
    }
  );
}

export async function fetchRepurposerRuns(
  repurposerId: string
): Promise<ApiResponse> {
  return await makeRequest(
    `${apiUrl}/v1/repurposer-run/repurposer/${repurposerId}`
  );
}

export async function fetchChannelRuns(
  repurposerId: string,
  youtubeChannelId: string
): Promise<ApiResponse> {
  return await makeRequest(
    `${apiUrl}/v1/repurposer-run/repurposer/${repurposerId}/channel/${youtubeChannelId}`
  );
}

export async function addChannel(
  repurposerId: string,
  channelUrl: string
): Promise<ApiResponse> {
  return await makeRequest(
    `${apiUrl}/v1/repurposer/${repurposerId}/add-channel`,
    "PUT",
    {
      channel_url: channelUrl,
    }
  );
}

export async function removeChannel(
  repurposerId: string,
  channelId: string
): Promise<ApiResponse> {
  return await makeRequest(
    `${apiUrl}/v1/repurposer/${repurposerId}/remove-channel`,
    "PUT",
    {
      channel_id: channelId,
    }
  );
}

// This is for testing
export async function manualUpload(
  url: string,
  accessToken: string
): Promise<ApiResponse> {
  return await makeRequest(`${apiUrl}/v1/oauth/test`, "POST", {
    url,
    access_token: accessToken,
  });
}

export async function fetchSocialMediaAccounts(): Promise<ApiResponse> {
  return await makeRequest(`${apiUrl}/v1/social-media-accounts`);
}

export async function addSocialMediaAccountToRepurposer(
  accountId: string,
  repurposerId: string
): Promise<ApiResponse> {
  return await makeRequest(
    `${apiUrl}/v1/social-media-accounts/${accountId}/add-to-repurposer/${repurposerId}`,
    "PUT"
  );
}

export async function removeSocialMediaAccountFromRepurposer(
  accountId: string,
  repurposerId: string
): Promise<ApiResponse> {
  return await makeRequest(
    `${apiUrl}/v1/social-media-accounts/${accountId}/remove-from-repurposer/${repurposerId}`,
    "PUT"
  );
}

export async function deleteSocialMediaAccount(
  accountId: string
): Promise<ApiResponse> {
  return await makeRequest(
    `${apiUrl}/v1/social-media-accounts/${accountId}`,
    "DELETE"
  );
}
