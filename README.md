# python-infisical

Lightweight Python client for [Infisical](https://infisical.com/) secrets manager using Machine Identity (Universal Auth).

## Install

```bash
pip install git+https://github.com/jlixfeld/python-infisical.git
```

## Usage

```python
from python_infisical import InfisicalConfig, fetch_secrets, load_secrets_into_env

# Build config from environment variables
config = InfisicalConfig.from_env()

# Fetch specific secrets
secrets = fetch_secrets(
    config,
    required=["GITHUB_TOKEN", "DATABASE_URL"],
    optional=["DEEPGRAM_API_KEY"],
)

# Or inject directly into os.environ
load_secrets_into_env(config, required=["GITHUB_TOKEN"])
```

### Environment variables

| Variable | Required | Default |
|---|---|---|
| `INFISICAL_CLIENT_ID` | Yes | |
| `INFISICAL_CLIENT_SECRET` | Yes | |
| `INFISICAL_HOST` | No | `http://localhost:8080` |
| `INFISICAL_PROJECT_ID` | No | |
| `INFISICAL_ENVIRONMENT` | No | `prod` |

## License

MIT
