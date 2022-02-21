import os
import time
import threading
from flask import request, session
from .redis_connect import RedisConnect
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from .tools import handle_abnormal
from .db_connect import DBConnect
import logging
import platform

logging.basicConfig(
    level=logging.WARNING,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)


def set_token_session(app, verify, per_defaults: list, whitelist: list = []):
    app.secret_key = 'sdfj48@$NF94@4dfsdf&)$#*'  # 配置session key

    @app.before_request
    def base_auth():
        """验证用户是否有访问页面的权限"""
        for path in whitelist:
            request_path = request.path
            path_list = path.split('/<')
            if len(path_list) != 1:
                path = path_list[0]
                request_path = '/'.join(request_path.split('/')[:-1])
            if request_path == path:
                return  # 忽略路由白名单列表中的路由认证
        # 调用VerifyToken类进行校验
        user = verify.verify_token(request)
        session['token_id'] = user['token_id']
        session['user_name'] = user['user_name']
        session['real_name'] = user['real_name']
        for per in per_defaults:
            session[per['session_key']] = verify.permission_verify(
                per['center_name'], per['permission_name'])
        if verify.group_list is None:
            verify.group_list = []
        session['group_list'] = verify.group_list


class VerifyToken:
    def __init__(self, per_defaults=[{}], debug: bool = False, debug_permission: list = [0, 1, 2, 4, 8, 16, 32], proxy_none_response: bool = True):
        self.debug = debug  # 是否开启DEBUG模式
        self.debug_permission = debug_permission
        self.proxy_none_response = proxy_none_response  # 代理无权限响应
        self.uid = ''
        self.group_list = None
        # 认证中心的 Redis 库号码
        self.redis_db_permission = os.environ.get('REDIS_DB_PERMISSION', None)
        self.secret_key = os.environ.get(
            'SECRET_KEY', None)  # 密钥
        self.expiration = os.environ.get('EXPIRATION', None)  # 超时时间
        # 认证中心 MongoDB 的库和集合名称
        self.mongo_db_name = os.environ.get('MONGODB_DB_NAME', None)
        self.mongo_permission = os.environ.get(
            'MONGODB_PERMISSION', None)  # 权限集合名称
        if self.redis_db_permission:
            self.redis_connect = RedisConnect(self.redis_db_permission)
        else:
            self.redis_connect = None  # 如果认证组件未连接，连接为空值
        self.mongo_permission_set = os.environ.get(
            'MONGODB_PERMISSIONSET', None)  # 权限设置集合名称
        # 连接权限设置集合数据
        if self.mongo_permission_set and self.mongo_db_name:
            self.permission_set_db = DBConnect(
                db=self.mongo_db_name, collection=self.mongo_permission_set)
        else:
            self.permission_set_db = None
        self.mongo_role = os.environ.get('MONGODB_ROLE', None)  # 角色集合名称
        # 连接角色集合数据
        if self.mongo_role and self.mongo_db_name:
            self.role_db = DBConnect(
                db=self.mongo_db_name, collection=self.mongo_role)
        else:
            self.role_db = None
        self.mongo_user = os.environ.get('MONGODB_USER', None)  # 用户集合名称
        # 连接用户集合数据
        if self.mongo_user and self.mongo_db_name:
            self.user_db = DBConnect(
                db=self.mongo_db_name, collection=self.mongo_user)
        else:
            self.user_db = None
        # 通过 per_defaults 添加权限数据，例如：[{'center_name': '组件名称', 'permission_name': '权限名称'},]
        threading.Thread(target=self.add_permission_db,
                         args=(per_defaults, )).start()

    def verify_token(self, request):
        """验证token"""
        if self.debug or platform.system() == 'Windows':
            return {'token_id': '0f0f0f0f0f0f0f0f0f0f0f0f', 'user_name': 'tmp_use', 'real_name': '调试账号'}
        if not self.redis_connect:
            handle_abnormal(
                message='计算组件未建立连接/依赖到认证中心(Redis)，无法验证凭证',
                status=500,
            )
        token = request.headers.get('token')  # 获取请求头中的Token
        s = Serializer(self.secret_key, self.expiration)
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            handle_abnormal(
                message='来自 {0} 的 Token 验证失败'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr)),
                status=401,
            )
        toke_uid = data.get('id')  # token中传来的
        # redis中写入的
        redis_uid = self.redis_connect.get_(toke_uid.split('--')[0])
        if redis_uid == toke_uid:
            tok = toke_uid.split('--')
            self.uid = tok[0]  # 用户ID
            user_name = tok[1]  # 用户名称，通常是英文
            real_name = tok[2]  # 真实姓名，通常是中文
            return {'token_id': self.uid, 'user_name': user_name, 'real_name': real_name}
        handle_abnormal(
            message='来自 {0} 的账户已退出，需要重新登录'.format(request.remote_addr),
            status=401,
        )

    def add_permission_db(self, per_defaults):
        """添加默认权限中心/名称 到数据库"""
        if self.debug or platform.system() == 'Windows':
            logging.warning('{0} 系统环境 Debug 模式启动'.format(platform.system()))
            return
        time.sleep(10)
        if self.mongo_db_name and self.mongo_permission:
            # 添加权限中心/名称到权限管理
            try:
                for per in per_defaults:
                    db = DBConnect(db=self.mongo_db_name,
                                   collection=self.mongo_permission)
                    # 查询是否已存在
                    find_dict = {'center_name': str(per['center_name']),
                                 'permission_name': str(per['permission_name'])}
                    sear_permission = db.find_docu(
                        find_dict=find_dict, many=False)
                    if not sear_permission:
                        purview_name_id = db.write_one_docu(docu=find_dict)
                    else:
                        purview_name_id = sear_permission[0]['id']
                    if self.permission_set_db:
                        # 添加权限信息到权限集合（0无权限-1查看-2新增-4编辑-8删除-16下载）
                        for status in per['status']:
                            find_dict.update({'permission_status': status})
                            if not self.permission_set_db.does_it_exist(find_dict):
                                find_dict.update(
                                    {'permission_id': purview_name_id})
                                self.permission_set_db.write_one_docu(
                                    docu=find_dict)
                    else:
                        logging.error('计算组件未建立连接/依赖到认证中心(MongoDB)，无法注册对应的角色权限')
            except Exception as e:
                logging.warning('添加权限中心/名称失败', str(e))
        else:
            logging.error('计算组件未读取到认证中心(MongoDB)连接依赖变量，无法注册权限')

    def permission_verify(self, center_name, permission_name) -> dict:
        """
        验证权限，通过所属 中心/权限名称 获取当前用户的权限
          center_name = '用户管理'  # 当前视图函数所属 中心
          permission_name = '用户列表'  # 当前视图函数所属 权限名称
          permission_list = [0]  # 默认无权限, 更具获取的权限控制请求方式
        """
        if self.debug or platform.system() == 'Windows':
            return {'permission_list': self.debug_permission, 'is_all_data': True}
        if not self.redis_connect:
            handle_abnormal(
                message='计算组件未建立连接/依赖到认证中心(Redis)服务，无法验证权限',
                status=500,
            )
        elif not self.role_db:
            handle_abnormal(
                message='计算组件未建立连接/依赖到认证中心(MongoDB)-角色集合({0})，无法验证权限'.format(
                    self.mongo_role),
                status=500,
            )
        elif not self.user_db:
            handle_abnormal(
                message='计算组件未建立连接/依赖到认证中心(MongoDB)-用户集合({0})，无法验证权限'.format(
                    self.mongo_user),
                status=500,
            )
        user = self.user_db.find_docu_by_id(id=self.uid)  # 查询用户对应的角色数据
        role_name_list = user['role_name']  # 用户包含的所有角色名称
        self.group_list = user.get('group_name', [])  # 用户包含的所有组别名称
        # 合并多角色权限
        permission_list = []
        is_all_data_list = []
        # 遍历角色权限数据
        for role_name in role_name_list:
            # 查询角色包含的权限集合，role_name + center_name + permission_name 不重复
            roles = self.role_db.find_docu(find_dict={'role_name': role_name,
                                                      'center_name': center_name,
                                                      'permission_name': permission_name
                                                      },
                                           many=False)
            if roles:
                permission_list.extend(roles[0].get('permission_status', []))  # list类型
                is_all_data_list.append(roles[0]['is_all_data'])  # 是否开放全部数据
        permission_list = list(set(permission_list))  # 权限值去重
        is_all_data_list = list(set(is_all_data_list))  # 数据权限去重
        if is_all_data_list == [True]:
            is_all_data = True  # 仅全部True为True
        else:
            is_all_data = False  # 安全考虑，含False都为False
        # 结束合并角色权限
        if self.proxy_none_response:
            if ([0] == permission_list) or (not permission_list):
                handle_abnormal(
                    message='无 "{0}-{1}" 的访问权限({2})'.format(
                        center_name, permission_name, str(permission_list)),
                    status=403,
                )
        permission_status = {
            'permission_list': permission_list, 'is_all_data': is_all_data}
        return permission_status

    def filter_verify(self, group_list, is_all_data, user_name, user_field_name='creator'):
        """
        根据用户分组权限，个人权限，用户信息。整理出符合mongo塞选语句的权限赛选条件
        用户实际业务模块直接塞选出符合权限要求的数据
        """
        # 根据用户分组权限，设置相关查询过滤条件
        auth_filter = {}
        # 从环境变量中获取超级管理员账号信息
        admin_user = os.environ.get('ADMIN_USER', [])
        # 判断用户是否为超级管理员，超级管理员则跳过群组认证环节
        if user_name in admin_user:
            pass
        elif group_list:
            auth_filter.update(group_list={'$elemMatch': {'$in': group_list}})
        else:
            handle_abnormal(message='用户无任何群组权限，无法操作数据', status=403)
        if not is_all_data:
            auth_filter.update({user_field_name: user_name})

        return auth_filter