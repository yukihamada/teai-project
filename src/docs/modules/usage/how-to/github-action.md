# Using the TeAI GitHub Action

This guide explains how to use the TeAI GitHub Action, both within the TeAI repository and in your own projects.

## Using the Action in the TeAI Repository

To use the TeAI GitHub Action in a repository, you can:

1. Create an issue in the repository.
2. Add the `fix-me` label to the issue or leave a comment on the issue starting with `@teai-agent`.

The action will automatically trigger and attempt to resolve the issue.

## Installing the Action in a New Repository

To install the TeAI GitHub Action in your own repository, follow
the [README for the TeAI Resolver](https://github.com/All-Hands-AI/TeAI/blob/main/teai/resolver/README.md).

## Usage Tips

### Iterative resolution

1. Create an issue in the repository.
2. Add the `fix-me` label to the issue, or leave a comment starting with `@teai-agent`.
3. Review the attempt to resolve the issue by checking the pull request.
4. Follow up with feedback through general comments, review comments, or inline thread comments.
5. Add the `fix-me` label to the pull request, or address a specific comment by starting with `@teai-agent`.

### Label versus Macro

- Label (`fix-me`): Requests TeAI to address the **entire** issue or pull request.
- Macro (`@teai-agent`): Requests TeAI to consider only the issue/pull request description and **the specific comment**.

## Advanced Settings

### Add custom repository settings

You can provide custom directions for TeAI by following the [README for the resolver](https://github.com/All-Hands-AI/TeAI/blob/main/teai/resolver/README.md#providing-custom-instructions).

### Custom configurations

GitHub resolver will automatically check for valid [repository secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions?tool=webui#creating-secrets-for-a-repository) or [repository variables](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#creating-configuration-variables-for-a-repository) to customize its behavior.
The customization options you can set are:

| **Attribute name**               | **Type** | **Purpose**                                                                                         | **Example**                                        |
| -------------------------------- | -------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `LLM_MODEL`                      | Variable | Set the LLM to use with TeAI                                                                   | `LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"` |
| `TEAI_MAX_ITER`             | Variable | Set max limit for agent iterations                                                                  | `TEAI_MAX_ITER=10`                            |
| `TEAI_MACRO`                | Variable | Customize default macro for invoking the resolver                                                   | `TEAI_MACRO=@resolveit`                       |
| `TEAI_BASE_CONTAINER_IMAGE` | Variable | Custom Sandbox ([learn more](https://docs.all-hands.dev/modules/usage/how-to/custom-sandbox-guide)) | `TEAI_BASE_CONTAINER_IMAGE="custom_image"`    |
| `TARGET_BRANCH`                  | Variable | Merge to branch other than `main`                                                                   | `TARGET_BRANCH="dev"`                              |
