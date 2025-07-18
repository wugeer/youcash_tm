import argparse
import subprocess
import os
from .youcash_ranger_v2 import run as ranger_run
from .ldap3_script import run as ldap_run
from pyhive import hive
from app.core.config import DATABASE_URL


# 从环境变量中获取LDAP配置
import os
LDAP_SERVER = os.getenv("LDAP_SERVER", "").split(",") if os.getenv("LDAP_SERVER") else []
USER_DN = os.getenv("LDAP_USER_DN", "")
DEFAULT_PASSWORD = os.getenv("LDAP_DEFAULT_PASSWORD", "")

import logging
logger = logging.getLogger(__name__)
 
class YoucashUtils:
    def __init__(self, user_name, database_name):
        self.user_name =  user_name
        self.database_name = database_name

    def find_user_password(self, log_file):
        password = None
        with open(log_file, 'r') as f:
            for line in f.readlines()[-500:][::-1]:
                if 'password:[' in line and self.user_name in line:
                    password = line.split('password:[')[-1].split("]")[0]
                    break
        return password

    @staticmethod
    def search_user(user_name):
        if not user_name:
            raise Exception('查询用户信息时请传入用户名')
        import psycopg2
        from urllib.parse import urlparse
        
        # 解析数据库URL
        result = urlparse(DATABASE_URL)
        username = result.username
        password = result.password
        database = result.path[1:]  # 去掉开头的'/'
        hostname = result.hostname
        port = result.port
        
        with psycopg2.connect(
            database=database,
            user=username,
            password=password,
            host=hostname,
            port=port
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"""select first_name, last_name, email from public.ab_user where username='{user_name}' limit 1""")
                for record in cursor:
                    return record
    
    def changer_airflow_user_password(self, new_password):
        o_user = YoucashUtils.search_user(self.user_name)
        if not o_user:
            logger.info(f'用户{username}不存在，不需要修改密码')
            return
        first_name, last_name, email = o_user
        command = """
        set -ex && source /app/airflow2.2.3/airflow2_env/bin/activate && \\
        airflow users delete -u "{user_name}" && \\
        airflow users create -u "{user_name}" -f "{first_name}" -l "{last_name}" -r "{user_name}" -e "{email}" -p '{new_password}' && \\
        airflow users add-role -r base -u "{user_name}"
        """.format(user_name=self.user_name, first_name=first_name, last_name=last_name, email=email, new_password=new_password)
        logger.info(f"执行命令:{command}")
        result = subprocess.run(["ssh","hadoop@zyxfcdp20", command], capture_output=True, text=True)
        logger.info(f"执行结果:{result.stdout}")
        if not result.stdout:
            raise Exception("修改airflow用户的密码应该有执行输出，请检查")
        
    def delete_airflow_rbac(self,):
        command = f"""
    set -ex && source /app/airflow2.2.3/airflow2_env/bin/activate && \
        airflow users delete -u "{self.user_name}" && \
        airflow connections delete {self.user_name}
    """
        logger.info(f"执行命令:{command}")
        result = subprocess.run(["ssh","hadoop@zyxfcdp20", command], capture_output=True, text=True)
        logger.info(f"执行结果:{result.stdout}")
        if not result.stdout:
            raise Exception("删除airflow用户应该有执行输出，请检查")
    
    def insert_airflow_rbac(self, log_file):
        user_pass = self.find_user_password(log_file)
        if not user_pass:
            raise Exception("无法找到用户密码")
        import random, string
        rand_str = "".join(random.choices(string.ascii_letters + string.digits, k=5))
        hs2_port=10000 
        hs2_host="zyxfcdp01"
        tez_queue_name = f'root.users.hive.{self.user_name.split("_")[-1]}' if '_' in self.user_name else 'root.default'
        command = """
        set -ex && source /app/airflow2.2.3/airflow2_env/bin/activate && \\
        airflow roles create "{user_name}" && \\
        airflow users create -u "{user_name}" -f "{user_name}" -l "{part_name}" -r "{user_name}" -e "{user_name}@{rand_str}.youcash.com" -p '{user_pass}' && \\
        airflow users add-role -r base -u "{user_name}"  && \\
        airflow connections add --conn-type hiveserver2 --conn-host "{hs2_host}" --conn-login "{user_name}" --conn-password '{user_pass}' --conn-port "{hs2_port}" --conn-schema "default" --conn-extra '{{"use_beeline":true,"auth":"","hive_cli_params":"--hiveconf tez.queue.name={tez_queue_name}"}}' \\
        {user_name}
        """.format(part_name=self.user_name.split("_")[-1] if '_' in self.user_name else self.user_name,tez_queue_name=tez_queue_name, user_name=self.user_name, rand_str=rand_str, user_pass=user_pass, hs2_host=hs2_host, hs2_port=hs2_port)
        logger.info(f"执行命令:{command}")
        result = subprocess.run(["ssh","hadoop@zyxfcdp20", command], capture_output=True, text=True)
        logger.info(f"执行结果:{result.stdout}")
        if not result.stdout:
            raise Exception("创建airflow用户应该有执行输出，请检查")
    
    def set_hdfs_space_quota(self, quota):
        env = os.environ.copy()
        env["HADOOP_USER_NAME"] = 'hdfs'
        command = ["hdfs","dfsadmin","-setSpaceQuota", f"{int(quota) if quota else 100}G", f"/user/hive/warehouse/{self.database_name}.db"]
        logger.info(f"执行命令:{' '.join(command)}")
        result = subprocess.run(command, env=env, capture_output=True, text=True)
        logger.info(f"执行结果:{result.stdout}")


