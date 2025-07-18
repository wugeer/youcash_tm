import random
import string
import argparse
from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE, ALL_ATTRIBUTES
from ldap3.core.exceptions import LDAPException
# from youcash_hash import youcash_hash
from .youcash_ranger_v2 import run as delete_strategy

# 从环境变量中获取LDAP配置
import os
LDAP_SERVER = os.getenv("LDAP_SERVER", "").split(",") if os.getenv("LDAP_SERVER") else []
USER_DN = os.getenv("LDAP_USER_DN", "")
DEFAULT_PASSWORD = os.getenv("LDAP_DEFAULT_PASSWORD", "")

import logging
logger = logging.getLogger(__name__)


class LDAPConnection:
    def __init__(self, servers, user_dn, password):
        self.servers = servers
        self.user_dn = user_dn
        self.password = password
        self.connection = self.connect()

    def connect(self):
        for server_address in self.servers:
            try:
                server = Server(server_address, get_info=ALL)
                connection = Connection(server, user=self.user_dn, password=self.password, auto_bind=True)
                logger.info(f"Connected to {server_address}")
                return connection
            except Exception:
                logger.warning(f"Failed to connect to {server_address}")
        raise Exception("Failed to connect to any LDAP server")

class LDAPOperations:
    def __init__(self, connection):
        self.connection = connection

    def search(self, search_base, search_filter, attributes):
        try:
            self.connection.search(search_base, search_filter, attributes=attributes)
            return self.connection.entries
        except LDAPException as e:
            logger.error(f"Failed to search: {e}")
            return None

    def create_entry(self, dn, attributes):
        try:
            self.connection.add(dn, attributes=attributes)
            logger.info(f"Entry {dn} created successfully")
        except LDAPException as e:
            logger.error(f"Failed to create entry {dn}: {e}")

    def delete_entry(self, dn):
        try:
            self.connection.delete(dn)
            logger.info(f"Entry {dn} deleted successfully")
        except LDAPException as e:
            logger.error(f"Failed to delete entry {dn}: {e}")

    def modify_entry(self, dn, changes):
        try:
            self.connection.modify(dn, changes)
            logger.info(f"Entry {dn} modified successfully")
        except LDAPException as e:
            logger.error(f"Failed to modify entry {dn}: {e}")

class LDAPUserManager(LDAPOperations):
    def search_user(self, user_name, attributes=ALL_ATTRIBUTES):
        search_base = 'ou=People,dc=youcash,dc=com'
        search_filter = f'(uid={user_name})'
        return self.search(search_base, search_filter, attributes)

    def search_user_all(self, attributes=ALL_ATTRIBUTES):
        search_base = 'ou=People,dc=youcash,dc=com'
        search_filter = '(objectClass=posixAccount)'
        return self.search(search_base, search_filter, attributes)

    def create_user(self, user_dn, attributes):
        self.create_entry(user_dn, attributes)

    def delete_user(self, user_dn):
        self.delete_entry(user_dn)

    def change_password(self, user_dn, new_password):
        changes = {'userPassword': [(MODIFY_REPLACE, [new_password])]}
        self.modify_entry(user_dn, changes)


class LDAPGroupManager(LDAPOperations):
    def search_group(self, group_name, attributes=ALL_ATTRIBUTES):
        search_base = 'ou=Group,dc=youcash,dc=com'
        search_filter = f'(&(objectClass=posixGroup)(cn={group_name}))'
        return self.search(search_base, search_filter, attributes)

    def search_group_all(self, attributes = ALL_ATTRIBUTES): 
        base_dn = 'ou=Group,dc=youcash,dc=com'
        search_filter = '(objectClass=posixGroup)'
        return self.search(base_dn, search_filter, attributes)

    def create_group(self, group_dn, attributes):
        self.create_entry(group_dn, attributes)

    def delete_group(self, group_dn):
        self.delete_entry(group_dn)

    def add_user_to_group(self, group_dn, user_dn):
        changes = {'memberUid': [(MODIFY_ADD, user_dn)]}
        self.modify_entry(group_dn, changes)

    def remove_user_from_group(self, group_dn, user_dn):
        changes = {'memberUid': [(MODIFY_DELETE, user_dn)]}
        self.modify_entry(group_dn, changes)

