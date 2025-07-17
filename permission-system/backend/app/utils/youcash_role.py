from apache_ranger.client.ranger_client import RangerClient
import logging
import argparse
from pathlib import Path
from datetime import datetime

# 从环境变量中获取Ranger配置
import os
RANGER_URL = os.getenv("RANGER_URL", "")
RANGER_USER = os.getenv("RANGER_USER", "")
RANGER_PASSWORD = os.getenv("RANGER_PASSWORD", "")

logger = logging.getLogger(__name__)

class RangerRoleManager:
    def __init__(self, ranger_url, ranger_user, ranger_password):
        self.client = RangerClient(ranger_url, (ranger_user, ranger_password))

    def search_roles_with_user(self, user_name):
        import requests
        auth = (RANGER_USER, RANGER_PASSWORD)
        headers = {
            'Content-Type': 'application/json'
        }
        
        url = f'{RANGER_URL}/service/public/v2/api/roles'
        roles = []
        try:
            response = requests.get(url, headers=headers, auth=auth, params={'userName':user_name})
            response.raise_for_status()
            roles.extend(response.json())
        except Exception as e:
            logger.warning(f"Error fetching roles with user name:{user_name}: {e}")
        return roles 

    def remove_user_from_all_roles(self, args, ):
        for user in args.users:
            for role in self.search_roles_with_user(user):
                args.role_name = role.name
                logger.info(f"start to remove user {user} from role {role.name}")
                self.remove_user_from_role(args, role)

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
            args.groups = []
            logger.info(f"目标角色已经存在，开始确保指定的用户、组在角色中")
            self.add_user_to_role(args, existing_role)
        else:
            role = {
                "name": args.role_name,
                "users": [{"name": user, "isAdmin": False} for user in (args.users or [])],
                "groups": [{"name": group, "isAdmin": False} for group in (args.groups or [])],
                "roles": [],
            }
            self.client.create_role(args.service, role)
            logger.info(f"Created role: {role}")

    def add_user_to_role(self, args, existing_role=None):
        role_name = args.role_name
        add_users = set(args.users)
        add_groups = set(args.groups) if hasattr(args, "groups") else set()
        existing_role = existing_role or self.search_role(args)
        new_users, new_groups = [], []

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

            if new_users:
                o_users.extend(new_users)
            if new_groups:
                o_groups.extend(new_groups)

            if new_users + new_groups:
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
                "roles": [],
            }
            self.client.create_role(args.service, role)
            logger.info(f"Created role: {role}")

    def remove_user_from_role(self, args, existing_role=None):
        role_name = args.role_name
        to_del_users = args.users
        existing_role = existing_role or self.search_role(args)
        actual_del_users = []

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
                self.client.update_role(existing_role["id"], existing_role)
                logger.info(f"Updated role: {existing_role}")
            else:
                logger.info(f"No updates needed for role: {role_name}")
        else:
            logger.info(f"No role found with name: {role_name}")

def init_parse():
    parser = argparse.ArgumentParser(description='Apache Ranger Role Manager')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # 创建角色的子命令
    create_parser = subparsers.add_parser('create_role', help='Create a new role')
    create_parser.add_argument('--service', default='cm_hive',  help='Service name')
    create_parser.add_argument('--role_name', required=True, help='Name of the role to create')
    create_parser.add_argument('--users', nargs='*', default=[], help='List of users to add to the role')
    create_parser.add_argument('--groups', nargs='*', default=[], help='List of groups to add to the role')

    # 查看角色的子命令
    view_parser = subparsers.add_parser('search_role', help='search details of a role')
    view_parser.add_argument('--service', default='cm_hive',  help='Service name')
    view_parser.add_argument('--role_name', required=True, help='Name of the role to view')

    # 将用户添加到角色的子命令
    add_user_parser = subparsers.add_parser('add_user_to_role', help='Add users to a role')
    add_user_parser.add_argument('--service', default='cm_hive',  help='Service name')
    add_user_parser.add_argument('--role_name', required=True, help='Name of the role')
    add_user_parser.add_argument('--users', nargs='+', required=True, help='List of users to add to the role')

    # 从角色中移除用户的子命令
    remove_user_parser = subparsers.add_parser('remove_user_from_role', help='Remove users from a role')
    remove_user_parser.add_argument('--service', default='cm_hive',  help='Service name')
    remove_user_parser.add_argument('--role_name', required=True, help='Name of the role')
    remove_user_parser.add_argument('--users', nargs='+', required=True, help='List of users to remove from the role')

    # 从所有角色中移除用户
    remove_user_all_parser = subparsers.add_parser('remove_user_from_all_roles', help='Remove users from all roles')
    remove_user_all_parser.add_argument('--service', default='cm_hive',  help='Service name')
    remove_user_all_parser.add_argument('--users', nargs='+', required=True, help='the users to remove from all roles')
    remove_user_all_parser.add_argument('--groups', nargs='*', default=[], help='the groups to remove from all roles')
    remove_user_all_parser.add_argument('--roles', nargs='*', default=[], help='the groups to remove from all roles')

    return parser.parse_args()


def run(args):
    manager = RangerRoleManager(RANGER_URL, RANGER_USER, RANGER_PASSWORD)

    command_map = {
        'create_role': manager.create_role,
        'search_role': manager.search_role,
        'add_user_to_role': manager.add_user_to_role,
        'remove_user_from_role': manager.remove_user_from_role,
        'remove_user_from_all_roles': manager.remove_user_from_all_roles,
    }

    command = args.command
    if command in command_map:
        command_map[command](args)
    else:
        logger.error(f"Unknown command: {command}")


def main():
    run(init_parse())

if __name__ == '__main__':
    main()
