# GitHub Actions Workflows

## Docker Build Workflow

This workflow automatically builds and pushes Docker images to Docker Hub when:

- Code is pushed to `main` or `dev` branches
- Tags are created (for releases)
- Pull requests are opened

## Setup Instructions

### 1. Create Docker Hub Account
- Sign up at [hub.docker.com](https://hub.docker.com)
- Create repository: `alexxyk/surya-ocr`

### 2. Configure GitHub Secrets
Go to repository Settings → Secrets and variables → Actions, and add:

- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password or access token

### 3. After Setup
Once configured, your images will be available as:

- **Latest (main branch)**: `alexxyk/surya-ocr:latest`
- **Development**: `alexxyk/surya-ocr:dev`
- **Tagged releases**: `alexxyk/surya-ocr:v1.0.0`

## Unraid Usage After Setup

Instead of building from repository, you can use:

```
Docker Hub Image: alexxyk/surya-ocr:latest
# or
Docker Hub Image: alexxyk/surya-ocr:dev
```

This is much faster for Unraid deployment!