class HiveOperation:
    def __init__(self,):
        self.host = 'zyxfcdp01'
        self.port = 10000
        self.username = 'airflow'
        self.password = 'airflow'

    def create_database(self, database_name):
        self.execute_sql(f"create database if not exists {database_name}")

    def drop_database(self, database_name):
        self.execute_sql(f"drop database if exists {database_name}")

    def execute_sql(self, sql):
        try:
            with hive.Connection(host=self.host, port=self.port, username=self.username, password=self.password, auth='LDAP') as conn:
                with conn.cursor() as cursor:
                    logger.info(f"开始执行sql:[{sql}]")
                    cursor.execute(sql)
                    logger.info(f"执行sql:[{sql}]成功")
        except Exception:
            logger.warning(f"Failed to connect to {server_address}")

def init_parse():
    parser = argparse.ArgumentParser(description='LDAP and Ranger Manager')
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

    create_user_parser = subparsers.add_parser('create_user', help='create user')
    create_user_parser.add_argument('--service', nargs='+', default=['cm_hive'], help='Service name')
    create_user_parser.add_argument('--catalog', nargs='*', default=[], help='List of catelogs')
    create_user_parser.add_argument('--user', required=True, help='User name')
    create_user_parser.add_argument('--group', nargs='*', default=[], help='create user will attach in this list of Group names')
    create_user_parser.add_argument('--roles', nargs='*', default=[], help='create user will attach in this list of role names')
    create_user_parser.add_argument('--department_name', help='create user in which department name')
    create_user_parser.add_argument('--quota', help='person database space quota')
    create_user_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    create_user_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    create_user_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    delete_user_parser = subparsers.add_parser('delete_user', help='delete user')
    delete_user_parser.add_argument('--user', required=True, help='User name')
    delete_user_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    delete_user_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    delete_user_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    # add_user_to_group_parser = subparsers.add_parser('add_user_to_group', help='add user to target groups')
    # add_user_to_group_parser.add_argument('--user', required=True, nargs='+', default=[], help='User name')
    # add_user_to_group_parser.add_argument('--group', required=True, nargs='+', default=[], help='list of target Group names')
    # add_user_to_group_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    # add_user_to_group_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    # add_user_to_group_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    # remove_user_from_group_parser = subparsers.add_parser('remove_user_from_group', help='remove user from target groups')
    # remove_user_from_group_parser.add_argument('--user', required=True, nargs='+', default=[], help='User name')
    # remove_user_from_group_parser.add_argument('--group', required=True, nargs='+', default=[], help='list of target Group names')
    # remove_user_from_group_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    # remove_user_from_group_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    # remove_user_from_group_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    # create_group_parser = subparsers.add_parser('create_group', help='create group')
    # create_group_parser.add_argument('--group', required=True, help='create Group name')
    # create_group_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    # create_group_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    # create_group_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    # delete_group_parser = subparsers.add_parser('delete_group', help='delete group')
    # delete_group_parser.add_argument('--group', required=True, help='delete Group name')
    # delete_group_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    # delete_group_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    # delete_group_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    search_user_parser = subparsers.add_parser('search_user', help='search user')
    search_user_parser.add_argument('--user', required=True, help='search user name')
    search_user_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    search_user_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    search_user_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    # search_group_parser = subparsers.add_parser('search_group', help='search group')
    # search_group_parser.add_argument('--group', required=True, help='search Group name')
    # search_group_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    # search_group_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    # search_group_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    change_password_parser = subparsers.add_parser('change_password', help='change ldap user password')
    change_password_parser.add_argument('--user', required=True, help='ldap user name')
    change_password_parser.add_argument("--new_password", help="New password")
    change_password_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    change_password_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    change_password_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    search_user_all_parser = subparsers.add_parser('search_user_all', help='search all user')
    search_user_all_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    search_user_all_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    search_user_all_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    # search_group_all_parser = subparsers.add_parser('search_group_all', help='search all group')
    # search_group_all_parser.add_argument("--servers", nargs='+', default=LDAP_SERVER, help="LDAP servers")
    # search_group_all_parser.add_argument("--user_dn", default=USER_DN, help="User DN")
    # search_group_all_parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")

    set_space_quota_parser = subparsers.add_parser('set_space_quota', help='set hdfs space quota')
    set_space_quota_parser.add_argument('--database', required=True, help='user database name')
    set_space_quota_parser.add_argument('--quota', help='database space quota')

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

    # 从所有角色中移除用户
    remove_user_all_parser = subparsers.add_parser('remove_user_from_all_roles', help='Remove users from all roles')
    remove_user_all_parser.add_argument('--service', default='cm_hive',  help='Service name')
    remove_user_all_parser.add_argument('--users', nargs='+', required=True, help='the users to remove from all roles')
    remove_user_all_parser.add_argument('--groups', nargs='*', default=[], help='the groups to remove from all roles')
    remove_user_all_parser.add_argument('--roles', nargs='*', default=[], help='the roles to remove from all roles')

    return parser.parse_args()

