from rest_framework.permissions import BasePermission

from common.scoping import can_access_branch, can_access_company


ACTION_MAP = {
    "list": "can_view",
    "retrieve": "can_view",
    "create": "can_create",
    "update": "can_update",
    "partial_update": "can_update",
    "destroy": "can_delete",
    "siguiente": "can_create",
    "add_detail": "can_update",
    "cash_count": "can_update",
    "close": "can_close",
    "reset_password": "can_update",
    "set_roles": "can_approve",
    "set_permissions": "can_approve",
}


class HasModulePermission(BasePermission):
    """Checks role/module/action on every request; superusers bypass the matrix."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        module_code = getattr(view, "permission_module", None)
        permission_field = getattr(view, "permission_action", None) or ACTION_MAP.get(getattr(view, "action", ""), "can_view")
        if not module_code:
            return False
        allowed = user.roles.filter(
            is_active=True,
            profile__is_active=True,
            profile__permissions__module__code=module_code,
            **{f"profile__permissions__{permission_field}": True},
        ).exists()
        if not allowed:
            return False
        if request.method in ("POST", "PUT", "PATCH"):
            branch_id = request.data.get("sucursal_id") or request.data.get("sucursal") or request.data.get("branch")
            company_id = request.data.get("empresa") or request.data.get("company")
            if branch_id and not can_access_branch(user, branch_id):
                return False
            if company_id and not can_access_company(user, company_id):
                return False
        return True
