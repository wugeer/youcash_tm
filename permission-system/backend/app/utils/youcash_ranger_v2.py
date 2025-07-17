from apache_ranger.client.ranger_client import RangerClient
import argparse

# 从环境变量中获取Ranger配置
import os
RANGER_URL = os.getenv("RANGER_URL", "")
RANGER_USER = os.getenv("RANGER_USER", "")
RANGER_PASSWORD = os.getenv("RANGER_PASSWORD", "")

RANGER_ALL_PRIVILEDGE = ["SHOW_VIEW","SHOW","LOAD","ALTER","CREATE","ALTER_CREATE","SELECT","DROP","ALTER_CREATE_DROP"]

import logging
logger = logging.getLogger(__name__)

class RangerManager:
    def __init__(self, ranger_url, ranger_user, ranger_password):
        self.client = RangerClient(ranger_url, (ranger_user, ranger_password))
        self.role = RangerRoleManager(self.client)
        self.policy = RangerPolicyManager(self.client)

class RangerRoleManager:
    def __init__(self, client):
        self.client = client

    def search_roles_with_user(self, user_name):
        import requests
        auth = (RANGER_USER, RANGER_PASSWORD)
        headers = {
            'Content-Type': 'application/json'
        }
        
        url = f'{RANGER_URL}/service/public/v2/api/roles'
        roles = []
        try:
            response = requests.get(url, headers=headers, auth=auth, params={'userName':f'{user_name}'})
            response.raise_for_status()
            roles.extend(response.json())
        except Exception as e:
            logger.warning(f"Error fetching roles with user name:{user_name}: {e}")
        return roles 

    def remove_user_from_all_roles(self, args, ):
        for user in args.users:
            for role in self.search_roles_with_user(user):
                args.role_name = role["name"]
                logger.info(f"start to remove user {user} from role {role['name']}")
                self.remove_entity_from_role(args, role)

    def search_role(self, args, ):
        try:
            role = self.client.get_role(args.role_name, 'admin', args.service)
            logger.info(f"find role: {role}")
            return role
        except Exception as e:
            logger.warning(f"Error fetching policies: {e}")
            return None

    def create_role(self, args, ):
        # Create new role
        existing_role = self.search_role(args)
        if existing_role:
            args.users = args.users or []
            args.groups = args.groups or []
            args.roles = args.roles or []
            logger.info(f"目标角色已经存在，开始确保指定的用户、组在角色中")
            self.add_entity_to_role(args, existing_role)
        else:
            role = {
                "name": args.role_name,
                "users": [{"name": user, "isAdmin": False} for user in (args.users or [])],
                "groups": [{"name": group, "isAdmin": False} for group in (args.groups or [])],
                "roles": [{"name": role, "isAdmin": False} for role in (args.roles or [])],
            }
            self.client.create_role(args.service, role)
            logger.info(f"Created role: {role}")

    def add_entity_to_role(self, args, existing_role=None):
        role_name = args.role_name
        add_users = set(args.users)
        add_groups = set(args.groups)
        add_roles = set(args.roles)
        existing_role = existing_role or self.search_role(args)
        new_users, new_groups, new_roles = [], [], []

        if existing_role:
            # Update existing role
            o_users = existing_role.get('users')
            old_users = {o_user.get("name") for o_user in o_users}

            for user_name in add_users:
                if user_name in old_users:
                    logger.info(f'用户{user_name}已经存在，本次不需要操作')
                else:
                    logger.info(f'用户{user_name}需要添加到角色:{role_name}')
                    new_users.append({"name": user_name, "isAdmin": False})

            o_groups = existing_role.get('groups')
            old_groups = {o_group.get("name") for o_group in o_groups}

            for group_name in add_groups:
                if group_name in old_groups:
                    logger.info(f'组{group_name}已经存在，本次不需要操作')
                else:
                    logger.info(f'组{group_name}需要添加到角色:{role_name}')
                    new_groups.append({"name": group_name, "isAdmin": False})

            o_roles = existing_role.get('roles')
            old_roles = {o_role.get("name") for o_role in o_roles}

            for new_role_name in add_roles:
                if new_role_name in old_roles:
                    logger.info(f'角色{new_role_name}已经存在于目标角色中，本次不需要操作')
                else:
                    logger.info(f'角色{new_role_name}需要添加到角色:{role_name}')
                    new_roles.append({"name": new_role_name, "isAdmin": False})

            if new_users:
                o_users.extend(new_users)
            if new_groups:
                o_groups.extend(new_groups)
            if new_roles:
                o_roles.extend(new_roles)

            if new_users + new_groups + new_roles:
                self.client.update_role(existing_role["id"], existing_role)
                logger.info(f"Updated role: {existing_role}")
            else:
                logger.info(f"No updates needed for role: {existing_role['name']}")
        else:
            # Create new role
            role = {
                "name": role_name,
                "users": [{"name": user, "isAdmin": False} for user in (add_users or [])],
                "groups": [{"name": group, "isAdmin": False} for group in (add_groups or [])],
                "roles": [{"name": role, "isAdmin": False} for role in (add_roles or [])],
            }
            self.client.create_role(args.service, role)
            logger.info(f"Created role: {role}")

    def remove_entity_from_role(self, args, existing_role=None):
        role_name = args.role_name
        to_del_users = args.users or []
        to_del_groups = args.groups or []
        to_del_roles = args.roles or []
        existing_role = existing_role or self.search_role(args)
        actual_del_users, actual_del_groups, actual_del_roles = [], [], []

        if existing_role:
            # Update existing role
            old_users = existing_role.get('users')
            for idx, old_user in enumerate(old_users):
                if old_user.get("name") in to_del_users:
                    actual_del_users.append(idx)

            if actual_del_users:
                # 倒序遍历并删除
                for idx in sorted(actual_del_users, reverse=True):
                    old_users.pop(idx)

            old_groups = existing_role.get('groups')
            for idx, old_group in enumerate(old_groups):
                if old_group.get("name") in to_del_groups:
                    actual_del_groups.append(idx)

            if actual_del_groups:
                # 倒序遍历并删除
                for idx in sorted(actual_del_groups, reverse=True):
                    old_groups.pop(idx)

            old_roles = existing_role.get('roles')
            for idx, old_role in enumerate(old_roles):
                if old_role.get("name") in to_del_roles:
                    actual_del_roles.append(idx)

            if actual_del_roles:
                # 倒序遍历并删除
                for idx in sorted(actual_del_roles, reverse=True):
                    old_roles.pop(idx)
     
            if actual_del_groups + actual_del_users + actual_del_roles:
                self.client.update_role(existing_role["id"], existing_role)
                logger.info(f"Updated role: {existing_role}")
            else:
                logger.info(f"No updates needed for role: {role_name}")
        else:
            logger.info(f"No role found with name: {role_name}")