def main():
    args = init_parse()

    ranger_action = ('grant', 'revoke', 'search', 'delete', 'create_role', 'search_role', 'add_entity_to_role', 'remove_entity_from_role', 'remove_user_from_all_roles') 
    ldap_action = ("create_user", "delete_user", "search_user", "change_password", "search_user_all") 

    if args.command in ldap_action:
        args.action = args.command
        if not hasattr(args, 'new_password'):
            args.new_password = None
        if args.command == 'create_user' and args.department_name:
            args.user = args.user + '_' + args.department_name[:2]
            if args.department_name not in args.roles:
                args.roles.append(args.department_name)
        logger.info(args)
        ldap_run(args)
        if args.command == 'create_user':
            for role_name in args.roles:
                # 这里改为将用户加到部门组
                create_role_args = argparse.Namespace(
                    command='create_role',
                    service='cm_hive',
                    role_name=role_name,
                    users=[args.user],
                    groups=[],
                    roles=[],
                )
                ranger_run(create_role_args)
            obj = HiveOperation()
            obj.create_database(args.user)
            logger.info(f"grant all privileges on personal database [{args.user}] to user:[{args.user}]")
            grant_args = argparse.Namespace(
                command='grant',
                name=None,
                service=['cm_hive', 'doris'],
                catalog=['cdp_hive'],
                policy_type='normal',
                database=args.user,
                table='*',
                columns=['*'],
                accesses=['all'],
                users=[args.user],
                groups=[],
                roles=[],
                mask_type=None,
                row_filter=None
            )
            ranger_run(grant_args)
            # 配置只读角色
            grant_args = argparse.Namespace(
                command='grant',
                name=None,
                service=['cm_hive', 'doris'],
                catalog=['cdp_hive'],
                policy_type='normal',
                database=args.user,
                table='*',
                columns=['*'],
                accesses=['select'],
                users=[],
                groups=[],
                roles=["only_read"],
                mask_type=None,
                row_filter=None
            )
            ranger_run(grant_args)
            logger.info(f"set hdfs quota:[{args.quota if args.quota else 100}]G on personal database [{args.user}]")
            util_obj = YoucashUtils(args.user, args.user)
            util_obj.set_hdfs_space_quota(args.quota)
            logger.info(f"create yewu airflow account for user:[{args.user}]")
            util_obj.insert_airflow_rbac(LOG_FILE)
            # role_args = argparse.Namespace(
            #     command='add_user_to_role',
            #     service='cm_hive',
            #     users=[args.user],
            #     groups=[],
            #     roles=[],
            #     role_name='default_select',
            # )
            # role_run(role_args)
        elif args.command == 'delete_user':
            remove_user_from_all_role_args = argparse.Namespace(
                command='remove_user_from_all_roles',
                service='cm_hive',
                users=[args.user],
                groups=[],
                roles=[],
            )
            ranger_run(remove_user_from_all_role_args)
            # 删除个人数据库
            obj = HiveOperation()
            obj.drop_database(args.user)
            # 前面的ldap_run删除ldap账号时会自动删除对应的ranger权限，因此这里不需要单独操作ranger:)
            # 删除业务airflow中这个用户的账号
            util_obj = YoucashUtils(args.user, args.user)
            util_obj.delete_airflow_rbac()
        elif args.command == 'change_password':
            util_obj = YoucashUtils(args.user, args.user)
            util_obj.changer_airflow_user_password(args.new_password)
    elif args.command in ranger_action:
        # run ranger operation
        ranger_run(args)
    elif args.command in ('set_space_quota'):
        # set space quota here
        util_obj = YoucashUtils(args.database, args.database)
        util_obj.set_hdfs_space_quota(args.quota)
    else:
        logger.warning("未知action:[{args.command}]")

if __name__ == "__main__":
    main()
