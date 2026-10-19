# 12 OpenRouter models

**Status:** todo · **Seam:** Settings, Activity · **Depends on:** 10 · **Stories:** 19, 20

## What

OpenRouter backend for the Agent model (DeepSeek) and Judge model, configured with pydantic-settings; API key is SecretStr.

## Acceptance tests

- [ ] the Agent model and Judge model are read from settings and must differ
- [ ] the API key never appears in a Trace or log line
- [ ] a model response is turned into Capability calls or work (activity test against a recorded response)