def get_max_attribute(connection, search_base, search_filter, attribute):
    connection.search(search_base, search_filter, attributes=[attribute])
    max_value = 0
    for entry in connection.entries:
        value = int(entry[attribute].value)
        if value > max_value:
            max_value = value
    return max_value

import argparse

def init_parse():
    parser = argparse.ArgumentParser(description="LDAP Operations")
    parser.add_argument("action", choices=["create_user", "delete_user", "add_user_to_group", "remove_user_from_group", "create_group", "delete_group", "search_user", "search_group", "change_password", "search_user_all", "search_group_all"], help="Action to perform")
    parser.add_argument("--user", help="Username")
    parser.add_argument("--group", help="Group name")
    parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")
    parser.add_argument("--new_password", help="New password")

    return parser.parse_args()

def main():
    args = init_parse()
    run(args)

def run(args):
    connection = LDAPConnection(args.servers, args.user_dn, args.password)
    user_manager = LDAPUserManager(connection.connection)
    group_manager = LDAPGroupManager(connection.connection)

    actions = {
        "create_user": create_user,
        "delete_user": delete_user,
        "add_user_to_group": add_user_to_group,
        "remove_user_from_group": remove_user_from_group,
        "create_group": create_group,
        "delete_group": delete_group,
        "search_user": search_user,
        "search_user_all": search_user_all,
        "search_group": search_group,
        "search_group_all": search_group_all,
        "change_password": change_password,
    }

    if args.action in actions:
        res = actions[args.action](args, user_manager, group_manager, connection)
        if args.action.startswith('search_'):
            print(res)
    else:
        raise Exception("Invalid action")


def create_user(args, user_manager, group_manager, connection):
    if not args.user:
        raise ValueError("create_user requires --user")
    if user_manager.search_user(args.user):
        logger.info(f"user:[{args.user}] already exists, igonre create")
        return
    logger.info(f"start to create user:[args.user]")
    user_dn = f'uid={args.user},ou=People,dc=youcash,dc=com'
    group_dn = f'cn={args.user},ou=Group,dc=youcash,dc=com'
    gidNumber = get_max_attribute(connection.connection, 'ou=Group,dc=youcash,dc=com', '(objectClass=posixGroup)', 'gidNumber') + 1
    group_attributes = {'objectClass': ['posixGroup', 'top'], 'cn': args.user, 'gidNumber': str(gidNumber)}
    group_manager.create_group(group_dn, group_attributes)

    uidNumber = get_max_attribute(connection.connection, 'ou=People,dc=youcash,dc=com', '(objectClass=posixAccount)', 'uidNumber') + 1
    user_password = "".join(random.sample(string.ascii_letters+string.digits, 8)) if not args.new_password else args.new_password
    logger.info(f"hash user:[{args.user}] with password:[{user_password}]")
    # user_password = youcash_hash.hash(args.user)
    user_attributes = {'objectClass': ['inetOrgPerson', 'posixAccount', 'top'], 'sn': args.user, 'cn': args.user, 'uid': args.user, 'uidNumber': str(uidNumber), 'gidNumber': group_attributes['gidNumber'], 'loginShell': '/bin/bash', 'homeDirectory': f'/home/{args.user}', 'userPassword': user_password}
    user_manager.create_user(user_dn, user_attributes)

    args.group = args.group or []
    args.group.extend([args.user]) 
    for group in args.group:
        group_dn = f'cn={group},ou=Group,dc=youcash,dc=com'
        logger.info(f"add user:[{args.user}] to group:[{group}]")
        group_manager.add_user_to_group(group_dn, args.user)

