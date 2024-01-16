from lib.get_env import safe_get_env

def is_local():
  if safe_get_env("IS_LOCAL") == "TRUE":
    return True
  else:
    return False