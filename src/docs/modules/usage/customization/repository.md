# Repository Customization

You can customize how TeAI works with your repository by creating a
`.teai` directory at the root level.

## Microagents
You can use microagents to extend the TeAI prompts with information
about your project and how you want TeAI to work. See
[Repository Microagents](../prompting/microagents-repo) for more information.


## Setup Script
You can add `.teai/setup.sh`, which will be run every time TeAI begins
working with your repository. This is a good place to install dependencies, set
environment variables, etc.

For example:
```bash
#!/bin/bash
export MY_ENV_VAR="my value"
sudo apt-get update
sudo apt-get install -y lsof
cd frontend && npm install ; cd ..
```