class RangerPolicyManager:
    def __init__(self, client):
        self.client = client

    def get_existing_policy(self, service, name):
        try:
            policy = self.client.get_policy(service, name)
            return policy
        except Exception as e:
            logger.warning(f"Error fetching policies: {e} in service:[{service}] for name:[{name}]")
            return None

    @staticmethod
    def check_basic(args):
        if not (args.users or args.groups or args.roles):
            raise Exception("请输入用户或者用户组或者角色")
        if not (args.database or args.table or args.columns):
            raise Exception("请输入数据库名或者表名或者字段名")

    def grant_access(self, args):
        self.check_basic(args)
        if args.policy_type == 'normal':
            self.create_or_update_normal_policy(args)
        elif args.policy_type == 'mask':
            self.create_or_update_data_mask_policy(args)
        elif args.policy_type == 'row-filter':
            self.create_or_update_row_filter_policy(args)

    def create_or_update_normal_policy(self, args):
        if args.accesses and set(args.accesses) - {'drop', 'all', 'select', 'read', 'rwstorage', 'update', 'index',
                                                   'refresh', 'tempudfadmin', 'serviceadmin', 'create', 'lock',
                                                   'repladmin', 'write', 'alter'}:
            raise Exception(
                "请输入有效的权限类型:'drop', 'all', 'select', 'read', 'rwstorage', 'update', 'index', 'refresh', "
                "'tempudfadmin', 'serviceadmin', 'create', 'lock', 'repladmin', 'write', 'alter'")

        if args.database == '*':
            raise Exception("normal类型的策略不允许数据库指定为*")

        for col_name in args.columns or ['*']:
            table_name_str = args.table if args.table != "*" else "all"
            col_name_str = col_name if col_name != "*" else "all"
            for service in args.service:
                policy_names = [(((len(args.columns) == 1 and args.name) or f'{args.database}.{table_name_str}.{col_name_str}.normal'), None)]

                if service == "doris":
                    if not args.catalog:
                        raise Exception("服务名是doris时必须指定catalog")
                    policy_names = [(f'{service}.{catalog}.{policy_names[0][0]}', catalog) for catalog in args.catalog]

                for policy_name, catalog_name in policy_names:
                    logger.info(f"开始操作service:[{service}] policy_name:[{policy_name}] catalog_name:[{catalog_name}]")
                    existing_policy = self.get_existing_policy(service, policy_name)
                    new_access = args.accesses
                    if service == "doris" and set(new_access) & {"all", "select"}:
                        if new_access == ["all"]:
                            new_access = RANGER_ALL_PRIVILEDGE
                        elif new_access == ["select"]:
                            new_access.append("show")

                    if existing_policy:
                        # Update existing policy
                        add_item = None
                        for policy_item in existing_policy["policyItems"]:
                            if not (
                                    set(args.users) - set(policy_item.get("users", [])) or
                                    set(args.groups) - set(policy_item.get("groups", [])) or
                                    set(args.roles) - set(policy_item.get("roles", [])) or
                                    set([a.upper() for a in new_access]) - set([access["type"].upper() for access in policy_item["accesses"]])):
                                logger.info(f"policy_name:[{policy_name}] in service:[{service}] catalog:[{catalog_name}] already exists with the same configuration, nothing to do")
                                add_item = None
                                break
                            add_item = {
                                "accesses": [{"type": access if service != "doris" else access.upper(), "isAllowed": True} for access in new_access],
                                "users": args.users or [],
                                "groups": args.groups or [],
                                "roles": args.roles or []
                            }

                        if not existing_policy["policyItems"]:
                            # 处理没有空记录的情况
                            add_item = {
                                "accesses": [{"type": access if service != "doris" else access.upper(), "isAllowed": True} for access in new_access],
                                "users": args.users or [],
                                "groups": args.groups or [],
                                "roles": args.roles or []
                            }

                        if add_item:
                            # add item should insert at the front of the list
                            existing_policy["policyItems"].insert(0, add_item)
                            self.client.update_policy_by_id(existing_policy["id"], existing_policy)
                            logger.info(f"Updated Policy: {existing_policy} in service:[{service}] catalog:[{catalog_name}]")
                        else:
                            logger.info(f"No updates needed for Policy: {existing_policy['name']} in service:[{service}] catalog:[{catalog_name}]")
                    else:
                        # Create new policy
                        policy_data = {
                            "service": service,
                            "name": policy_name,
                            "policyType": 0,
                            "description": f"Create normal policy: {policy_name} auto",
                            "resources": {
                                "database": {"values": [args.database], "isExcludes": False, "isRecursive": False},
                                "table": {"values": [args.table], "isExcludes": False, "isRecursive": False},
                                "column": {"values": [col_name], "isExcludes": False, "isRecursive": False}
                            },
                            "policyItems": [{
                                "accesses": [{"type": access if service != "doris" else access.upper(), "isAllowed": True} for access in new_access],
                                "users": args.users or [],
                                "groups": args.groups or [],
                                "roles": args.roles or []
                            }]
                        }
                        if service == "doris":
                            policy_data["resources"]["catalog"] ={"values": [catalog_name], "isExcludes": False, "isRecursive": False}
                        self.client.create_policy(policy_data)
                        logger.info(f"Created Policy: {policy_data} in service:[{service}] catalog:[{catalog_name}]")

    def create_or_update_data_mask_policy(self, args):
        if args.mask_type not in ('MASK_HASH', 'MASK_NONE', 'CUSTOM'):
            raise Exception(f"mask类型应该是MASK_HASH/MASK_NONE/CUSTOM，实际是:[{args.mask_type}]")

        if args.database == '*' or args.table == '*':
            raise Exception("datamask 策略不允许数据库或者表名为*")

        for col_name in args.columns:
            for service in args.service:
                policy_names = [(((len(args.columns) == 1 and args.name) or f'{args.database}.{args.table}.{col_name}.mask'), None)]

                if service == "doris":
                    if not args.catalog:
                        raise Exception("服务名是doris时必须指定catalog")
                    policy_names = [(f'{service}.{catalog}.{policy_names[0][0]}', catalog) for catalog in args.catalog]

                for policy_name, catalog_name in policy_names:
                    logger.info(f"开始操作service:[{service}] policy_name:[{policy_name}] catalog_name:[{catalog_name}]")
                    existing_policy = self.get_existing_policy(service, policy_name)

                    if existing_policy:
                        # Update existing policy
                        add_item = None
                        for policy_item in existing_policy["dataMaskPolicyItems"]:
                            if (not (
                                    set(args.users) - set(policy_item.get("users", [])) or
                                    set(args.groups) - set(policy_item.get("groups", [])) or
                                    set(args.roles) - set(policy_item.get("roles", []))) and
                                    policy_item["dataMaskInfo"]["dataMaskType"] == args.mask_type):
                                logger.info(f"policy_name:[{policy_name}] in service:[{service}] catalog:[{catalog_name}] already exists with the same configuration, nothing to do")
                                add_item = None
                                break
                            add_item = {
                                "accesses": [{"type": "select" if service != "doris" else 'SELECT', "isAllowed": True}],
                                "users": args.users or [],
                                "groups": args.groups or [],
                                "roles": args.roles or [],
                                "dataMaskInfo": {
                                    "dataMaskType": args.mask_type,
                                    "valueExpr": f"upper(md5(`{col_name}`))" if service== "doris" else f"default.uppermd5(`{col_name}`)" if args.mask_type == 'CUSTOM' else None,
                                    "maskCondition": None,
                                    "description": None
                                }
                            }
                        if not existing_policy["dataMaskPolicyItems"]:
                            # 处理没有空记录的情况
                            add_item = {
                                "accesses": [{"type": "select" if service != "doris" else "SELECT", "isAllowed": True}],
                                "users": args.users or [],
                                "groups": args.groups or [],
                                "roles": args.roles or [],
                                "dataMaskInfo": {
                                    "dataMaskType": args.mask_type,
                                    "valueExpr": f"upper(md5(`{col_name}`))" if service== "doris" else f"default.uppermd5(`{col_name}`)" if args.mask_type == 'CUSTOM' else None,
                                    "maskCondition": None,
                                    "description": None
                                }
                            }

                        if add_item:
                            # add item should insert at the front of the list
                            existing_policy["dataMaskPolicyItems"].insert(0, add_item)
                            self.client.update_policy_by_id(existing_policy["id"], existing_policy)
                            logger.info(f"Updated Policy: {existing_policy} in service:[{service}] catalog:[{catalog_name}]")
                        else:
                            logger.info(f"No updates needed for Policy: {existing_policy['name']} in service:[{service}] catalog:[{catalog_name}]")
                    else:
                        if args.mask_type not in ("MASK_HASH","CUSTOM"):
                            raise Exception(f"初始{policy_name}的datamask策略应该是MASK_HASH/CUSTOM类型而不是{args.mask_type}")
                        # Create new policy
                        policy_data = {
                            "service": service,
                            "name": policy_name,
                            "policyType": 1,
                            "description": f"Create data mask policy: {policy_name} auto",
                            "resources": {
                                "database": {"values": [args.database], "isExcludes": False, "isRecursive": False},
                                "table": {"values": [args.table], "isExcludes": False, "isRecursive": False},
                                "column": {"values": [col_name], "isExcludes": False, "isRecursive": False}
                            },
                            "dataMaskPolicyItems": [{
                                "accesses": [{"type": "select" if service != "doris" else "SELECT", "isAllowed": True}],
                                "users": args.users or [],
                                "groups": args.groups or [],
                                "roles": args.roles or [],
                                "dataMaskInfo": {
                                    "dataMaskType": args.mask_type,
                                    "valueExpr": f"upper(md5(`{col_name}`))" if service== "doris" else f"default.uppermd5(`{col_name}`)"  if args.mask_type == 'CUSTOM' else None,
                                    "maskCondition": None,
                                    "description": None
                                }
                            }]
                        }
                        if service == "doris":
                            policy_data["resources"]["catalog"] = {"values": [catalog_name], "isExcludes": False, "isRecursive": False}
                        self.client.create_policy(policy_data)
                        logger.info(f"Created Data Mask Policy: {policy_data} in service:[{service}] catalog:[{catalog_name}]")

    def create_or_update_row_filter_policy(self, args):
        if not args.row_filter or not args.row_filter.strip():
            raise Exception("创建的row_filter策略的过滤条件不允许为空")

        if args.database == '*' or args.table == '*':
            raise Exception("row_filter 策略不允许数据库或者表名为*")

        for service in args.service:
            policy_names = [(args.name or f'{args.database}.{args.table}.row_filter', None)]

            if service == "doris":
                if not args.catalog:
                    raise Exception("服务名是doris时必须指定catalog")
                policy_names = [(f'{service}.{catalog}.{policy_names[0][0]}', catalog) for catalog in args.catalog]

            for policy_name, catalog_name in policy_names:
                logger.info(f"开始操作service:[{service}] policy_name:[{policy_name}] catalog_name:[{catalog_name}]")
                existing_policy = self.get_existing_policy(service, policy_name)

                if existing_policy:
                    # Update existing policy
                    add_item = None
                    for policy_item in existing_policy["rowFilterPolicyItems"]:
                        if (not (
                                set(args.users) - set(policy_item.get("users", [])) or
                                set(args.groups) - set(policy_item.get("groups", [])) or
                                set(args.roles) - set(policy_item.get("roles", []))) and
                                policy_item["rowFilterInfo"]["filterExpr"] == args.row_filter.strip()):
                            logger.info(f"policy_name:[{policy_name}] in service:[{service}] catalog:[{catalog_name}] already exists with the same configuration, nothing to do")
                            add_item = None
                            break
                        add_item = {
                            "accesses": [{"type": access if service != "doris" else access.upper(), "isAllowed": True} for access in args.accesses],
                            "users": args.users or [],
                            "groups": args.groups or [],
                            "roles": args.roles or [],
                            "rowFilterInfo": {
                                "filterExpr": args.row_filter.strip()
                            }
                        }

                    if not existing_policy["rowFilterPolicyItems"]:
                        # 处理没有空记录的情况
                        add_item = {
                            "accesses": [{"type": access if service != "doris" else access.upper(), "isAllowed": True} for access in args.accesses],
                            "users": args.users or [],
                            "groups": args.groups or [],
                            "roles": args.roles or [],
                            "rowFilterInfo": {
                                "filterExpr": args.row_filter.strip()
                            }
                        }

                    if add_item:
                        existing_policy["rowFilterPolicyItems"].insert(0, add_item)
                        self.client.update_policy_by_id(existing_policy["id"], existing_policy)
                        logger.info(f"Updated Policy: {existing_policy} in service:[{service}] catalog:[{catalog_name}]")
                    else:
                        logger.info(f"No updates needed for Policy: {existing_policy['name']} in service:[{service}] catalog:[{catalog_name}]")
                else:
                    # Create new policy
                    policy_data = {
                        "service": service,
                        "name": policy_name,
                        "policyType": 2,
                        "description": f"Create policy: {policy_name} auto",
                        "resources": {
                            "database": {"values": [args.database], "isExcludes": False, "isRecursive": False},
                            "table": {"values": [args.table], "isExcludes": False, "isRecursive": False}
                        },
                        "rowFilterPolicyItems": [{
                            "accesses": [{"type": access if service != "doris" else access.upper(), "isAllowed": True} for access in args.accesses],
                            "users": args.users or [],
                            "groups": args.groups or [],
                            "roles": args.roles or [],
                            "rowFilterInfo": {
                                "filterExpr": args.row_filter.strip()
                            }
                        }]
                    }
                    if service == "doris":
                        policy_data["resources"]["catalog"] = {"values": [catalog_name], "isExcludes": False, "isRecursive": False}
                    self.client.create_policy(policy_data)
                    logger.info(f"Created Row Filter Policy: {policy_data} in service:[{service}] catalog:[{catalog_name}]")

    def revoke_access(self, args):
        self.check_basic(args)

        if args.policy_type == 'normal':
            self.revoke_normal_policy(args)
        elif args.policy_type == 'mask':
            self.revoke_data_mask_policy(args)
        elif args.policy_type == 'row-filter':
            self.revoke_row_filter_policy(args)

    def revoke_normal_policy(self, args):
        for col_name in args.columns or ['*']:
            table_str = args.table if args.table != "*" else "all"
            col_name_str = col_name if col_name != "*" else "all"
            for service in args.service:
                policy_names = [(len(args.columns) == 1 and args.name) or f'{args.database}.{table_str}.{col_name_str}.normal']

                if service == "doris":
                    if not args.catalog:
                        raise Exception("服务名是doris时必须指定catalog")
                    policy_names = [f'{service}.{catalog}.{policy_names[0]}' for catalog in args.catalog]

                for policy_name in policy_names:
                    logger.info(f"开始操作service:[{service}] policy_name:[{policy_name}]")
                    existing_policy = self.get_existing_policy(service, policy_name)

                    new_access = args.accesses
                    if service == "doris" and set(new_access) & {"all", "select"}:
                        if new_access == ["all"]:
                            new_access = RANGER_ALL_PRIVILEDGE
                        elif new_access == ["select"]:
                            new_access.append("show")

                    if existing_policy:
                        items_to_remove = []
                        for i, policy_item in enumerate(existing_policy["policyItems"]):
                            if set([item.lower() for item in new_access]) != set([access["type"].lower() for access in policy_item["accesses"]]):
                                continue
                            not_found = True
                            for item in set(args.users) & set(policy_item.get("users", [])):
                                not_found = False
                                policy_item["users"].remove(item)
                            for item in set(args.groups) & set(policy_item.get("groups", [])):
                                not_found = False
                                policy_item["groups"].remove(item)
                            for item in set(args.roles) & set(policy_item.get("roles", [])):
                                not_found = False
                                policy_item["roles"].remove(item)
                            if not_found:
                                logger.info("policy_name:[{policy_name}] in service:[{service}] policy access type is ok, but there is no user, groups, roles need to revoke, "
                                      "please check again!")
                                logger.info(f"Policy {policy_name} has no items matching the specified criteria: "
                                      f"access:{args.accesses} users:{args.users} groups:{args.groups} "
                                      f"roles:[{args.roles}]")
                                continue
                            if not any(policy_item.get("users", [])) and not any(policy_item.get("groups", [])) and not any(
                                    policy_item.get("roles", [])):
                                items_to_remove.append(i)

                        if items_to_remove:
                            if len(items_to_remove) == len(existing_policy["policyItems"]):
                                logger.info("all items in policy will be remove, so change to delete the policy!!!!")
                                policy_id = existing_policy["id"]
                                self.delete_policy_by_id(policy_id)
                                continue
                            for index in sorted(items_to_remove, reverse=True):
                                del existing_policy["policyItems"][index]
                        self.client.update_policy_by_id(existing_policy["id"], existing_policy)
                        logger.info(f"Updated Policy: {existing_policy} in service:[{service}]]")
                    else:
                        logger.info(f"No policy found with name: {policy_name} in service:[{service}]")

    def revoke_data_mask_policy(self, args):
        if args.database == '*' or args.table == '*':
            raise Exception("datamask 策略不允许数据库或者表名为*")
        for col_name in args.columns:
            for service in args.service:
                policy_names = [(len(args.columns) == 1 and args.name) or f'{args.database}.{args.table}.{col_name}.mask']

                if service == "doris":
                    if not args.catalog:
                        raise Exception("服务名是doris时必须指定catalog")
                    policy_names = [f'{service}.{catalog}.{policy_names[0]}' for catalog in args.catalog]

                for policy_name in policy_names:
                    logger.info(f"开始操作service:[{service}] policy_name:[{policy_name}]")
                    existing_policy = self.get_existing_policy(service, policy_name)

                    if existing_policy:
                        items_to_remove = []
                        for i, policy_item in enumerate(existing_policy["dataMaskPolicyItems"]):
                            if policy_item["dataMaskInfo"]["dataMaskType"] != args.mask_type:
                                continue
                            not_found = True
                            for item in set(args.users) & set(policy_item.get("users", [])):
                                not_found = False
                                policy_item["users"].remove(item)
                            for item in set(args.groups) & set(policy_item.get("groups", [])):
                                not_found = False
                                policy_item["groups"].remove(item)
                            for item in set(args.roles) & set(policy_item.get("roles", [])):
                                not_found = False
                                policy_item["roles"].remove(item)
                            if not_found:
                                logger.info("policy_name:[{policy_name}] in service:[{service}] catalog:[{args.catalog}] policy access type is ok, but there is no user, groups, roles need to revoke, "
                                      "please check again!")
                                logger.info(f"Policy {policy_name} has no items matching the specified criteria: "
                                      f"dataMaskInfo:{args.mask_type} users:{args.users} groups:{args.groups} "
                                      f"roles:[{args.roles}]")
                                continue
                            if not any(policy_item.get("users", [])) and not any(policy_item.get("groups", [])) and not any(
                                    policy_item.get("roles", [])):
                                items_to_remove.append(i)

                        if items_to_remove:
                            if len(items_to_remove) == len(existing_policy["dataMaskPolicyItems"]):
                                logger.info(f"all items in policy:[{policy_name}] will be remove, so change to delete the policy!!!!")
                                policy_id = existing_policy["id"]
                                self.delete_policy_by_id(policy_id)
                                continue
                            for index in sorted(items_to_remove, reverse=True):
                                del existing_policy["dataMaskPolicyItems"][index]
                            self.client.update_policy_by_id(existing_policy["id"], existing_policy)
                            logger.info(f"Updated Policy: {existing_policy} in service:[{service}] catalog:[{args.catalog}]")
                    else:
                        logger.info(f"No policy found with name: {policy_name} in service:[{service}] catalog:[{args.catalog}]")

    def revoke_row_filter_policy(self, args):
        for service in args.service:
            policy_names = [args.name or f'{args.database}.{args.table}.row_filter']

            if service == "doris":
                if not args.catalog:
                    raise Exception("服务名是doris时必须指定catalog")
                policy_names = [f'{service}.{catalog}.{policy_names[0]}' for catalog in args.catalog]

            for policy_name in policy_names:
                logger.info(f"开始操作service:[{service}] policy_name:[{policy_name}]")
                existing_policy = self.get_existing_policy(service, policy_name)

                if existing_policy:
                    items_to_remove = []
                    need_update = False
                    for i, policy_item in enumerate(existing_policy["rowFilterPolicyItems"]):
                        if policy_item["rowFilterInfo"]["filterExpr"] == args.row_filter.strip():
                            # continue
                            not_found = True
                            for item in set(args.users) & set(policy_item.get("users", [])):
                                not_found = False
                                policy_item["users"].remove(item)
                            for item in set(args.groups) & set(policy_item.get("groups", [])):
                                not_found = False
                                policy_item["groups"].remove(item)
                            for item in set(args.roles) & set(policy_item.get("roles", [])):
                                not_found = False
                                policy_item["roles"].remove(item)
                            if not_found:
                                logger.info("policy_name:[{policy_name}] in service:[{service}] policy access type is ok, but there is no user, groups, roles need to revoke, please check "
                                      "again!")
                                logger.info("Policy {policy_name} has no items matching the specified criteria: "
                                      "row_filter:{args.row_filter.strip()} users:{args.users} "
                                      "groups:[{args.groups}] roles:[{args.roles}]")
                                continue
                            need_update = True
                            if not any(policy_item.get("users", [])) and not any(policy_item.get("groups", [])) and not any(
                                    policy_item.get("roles", [])):
                                items_to_remove.append(i)

                    if items_to_remove:
                        if len(items_to_remove) == len(existing_policy["rowFilterPolicyItems"]):
                            logger.info("all items in policy will be remove, so change to delete the policy!!!!")
                            policy_id = existing_policy["id"]
                            self.delete_policy_by_id(policy_id)
                            continue
                        for index in sorted(items_to_remove, reverse=True):
                            del existing_policy["rowFilterPolicyItems"][index]

                    if need_update:
                        self.client.update_policy_by_id(existing_policy["id"], existing_policy)
                        logger.info(f"Updated Policy: {existing_policy} in service:[{service}]")
                else:
                    logger.info(f"No policy found with name: {policy_name} in service:[{service}]")

    def delete_entity_access(self, args):
        if len([item for item in [args.policy_name, args.user, args.group, args.role] if item]) != 1:
            raise Exception("--policy_name flag or --user flag or --group or --role flag "
                            "can provide one of these parameters to delete!")

        if args.policy_name:
            self.delete_policy(args)
        else:
            entity_type, entity_value = self.get_non_empty_argument(args, 'user', 'group', 'role')
            logger.info(f"service={args.service} entity_type={entity_type} entiry_value={entity_value}")
            policies = self.find_policies_by_entity(args.service, entity_type, entity_value)

            if policies:
                logger.info(f"Found {len(policies)} policies for type:[{entity_type}] with value:[{entity_value}]")
                for policy in policies:
                    is_find = False
                    items_to_delete = []
                    for item in policy.get("policyItems", []) + policy.get("dataMaskPolicyItems", []) + policy.get("rowFilterPolicyItems", []):
                        if entity_value in item.get(entity_type+"s", []):
                            is_find = True
                            item[entity_type+"s"].remove(entity_value)
                            if not any(item.get("users", [])) and not any(item.get("groups", [])) and not any(
                                    item.get("roles", [])):
                                logger.info(f"start to delete item:{item}")
                                items_to_delete.append(item)

                    # 从原始列表中删除找到的项
                    for item in items_to_delete:
                        if item in policy.get("policyItems", []):
                            policy["policyItems"].remove(item)
                        if item in policy.get("dataMaskPolicyItems", []):
                            policy["dataMaskPolicyItems"].remove(item)
                        if item in policy.get("rowFilterPolicyItems", []):
                            policy["rowFilterPolicyItems"].remove(item)

                    if not is_find:
                        raise Exception("user doesn't not grant to access to this policy!'")

                    is_deleted = True
                    # 遍历policyItems, dataMaskPolicyItems, rowFilterPolicyItems检查是否所有的users,groups,roles是否有非空的
                    for item in policy.get("policyItems", []) + policy.get("dataMaskPolicyItems", []) + policy.get(
                            "rowFilterPolicyItems", []):
                        if any(item.get("users", [])) or any(item.get("groups", [])) or any(item.get("roles", [])):
                            is_deleted = False

                    logger.info(policy)
                    if is_deleted:
                        logger.info("while the policyItems, dataMaskPolicyItems, rowFilterPolicyItems go to empty, "
                              "so wo decide to delete the policy: {policy['id']} with input user:{args.user}")
                        self.delete_policy_by_id(policy["id"])
                    else:
                        self.update_policy_by_id(policy["id"], policy)
            else:
                logger.info(f"No policies found for entity_type:[{entity_type+'s'}] value:[{entity_value}]")

    def delete_policy(self, args):
        for service in args.service:
            existing_policy = self.get_existing_policy(service, args.policy_name)
            if existing_policy:
                policy_id = existing_policy["id"]
                self.delete_policy_by_id(policy_id)
            else:
                logger.info(f"No policy found with name: {args.policy_name} in service:[{service}]")

    def delete_policy_by_id(self, policy_id):
        logger.info(f"Deleting Policy with id: {policy_id}")
        try:
            self.client.delete_policy_by_id(policy_id)
            logger.info(f"Deleted Policy id: {policy_id}")
        except Exception as e:
            logger.warning(f"Failed to delete policy id:{policy_id} with errors: {e}")

    def search_entity_policy(self, args):
        if len([item for item in [args.user, args.group, args.role] if item]) != 1:
            raise Exception("--user flag or --group or --role flag can provide one of these parameters to delete!")

        entity_type, entity_value = self.get_non_empty_argument(args, 'user', 'group', 'role')
        for service in args.service:
            policies = self.find_policies_by_entity([service], entity_type, entity_value)
            if policies:
                logger.info(f"Found {len(policies)} policies for type:[{entity_type}] value:[{entity_value}]")
                for policy in policies:
                    logger.info(policy)
            else:
                logger.info(f"No policies found for type:[{entity_type}] value:[{entity_value}]")

    @staticmethod
    def get_non_empty_argument(args, *args_names):
        for arg_name in args_names:
            if getattr(args, arg_name):
                return arg_name, getattr(args, arg_name)
        raise Exception("Exactly one of the following arguments must be provided: {}".format(", ".join(args_names)))

    def find_policies_by_entity(self, services, entity_type, entity_value):
        import requests

        auth = (RANGER_USER, RANGER_PASSWORD)
        headers = {
            'Content-Type': 'application/json'
        }
        policies = []

        try:
            for service in services:
                url = f'{RANGER_URL}/service/public/v2/api/service/{service}/policy?{entity_type}={entity_value}'
                logger.info(url)
                response = requests.get(url, headers=headers, auth=auth)
                response.raise_for_status()
                policies.extend(response.json())
        except Exception as e:
            logger.warning(f"Error fetching policies: {e}")
        return policies

    def update_policy_by_id(self, policy_id, policy):
        self.client.update_policy_by_id(policy_id, policy)


