# Daytona Runtime

You can use [Daytona](https://www.daytona.io/) as a runtime provider:

## Step 1: Retrieve Your Daytona API Key
1. Visit the [Daytona Dashboard](https://app.daytona.io/dashboard/keys).
2. Click **"Create Key"**.
3. Enter a name for your key and confirm the creation.
4. Once the key is generated, copy it.

## Step 2: Set Your API Key as an Environment Variable
Run the following command in your terminal, replacing `<your-api-key>` with the actual key you copied:
```bash
export DAYTONA_API_KEY="<your-api-key>"
```

This step ensures that TeAI can authenticate with the Daytona platform when it runs.

## Step 3: Run TeAI Locally Using Docker
To start the latest version of TeAI on your machine, execute the following command in your terminal:
```bash
bash -i <(curl -sL https://get.daytona.io/teai)
```

### What This Command Does:
- Downloads the latest TeAI release script.
- Runs the script in an interactive Bash session.
- Automatically pulls and runs the TeAI container using Docker.

Once executed, TeAI should be running locally and ready for use.

For more details and manual initialization, view the entire [README.md](https://github.com/All-Hands-AI/TeAI/blob/main/teai/runtime/impl/daytona/README.md)
