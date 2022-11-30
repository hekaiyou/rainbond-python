import os
import redis
import logging
from .tools import handle_abnormal

logging.basicConfig(
    level=logging.WARNING,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)


class RedisConnect:
    def __init__(self, db=0, host_key='REDIS_HOST', port_key='REDIS_PORT', password='REDIS_PASSWORD', decode_responses: bool = True, *args, **kwargs):
        self.redis_host = os.environ.get(host_key, '127.0.0.1')
        self.redis_port = os.environ.get(port_key, 6379)
        self.redis_password = os.environ.get(password, None)
        # 创建Redis连接池
        if self.redis_password:
            self.pool = redis.ConnectionPool(
                host=self.redis_host, port=self.redis_port, decode_responses=decode_responses, password=self.redis_password, *args, **kwargs)
        else:
            self.pool = redis.ConnectionPool(
                host=self.redis_host, port=self.redis_port, decode_responses=decode_responses, *args, **kwargs)

    def connect(self):
        try:
            # 创建Redis实例（共享一个连接池）
            con = redis.Redis(connection_pool=self.pool)
            con.get('usability_testing')  # 主动尝试连接
            return con
        except Exception as e:
            # 尝试连接失败直接抛出异常
            handle_abnormal(
                message='Redis 连接失败',
                status=500,
                other={'prompt': str(e)}
            )

    def mset_(self, *args, **kwargs):
        """
        批量设置值
        mset_({'k1': 'v1', 'k2': 'v2'})
        mset_(k1='v1', k2='v2')
        mset_('k1', 'k2')
        mset_('k1')
        """
        return self.connect().mset(*args, **kwargs)

    def getset_(self, *args, **kwargs):
        """
        设置新值并获取原来的值
        getset_('food', 'barbecue')
        """
        return self.connect().getset(*args, **kwargs)

    def get_(self, *args, **kwargs):
        """
        取出键对应的值
        get_('foo')
        """
        return self.connect().get(*args, **kwargs)

    def mget_(self, *args, **kwargs):
        """
        批量获取
        mget_('k1', 'k2')
        mget_(['k1', 'k2'])
        mget_('fruit', 'fruit1', 'fruit2', 'k1', 'k2')
        """
        return self.connect().mget(*args, **kwargs)

    def delete_(self, *args, **kwargs):
        """
        删除
        delete_('gender')
        """
        return self.connect().delete(*args, **kwargs)

    def incr_(self, *args, **kwargs):
        """
        自增 name 对应的值，当 name 不存在时，则创建 name＝amount，否则，则自增
        incr_('foo', amount=1)
        """
        return self.connect().incr(*args, **kwargs)

    def decr_(self, *args, **kwargs):
        """
        自减 name 对应的值，当 name 不存在时，则创建 name＝amount，否则，则自减
        decr_('foo4', amount=3)
        decr_('foo1', amount=1)
        decr_('foo1', 'foo4')
        """
        return self.connect().decr(*args, **kwargs)

    def lpush_(self, *args, **kwargs):
        """
        list增加（类似于list的append，只是这里是从左边新增加）--没有就新建
        lpush_('list1', 11, 22, 33)
        """
        return self.connect().lpush(*args, **kwargs)

    def rpush_(self, *args, **kwargs):
        """
        list增加（从右边增加）--没有就新建
        rpush_('list2', 11, 22, 33)
        """
        return self.connect().rpush(*args, **kwargs)

    def lpop_(self, *args, **kwargs):
        """
        list从左删除并返回删除值
        lpop_('list2')
        """
        return self.connect().lpop(*args, **kwargs)

    def rpop_(self, *args, **kwargs):
        """
        list从右删除并返回删除值
        rpop_('list2')
        """
        return self.connect().rpop(*args, **kwargs)

    def exists_(self, *args):
        """
        检查名字是否存在
        exists_('zset1')
        """
        return self.connect().exists(*args)

    def expire_(self, *args, **kwargs):
        """
        设置超时时间
        expire_('list5', time=3)
        """
        return self.connect().expire(*args, **kwargs)