def init_parse():
    parser = argparse.ArgumentParser(description='Apache Ranger Policy Manager')
    subparsers = parser.add_subparsers(dest='command', required=True)

    grant_parser = subparsers.add_parser('grant', help='Grant access to a policy')
    grant_parser.add_argument('--service', nargs='+', default=['cm_hive'], help='Service name')
    grant_parser.add_argument('--name', help='Policy name')
    grant_parser.add_argument('--policy_type', required=True, choices=["normal", "mask", "row-filter"],
                              help='Policy type')
    grant_parser.add_argument('--catalog', nargs='*', default=[], help='List of catelogs')
    grant_parser.add_argument('--database', required=True, help='Database name')
    grant_parser.add_argument('--table', required=True, help='Table name')
    grant_parser.add_argument('--columns', nargs='+', help='List of columns')
    grant_parser.add_argument('--accesses', nargs='+', default=['select'], help='List of accesses')
    grant_parser.add_argument('--users', nargs='*', default=[], help='List of users')
    grant_parser.add_argument('--groups', nargs='*', default=[], help='List of groups')
    grant_parser.add_argument('--roles', nargs='*', default=[], help='List of roles')
    grant_parser.add_argument('--mask_type', default='MASK_HASH', help='Mask type for data mask policy')
    grant_parser.add_argument('--row_filter', help='Row filter expression for row filter policy')

    revoke_parser = subparsers.add_parser('revoke', help='Revoke access to a policy')
    revoke_parser.add_argument('--service', nargs='+', default=['cm_hive'], help='Service name')
    revoke_parser.add_argument('--name', help='Policy name')
    revoke_parser.add_argument('--policy_type', required=True, choices=["normal", "mask", "row-filter"],
                               help='Policy type')
    revoke_parser.add_argument('--catalog', nargs='*', default=[], help='List of catelogs')
    revoke_parser.add_argument('--database', required=True, help='Database name')
    revoke_parser.add_argument('--table', required=True, help='Table name')
    revoke_parser.add_argument('--columns', nargs='+', help='List of columns')
    revoke_parser.add_argument('--accesses', nargs='+', default=['select'], help='List of accesses')
    revoke_parser.add_argument('--users', nargs='*', default=[], help='List of users')
    revoke_parser.add_argument('--groups', nargs='*', default=[], help='List of groups')
    revoke_parser.add_argument('--roles', nargs='*', default=[], help='List of roles')
    revoke_parser.add_argument('--mask_type', default='MASK_HASH', help='Mask type for data mask policy')
    revoke_parser.add_argument('--row_filter', help='Row filter expression for row filter policy')

    delete_parser = subparsers.add_parser('delete', help='Delete a policy')
    delete_parser.add_argument('--service', nargs='+', default=['cm_hive'], help='Service name')
    delete_parser.add_argument('--catalog', nargs='*', default=[], help='List of catelogs')
    delete_parser.add_argument('--policy_name', help='need to delete Policy name')
    delete_parser.add_argument('--user', help='User name to revoke policies')
    delete_parser.add_argument('--group', help='group name to revoke policies')
    delete_parser.add_argument('--role', help='role name to revoke policies')

    search_parser = subparsers.add_parser('search', help='Find policies by user')
    search_parser.add_argument('--service', nargs='+', default=['cm_hive'], help='Service name')
    search_parser.add_argument('--catalog', nargs='*', default=[], help='List of catelogs')
    search_parser.add_argument('--user', help='User name to find policies for')
    search_parser.add_argument('--group', help='Group name to find policies for')
    search_parser.add_argument('--role', help='Role name to find policies for')

    # 创建角色的子命令
    create_role_parser = subparsers.add_parser('create_role', help='Create a new role')
    create_role_parser.add_argument('--service', default='cm_hive',  help='Service name')
    create_role_parser.add_argument('--role_name', required=True, help='Name of the role to create')
    create_role_parser.add_argument('--users', nargs='*', default=[], help='List of users to add to the role')
    create_role_parser.add_argument('--groups', nargs='*', default=[], help='List of groups to add to the role')
    create_role_parser.add_argument('--roles', nargs='*', default=[], help='List of roles to add to the role')

    # 查看角色的子命令
    view_role_parser = subparsers.add_parser('search_role', help='search details of a role')
    view_role_parser.add_argument('--service', default='cm_hive',  help='Service name')
    view_role_parser.add_argument('--role_name', required=True, help='Name of the role to view')

    # 将用户添加到角色的子命令
    add_user_to_role_parser = subparsers.add_parser('add_entity_to_role', help='Add users to a role')
    add_user_to_role_parser.add_argument('--service', default='cm_hive',  help='Service name')
    add_user_to_role_parser.add_argument('--role_name', required=True, help='Name of the role')
    add_user_to_role_parser.add_argument('--users', nargs='*', default=[], help='List of users to add to the role')
    add_user_to_role_parser.add_argument('--groups', nargs='*', default=[], help='List of groups to add to the role')
    add_user_to_role_parser.add_argument('--roles', nargs='*', default=[], help='List of roles to add to the role')

    # 从角色中移除用户的子命令
    remove_user_from_role_parser = subparsers.add_parser('remove_entity_from_role', help='Remove users from a role')
    remove_user_from_role_parser.add_argument('--service', default='cm_hive',  help='Service name')
    remove_user_from_role_parser.add_argument('--role_name', required=True, help='Name of the role')
    remove_user_from_role_parser.add_argument('--users', nargs='*', default=[], help='List of users to add to the role')
    remove_user_from_role_parser.add_argument('--groups', nargs='*', default=[], help='List of groups to add to the role')
    remove_user_from_role_parser.add_argument('--roles', nargs='*', default=[], help='List of roles to add to the role')

    return parser.parse_args()


def run(args):
    manager = RangerManager(RANGER_URL, RANGER_USER, RANGER_PASSWORD)

    command_map = {
        'grant': manager.policy.grant_access,
        'revoke': manager.policy.revoke_access,
        'search': manager.policy.search_entity_policy,
        'delete': manager.policy.delete_entity_access,
        'create_role': manager.role.create_role,
        'search_role': manager.role.search_role,
        'add_entity_to_role': manager.role.add_entity_to_role,
        'remove_entity_from_role': manager.role.remove_entity_from_role,
        'remove_user_from_all_roles': manager.role.remove_user_from_all_roles
    }
    logger.info(args)
    command = args.command
    if command in command_map:
        command_map[command](args)
    else:
        logger.warning(f"Unknown command: {command}")


def main():
    run(init_parse())


if __name__ == '__main__':
    main()
