# 💿 Comment Créer un Soutien Docker sur Mesure

Le sandbox par défaut TeAI est équipé d'une configuration ubuntu minimaliste. Votre cas d'utilisation pourrait nécessiter des logiciels installés par défaut. Cet article vous enseignera comment réaliser cela en utilisant une image docker personnalisée.

## Configuration

Assurez-vous de pouvoir utiliser TeAI en suivant la documentation [Development.md](https://github.com/All-Hands-AI/TeAI/blob/main/Development.md).

## Créer Votre Image Docker

Ensuite, vous devez créer votre image docker personnalisée qui doit être basée sur debian/ubuntu. Par exemple, si nous souhaitons que TeAI ait accès au "node" binaire, nous utiliserions ce Dockerfile:

```bash
# Commencez avec l'image ubuntu la plus récente
FROM ubuntu:latest

# Effectuez les mises à jour nécessaires
RUN apt-get update && apt-get install

# Installez nodejs
RUN apt-get install -y nodejs
```

Ensuite, construisez votre image docker avec le nom de votre choix. Par exemple "image_personnalisée". Pour cela, créez un répertoire et placez le fichier à l'intérieur avec le nom "Dockerfile", puis dans le répertoire exécutez cette commande:

```bash
docker build -t image_personnalisée .
```

Cela produira une nouvelle image appelée ```image_personnalisée``` qui sera disponible dans Docker Engine.

> Remarque: Dans la configuration décrite ici, TeAI va fonctionner en tant que utilisateur "teai" à l'intérieur du sandbox et donc tous les packages installés via le Dockerfile seront disponibles pour tous les utilisateurs sur le système, pas seulement root.
>
> L'installation avec apt-get ci-dessus installe nodejs pour tous les utilisateurs.

## Spécifiez votre image personnalisée dans le fichier config.toml

La configuration TeAI se fait via le fichier de niveau supérieur ```config.toml``` .
Créez un fichier ```config.toml``` dans le répertoire TeAI et entrez ces contenus:

```toml
[core]
workspace_base="./workspace"
run_as_teai=true
[sandbox]
base_container_image="image_personnalisée"
```

> Assurez-vous que ```base_container_image``` est défini sur le nom de votre image personnalisée précédente.

## Exécution

Exécutez TeAI en exécutant ```make run``` dans le répertoire racine.

Naviguez vers ```localhost:3001``` et vérifiez si vos dépendances souhaitées sont disponibles.

Dans le cas de l'exemple ci-dessus, la commande ```node -v``` dans la console produit ```v18.19.1```

Félicitations !

## Explication technique

Lorsqu'une image personnalisée est utilisée pour la première fois, elle ne sera pas trouvée et donc elle sera construite (à l'exécution ultérieure, l'image construite sera trouvée et renvoyée).

L'image personnalisée est construite avec [_build_sandbox_image()](https://github.com/All-Hands-AI/TeAI/blob/main/teai/runtime/docker/image_agnostic_util.py#L29), qui crée un fichier docker en utilisant votre image personnalisée comme base et configure ensuite l'environnement pour TeAI, comme ceci:

```python
dockerfile_content = (
        f'FROM {base_image}\n'
        'RUN apt update && apt install -y openssh-server wget sudo\n'
        'RUN mkdir -p -m0755 /var/run/sshd\n'
        'RUN mkdir -p /teai && mkdir -p /teai/logs && chmod 777 /teai/logs\n'
        'RUN wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"\n'
        'RUN bash Miniforge3-$(uname)-$(uname -m).sh -b -p /teai/miniforge3\n'
        'RUN bash -c ". /teai/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"\n'
        'RUN echo "export PATH=/teai/miniforge3/bin:$PATH" >> ~/.bashrc\n'
        'RUN echo "export PATH=/teai/miniforge3/bin:$PATH" >> /teai/bash.bashrc\n'
    ).strip()
```

> Remarque: Le nom de l'image est modifié via [_get_new_image_name()](https://github.com/All-Hands-AI/TeAI/blob/main/teai/runtime/docker/image_agnostic_util.py#L63) et c'est ce nom modifié qui sera recherché lors des exécutions ultérieures.

## Dépannage / Erreurs

### Erreur: ```useradd: UID 1000 est non unique```
Si vous voyez cette erreur dans la sortie de la console, il s'agit du fait que TeAI essaie de créer le utilisateur teai dans le sandbox avec un ID d'utilisateur de 1000, cependant cet ID d'utilisateur est déjà utilisé dans l'image (pour une raison inconnue). Pour résoudre ce problème, changez la valeur du champ user_id dans le fichier config.toml en une valeur différente:

```toml
[core]
workspace_base="./workspace"
run_as_teai=true
[sandbox]
base_container_image="image_personnalisée"
user_id="1001"
```

### Erreurs de port d'utilisation

Si vous voyez un message d'erreur indiquant que le port est utilisé ou indisponible, essayez de supprimer toutes les containers docker en cours d'exécution (exécutez `docker ps` et `docker rm` des containers concernés) puis ré-exécutez ```make run```
