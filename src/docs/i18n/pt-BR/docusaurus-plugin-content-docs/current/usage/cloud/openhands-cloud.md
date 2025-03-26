# Openhands Cloud

O TeAI Cloud é a versão hospedada na nuvem do TeAI da All Hands AI.

## Acessando o TeAI Cloud

Atualmente, os usuários estão sendo admitidos para acessar o TeAI Cloud em ondas. Para se inscrever,
[entre na lista de espera](https://www.all-hands.dev/join-waitlist). Assim que for aprovado, você receberá um e-mail com
instruções sobre como acessá-lo.

## Primeiros Passos

Após visitar o TeAI Cloud, você será solicitado a se conectar com sua conta do GitHub:
1. Após ler e aceitar os termos de serviço, clique em `Connect to GitHub`.
2. Revise as permissões solicitadas pelo TeAI e clique em `Authorize TeAI AI`.
   - O TeAI exigirá algumas permissões da sua conta do GitHub. Para ler mais sobre essas permissões,
     você pode clicar no link `Learn more` na página de autorização do GitHub.

## Acesso ao Repositório

### Adicionando Acesso ao Repositório

Você pode conceder ao TeAI acesso específico ao repositório:
1. Clique no menu suspenso `Select a GitHub project`, selecione `Add more repositories...`.
2. Selecione a organização e escolha os repositórios específicos para conceder acesso ao TeAI.
   - O Openhands solicita tokens de curta duração (expiração de 8 horas) com estas permissões:
     - Actions: Read and write
     - Administration: Read-only
     - Commit statuses: Read and write
     - Contents: Read and write
     - Issues: Read and write
     - Metadata: Read-only
     - Pull requests: Read and write
     - Webhooks: Read and write
     - Workflows: Read and write
   - O acesso ao repositório para um usuário é concedido com base em:
     - Permissão concedida para o repositório.
     - Permissões do GitHub do usuário (proprietário/colaborador).
3. Clique em `Install & Authorize`.

### Modificando o Acesso ao Repositório

Você pode modificar o acesso ao repositório a qualquer momento:
* Usando o mesmo fluxo de trabalho `Select a GitHub project > Add more repositories`, ou
* Visitando a página de Configurações e selecionando `Configure GitHub Repositories` na seção `GitHub Settings`.
