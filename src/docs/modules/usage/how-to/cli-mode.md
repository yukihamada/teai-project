# CLI Mode

TeAI can be run in an interactive CLI mode, which allows users to start an interactive session via the command line.

This mode is different from the [headless mode](headless-mode), which is non-interactive and better for scripting.

## With Python

To start an interactive TeAI session via the command line:

1. Ensure you have followed the [Development setup instructions](https://github.com/All-Hands-AI/TeAI/blob/main/Development.md).
2. Run the following command:

```bash
poetry run python -m teai.core.cli
```

This command will start an interactive session where you can input tasks and receive responses from TeAI.

You'll need to be sure to set your model, API key, and other settings via environment variables
[or the `config.toml` file](https://github.com/All-Hands-AI/TeAI/blob/main/config.template.toml).

## With Docker

To run TeAI in CLI mode with Docker:

1. Set the following environmental variables in your terminal:

- `WORKSPACE_BASE` to the directory you want TeAI to edit (Ex: `export WORKSPACE_BASE=$(pwd)/workspace`).
- `LLM_MODEL` to the model to use (Ex: `export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`).
- `LLM_API_KEY` to the API key (Ex: `export LLM_API_KEY="sk_test_12345"`).

2. Run the following Docker command:

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.30-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.teai-state:/.teai-state \
    --add-host host.docker.internal:host-gateway \
    --name teai-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/teai:0.30 \
    python -m teai.core.cli
```

This command will start an interactive session in Docker where you can input tasks and receive responses from TeAI.

## Examples of CLI Commands and Expected Outputs

Here are some examples of CLI commands and their expected outputs:

### Example 1: Simple Task

```bash
>> Write a Python script that prints "Hello, World!"
```

Expected Output:

```bash
🤖 Sure! Here is a Python script that prints "Hello, World!":

❯ print("Hello, World!")
```

### Example 2: Bash Command

```bash
>> Create a directory named "test_dir"
```

Expected Output:

```bash
🤖 Creating a directory named "test_dir":

❯ mkdir test_dir
```

### Example 3: Error Handling

```bash
>> Delete a non-existent file
```

Expected Output:

```bash
🤖 An error occurred. Please try again.
```