def delete_user(args, user_manager, group_manager, connection):
    if not args.user:
        raise ValueError("delete_user requires --user")
    user_dn = f'uid={args.user},ou=People,dc=youcash,dc=com'
    user_manager.delete_user(user_dn)
    group_dn = f'cn={args.user},ou=Group,dc=youcash,dc=com'
    group_manager.delete_group(group_dn)
    
    logger.info(f"start to revoke all privileges of the user=[{args.user}]")
    user_args = argparse.Namespace(
        command='delete',
        service=['cm_hive','doris'],
        user=args.user,
        group=[],
        role=[],
        policy_name=[],
    )
    delete_strategy(user_args)

    logger.info(f"start to revoke all privileges of the group=[{args.user}]")
    group_args = argparse.Namespace(
        command='delete',
        service=['cm_hive','doris'],
        user=[],
        group=args.user,
        role=[],
        policy_name=[],
    )
    delete_strategy(group_args)

    logger.info(f"start to revoke user:[only_read] select privileges of the database:[{args.user}]")
    only_read_args = argparse.Namespace(
        command='revoke',
        name=None,
        service=['cm_hive','doris'],
        catalog=['cdp_hive'],
        policy_type='normal',
        users=[],
        groups=[],
        roles=['only_read'],
        accesses=['select'],
        database=args.user,
        table='*',
        columns=['*'],
        policy_name=[],
    )
    delete_strategy(only_read_args)


def add_user_to_group(args, user_manager, group_manager, connection):
    if not args.user or not args.group:
        raise ValueError("add_user_to_group requires --user and --group")
    for group in args.group:
        group_dn = f'cn={group},ou=Group,dc=youcash,dc=com'
        logger.info(f"add user:[{args.user}] to group:[{group}]")
        group_manager.add_user_to_group(group_dn, args.user)

def remove_user_from_group(args, user_manager, group_manager, connection):
    if not args.user or not args.group:
        raise ValueError("remove_user_from_group requires --user and --group")
    for group in args.group:
        group_dn = f'cn={group},ou=Group,dc=youcash,dc=com'
        logger.info(f"remove user:[{args.user}] from group:[{group}]")
        group_manager.remove_user_from_group(group_dn, args.user)

def create_group(args, user_manager, group_manager, connection):
    if not args.group:
        raise ValueError("create_group requires --group")
    group_dn = f'cn={args.group},ou=Group,dc=youcash,dc=com'
    gidNumber = get_max_attribute(connection.connection, 'ou=Group,dc=youcash,dc=com', '(objectClass=posixGroup)', 'gidNumber') + 1
    group_attributes = {'objectClass': ['posixGroup', 'top'], 'cn': args.group, 'gidNumber': str(gidNumber)}
    group_manager.create_group(group_dn, group_attributes)

def delete_group(args, user_manager, group_manager, connection):
    if not args.group:
        raise ValueError("delete_group requires --group")
    group_dn = f'cn={args.group},ou=Group,dc=youcash,dc=com'
    group_manager.delete_group(group_dn)

    logger.info(f"start to revoke all privileges of the group=[{args.group}]")
    group_args = argparse.Namespace(
        command='delete',
        service=['cm_hive', 'doris'],
        user=[],
        group=args.group,
        role=[],
        policy_name=[],
    )
    delete_strategy(group_args)

def search_user(args, user_manager, group_manager, connection):
    if not args.user:
        raise ValueError("search_user requires --user")
    result = user_manager.search_user(args.user)
    if result:
        return [entry.cn for entry in result]
    else:
        logger.warning(f"找不到uid={args.user}的用户")

def search_user_all(args, user_manager, group_manager, connection):
    result = user_manager.search_user_all(['cn'])
    if result:
        return [entry.cn for entry in result]
    else:
        logger.warning(f"查询不到ldap的任意一个posixAccount用户")

def search_group(args, user_manager, group_manager, connection):
    if not args.group:
        raise ValueError("search_group requires --group")
    result = group_manager.search_group(args.group, ['cn', 'memberUid'])
    if result:
        return [(entry.cn, entry.memberUid) for entry in result]
    else:
        logger.warning(f"找不到cn={args.group}的组")

def search_group_all(args, user_manager, group_manager, connection):
    result = group_manager.search_group_all(['cn'])
    if result:
        return [entry.cn for entry in result]
    else:
        logger.warning(f"查询不到ldap 的任意一个posixGroup组")

def change_password(args, user_manager, group_manager, connection):
    if not args.user:
        raise ValueError("change_password requires --user")
    if not args.new_password:
        raise ValueError("change_password requires --new_password")
    user_dn = f'uid={args.user},ou=People,dc=youcash,dc=com'
    user_manager.change_password(user_dn, args.new_password)

if __name__ == "__main__":
    main()
