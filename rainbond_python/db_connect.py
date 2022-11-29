import os
import json
import pymongo
import logging
import math
import copy
from datetime import datetime
from .parameter import Parameter
from .tools import handle_date, handle_db_to_list, handle_db_dict, handle_db_id, handle_db_remove, handle_abnormal
from flask import abort, Response
from bson import ObjectId

logging.basicConfig(
    level=logging.WARNING,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)


class DBConnect:
    def __init__(self, db: str, collection: str, home_key='MONGODB_HOST', port_key='MONGODB_PORT', name_key='MONGODB_NAME', password_key='MONGODB_PASSWORD'):
        self.mongo_home = os.environ.get(home_key, None)
        self.mongo_port = os.environ.get(port_key, 27017)
        # 额外的认证用户与密码
        self.mongo_name = os.environ.get(name_key, None)
        self.mongo_password = os.environ.get(password_key, None)

        if not self.mongo_home or not self.mongo_port:
            logging.error('MongoDB(组件)的组件连接信息是不完整的')
        else:
            logging.warning('已连接地址为 {0}:{1} 的 MongoDB(组件)'.format(
                self.mongo_home, self.mongo_port))
        if self.mongo_name or self.mongo_password:
            # 额外的认证
            self.mongo_client = pymongo.MongoClient(
                host=self.mongo_home,
                port=int(self.mongo_port),
                username=self.mongo_name,
                password=self.mongo_password
            )
        else:
            # 常规连接
            self.mongo_client = pymongo.MongoClient(
                host=self.mongo_home,
                port=int(self.mongo_port)
            )
        self.mongo_db = self.mongo_client[db]
        self.mongo_collection = self.mongo_db[collection]

    def write_one_docu(self, docu: dict) -> str:
        try:
            deep_docu = copy.deepcopy(docu)  # 深拷贝
            # 兼容直接指定ID的创建方式
            deep_docu = handle_db_id(deep_docu)
            # 添加创建时间和更新时间，日期格式
            if not deep_docu.__contains__('creation_time'):
                deep_docu['creation_time'] = datetime.today()
            if not deep_docu.__contains__('update_time'):
                deep_docu['update_time'] = datetime.today()
            new_data = self.mongo_collection.insert_one(deep_docu)
            return str(new_data.inserted_id)
        except Exception as err:
            handle_abnormal(
                message='MongoDB(组件)出现写入错误: {0}'.format(json.dumps(docu)),
                status=500,
                other={'prompt': str(err)}
            )

    def write_many_docu(self, docu_list: list) -> list:
        try:
            new_docu_list = []
            for docu in docu_list:
                if isinstance(docu, dict):
                    # 添加创建时间和更新时间，日期格式
                    if not docu.__contains__('creation_time'):
                        docu['creation_time'] = datetime.today()
                    if not docu.__contains__('update_time'):
                        docu['update_time'] = datetime.today()
                    # 深渊巨坑，字段append()到列表中要用深拷贝
                    deep_docu = copy.deepcopy(docu)
                    new_docu_list.append(deep_docu)
                else:
                    handle_abnormal(
                        message='参数docu_list格式不正确，要求为：[{},{},{}...]',
                        status=500,
                        other={'prompt': {'docu_list': docu_list}}
                    )
            new_data_list = self.mongo_collection.insert_many(new_docu_list)
            new_id_list = [str(_id) for _id in new_data_list.inserted_ids]
            return new_id_list
        except Exception as err:
            handle_abnormal(
                message='MongoDB(组件)出现写入错误',
                status=500,
                other={'prompt': str(err)}
            )

    def does_it_exist(self, docu: dict) -> bool:
        deep_docu = copy.deepcopy(docu)  # 深拷贝
        deep_docu = handle_db_id(deep_docu)
        count = self.mongo_collection.count_documents(deep_docu)
        if count != 0:
            return True
        else:
            return False

    def update_docu(self, find_docu: dict, modify_docu: dict, many=False) -> dict:
        # 标准更新
        try:
            # 将参数id处理成符合mongo格式的_id对象
            find_docu = handle_db_id(find_docu)
            # 排除假删除数据
            find_docu = handle_db_remove(find_docu)
            # 重置更新时间
            if not modify_docu.__contains__('update_time'):
                modify_docu['update_time'] = datetime.today()
            # 将更新内容转化为mongo能识别的更新格式
            modify_docu = {'$set': modify_docu}
            if many:
                student = self.mongo_collection.update_many(
                    find_docu, modify_docu)
            else:
                student = self.mongo_collection.update_one(
                    find_docu, modify_docu)
            # 返回匹配条数、受影响条数
            return {'matched_count': student.matched_count, 'modified_count': student.modified_count}
        except Exception as err:
            handle_abnormal(
                message='MongoDB(组件)出现更新错误',
                status=500,
                other={'prompt': str(err)}
            )

    def update_docu_inc(self, find_docu: dict, modify_docu: dict, many=False) -> dict:
        # 字段自增更新
        try:
            # 将参数id处理成符合mongo格式的_id对象
            find_docu = handle_db_id(find_docu)
            # 排除假删除数据
            find_docu = handle_db_remove(find_docu)
            # 将更新内容转化为mongo能识别的更新格式
            modify_docu = {'$inc': modify_docu, '$set': {
                'update_time': datetime.today()}}
            if many:
                student = self.mongo_collection.update_many(
                    find_docu, modify_docu)
            else:
                student = self.mongo_collection.update_one(
                    find_docu, modify_docu)
            # 返回匹配条数、受影响条数
            return {'matched_count': student.matched_count, 'modified_count': student.modified_count}
        except Exception as err:
            handle_abnormal(
                message='MongoDB(组件)出现更新错误',
                status=500,
                other={'prompt': str(err)}
            )

    def delete_docu(self, find_docu: dict, many: bool = False, false_delete: bool = False) -> dict:
        try:
            if false_delete:
                # 假删除流程
                modify_dict = {'remove_time': datetime.today()}
                result = self.update_docu(
                    find_docu=find_docu, modify_docu=modify_dict, many=many)
                if not result['modified_count']:
                    logging.warning('MongoDB(组件)出现删除异常: 没有任何文档被假删除')
                return {'deleted_count': result['modified_count'], 'false_delete': false_delete}
            else:
                find_docu = handle_db_id(find_docu)
                find_docu = handle_db_remove(find_docu)
                # 真删除流程
                if many:
                    # 文档批量删除方式
                    result = self.mongo_collection.delete_many(find_docu)
                else:
                    # 文档精确删除方式
                    result = self.mongo_collection.delete_one(find_docu)
                if not result.deleted_count:
                    logging.error('MongoDB(组件)出现删除异常: 没有任何文档被真删除')
                # 返回删除成功条数
                return {'deleted_count': result.deleted_count, 'false_delete': false_delete}
        except Exception as err:
            handle_abnormal(
                message='MongoDB(组件)出现删除错误',
                status=500,
                other={'prompt': str(err)}
            )

    def find_docu(self, find_dict: dict, many: bool = True) -> list:
        try:
            deep_find_dict = copy.deepcopy(find_dict)  # 深拷贝
            deep_find_dict = handle_db_id(deep_find_dict)
            deep_find_dict = handle_db_remove(deep_find_dict)
            if many:
                # 多文档查询方式
                query_cursor = self.mongo_collection.find(deep_find_dict)
                return handle_db_to_list(query_cursor)
            else:
                # 单文档查询方式
                query_dict = self.mongo_collection.find_one(deep_find_dict)
                if not query_dict:
                    return []
                return [handle_db_dict(query_dict)]
        except Exception as err:
            handle_abnormal(
                message='MongoDB(组件)出现查询错误',
                status=500,
                other={'prompt': str(err)}
            )

    def find_docu_distinct(self, find_str: str) -> int:
        # 去重查询
        try:
            query_res = self.mongo_collection.distinct(find_str)
            return len(query_res)
        except Exception as err:
            handle_abnormal(
                message='MongoDB(组件)出现查询错误',
                status=500,
                other={'prompt': str(err)}
            )

    def find_docu_by_id(self, id: str, raise_err=True) -> dict:
        """
        根据id查找记录
        :param id:记录id
        :param raise_err:是否抛出异常（使用abort抛出），否则返回None
        :return: 将结果转换为字典
        """
        if not isinstance(id, str):
            handle_abnormal(
                message='类型错误, 预期 %s ,却得到 %s' % (str, type(id)),
                status=400,
            )
        entity = self.find_docu({'id': id}, many=False)
        if entity is None or len(entity) == 0:
            if raise_err:
                handle_abnormal(
                    message='找不到 id= %s 的记录' % (id,),
                    status=400,
                )
            else:
                return {}
        return entity[0]

    def find_docu_by_id_list(self, id_list: list) -> list:
        """
        根据id列表查找记录列表
        :param id_list:
        :return:
        """
        if not isinstance(id_list, list):
            handle_abnormal(
                message='类型错误, 预期 %s ,却得到 %s' % (list, type(id_list)),
                status=400,
            )
        id_search = []
        for id in id_list:
            id_search.append({'_id': ObjectId(id)})
        find_dict = {'$or': id_search}
        data = self.find_docu(find_dict)
        return data

    def find_paging(self, parameter: Parameter) -> dict:
        # 兼容GET和POST两个请求方式
        if parameter.method == 'GET':
            checking = parameter.param_url
        else:
            checking = parameter.param_json
        param = parameter.verification(
            checking=checking,
            verify={
                '$limit': int, '$offset': int, '$orderby': str, '$start_date': str, '$date_type': str,
                '$end_date': str,
            },
            optional={'$start_date': '', '$end_date': '', '$date_type': 'update_time',
                      '$offset': 0, '$limit': 10, '$orderby': ''},
            allow_extra=True
        )
        try:
            limit = int(param['$limit'])  # 指示页大小（从1开始）
            offset = int(param['$offset'])  # 指示记录起始位置（从0开始）
            if limit < 1:
                raise Exception('指示页大小必须从 1 开始计算')
            # 排序规则（`key1 desc,key2 asc`），asc=升序，desc=降序
            orderby = param['$orderby']
            sort_list = []  # 数据库排序规则列表
            if orderby:
                # 整理请求参数中的筛排序列表
                orderby = orderby.split(',')
                for order in orderby:
                    order_kv = order.split(' ')
                    if len(order_kv) == 2 and (order_kv[1] == 'asc' or order_kv[1] == 'desc') and order_kv[0].strip() != '':
                        if order_kv[1] == 'asc':
                            sort_list.append((order_kv[0], pymongo.ASCENDING))
                        elif order_kv[1] == 'desc':
                            sort_list.append((order_kv[0], pymongo.DESCENDING))
                    else:
                        raise Exception(
                            '排序参数不符合格式要求: "{0}"'.format(param['$orderby']))
            start_date = handle_date(date=param['$start_date'])  # 可选——开始日期
            # 可选——结束日期，与开始日期组成日期区间
            end_date = handle_date(date=param['$end_date'], date_type='end')
            # 查找假删除数据的数据量
            remove_count = self.mongo_collection.find(
                {'remove_time': {'$exists': True}}).count()
            # 查找字典和排序列表，处理假删除数据
            find_dict = handle_db_remove({})
            redundant_filter = param['redundant_dict']  # 额外的数据库筛选字典
            for filter_key, filter_value in redundant_filter.items():
                # 整理请求参数中的筛选项字典
                if type(filter_value) == int or type(filter_value) == dict or type(filter_value) == bool:
                    find_dict[filter_key] = filter_value
                elif filter_key == 'id' or filter_key == '_id':
                    find_dict['_id'] = ObjectId(str(filter_value))
                elif type(filter_value) == list:
                    # 值为列表，则使用元素匹配逻辑，将数据库中对应字段包含list元素的数据全部赛选出来
                    find_dict[filter_key] = {
                        "$elemMatch": {"$in": filter_value}}
                else:
                    # 查询值模糊匹配的结果
                    if filter_value.strip() != '':
                        filter_value = filter_value.replace("(", "\(")
                        filter_value = filter_value.replace(")", "\)")
                        find_dict[filter_key] = {'$regex': filter_value}
            # 仅存在日期查询区间参数时，进行额外的创建时间区间查询
            if start_date and end_date:
                find_dict[param['$date_type']] = {
                    '$gte': start_date, '$lte': end_date}
            # 对排序规则处理
            if sort_list:
                find_data = self.mongo_collection.find(find_dict).sort(sort_list).limit(
                    limit).skip(offset)
            else:
                find_data = self.mongo_collection.find(find_dict).limit(
                    limit).skip(offset)
            # 处理返回数据
            records_filtered = find_data.count()
            # 判断数据是否为空
            if records_filtered:
                # 处理返回数据
                query_result = handle_db_to_list(find_data)
                return {
                    'total': records_filtered,
                    'items': query_result,
                    'dummy_remove': remove_count,
                }
            else:
                return {
                    'total': 0,
                    'items': [],
                    'dummy_remove': remove_count,
                }
        except Exception as err:
            handle_abnormal(
                message='计算组件分页参数异常',
                status=400,
                other={'prompt': str(err)}
            )
