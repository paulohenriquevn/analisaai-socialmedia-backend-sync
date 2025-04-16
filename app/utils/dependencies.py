from fastapi import Depends, HTTPException, status
from typing import Dict
from app.utils.auth import get_current_user

# Exemplo de dependência para checar se usuário tem role 'manager'
def get_manager_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    if "manager" not in current_user["roles"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager role required")
    return current_user
