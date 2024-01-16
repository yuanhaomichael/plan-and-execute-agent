import os

def safe_get_env(name: str):
  if name in os.environ:
    return os.environ[name]
  return None