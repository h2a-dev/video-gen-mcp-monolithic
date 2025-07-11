# YouTube Integration Setup Guide

## Overview

The Video Agent MCP server supports YouTube integration for both searching/analyzing videos and uploading videos. These features use different authentication methods:

- **Search/Analysis**: Requires YouTube Data API v3 key
- **Upload**: Requires OAuth2 authentication

## YouTube Upload Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Note your project ID for later reference

### 2. Enable YouTube Data API v3

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "Enable"

### 3. Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" for user type
   - Fill in required fields (app name, support email)
   - Add your email to test users
   - You can skip optional fields for testing
4. For Application type, select "Desktop app"
5. Give it a name (e.g., "Video Agent MCP")
6. Click "Create"

### 4. Download Credentials

1. After creating the OAuth client, click the download button (⬇️)
2. Save the file as `client_secrets.json`
3. Place it in the project root directory (same folder as `main.py`)

### 5. First-Time Authentication

When you first use the `youtube_publish` tool:

1. The server will open your default web browser
2. Log in to your Google account
3. Review the permissions requested:
   - Upload videos to YouTube
   - Manage your YouTube videos
4. Click "Allow" to grant permissions
5. The browser will show "The authentication flow has completed"
6. A `token.json` file will be created for future use

### 6. Using YouTube Upload

Once set up, you can use the `youtube_publish` tool:

```
youtube_publish(
    project_id="your-project-id",
    title="Your Video Title",
    description="Your video description",
    tags=["tag1", "tag2"],
    category_id="22",  # People & Blogs
    privacy_status="private"  # or "public", "unlisted"
)
```

## YouTube Search Setup (Optional)

If you also want to use YouTube search and analysis features:

1. Create an API key in Google Cloud Console:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API key"
   - Copy the API key
2. Set the environment variable:
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```
   Or add to your `.env` file:
   ```
   GOOGLE_API_KEY=your-api-key-here
   ```

## Troubleshooting

### "Client secrets file not found"
- Ensure `client_secrets.json` is in the project root directory
- Check the file is named exactly `client_secrets.json` (not `client_secret.json` or other variations)

### "Invalid client secrets file"
- Make sure you downloaded the correct file from Google Cloud Console
- The file should be a JSON file starting with `{"installed":` or `{"web":`

### "Access blocked: Authorization Error"
- Ensure your OAuth consent screen is configured
- Add your email to the test users list
- If your app is in production, it needs to be verified by Google

### Token Expiration
- If uploads stop working after some time, delete `token.json` and re-authenticate
- The OAuth2 tokens are automatically refreshed, but sometimes manual re-auth is needed

## Security Notes

- Never commit `client_secrets.json` or `token.json` to version control
- Add both files to your `.gitignore`
- Keep your credentials secure and rotate them if compromised
- Use "private" privacy status for testing before making videos public