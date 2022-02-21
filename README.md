# Rainbond Python

一个完整的 Python 云原生应用开发解决方案，基于以下内容：

- [Flask](https://dormousehole.readthedocs.io/en/latest/)：轻量级 Python Web 应用程序框架
- [Rainbond](https://www.rainbond.com/)：开源的企业级云原生平台，撑企业应用开发、架构、交付和运维的全流程

## 安装

```shell script
$ pip install rainbond-python
或者
$ pip3 install rainbond-python
```

## 快速开始

通过 `rainbond-python -c <组件名称>` 命令可以创建一个 Python 云原生组件：

```python
rainbond-python -c demo_component
```

该命令会在当前目录下创建一个组件项目，并打印如下提示：

```shell script
Successfully created `demo_component` component. Run command:
$ cd demo_component
$ pip3 install -r requirements.txt
$ python3 app.py
```

按照上面的提示，可以把一个最简单的 Python 云原生组件运行起来！

### 部署组件

将上面快速生成的组件项目上传到 Git 仓库中，在 Rainbond 应用中选择 *从源代码开始* 添加组件，通过组件的的源码地址构建云原生组件。

![部署组件01](/static_image/部署组件01.png)

构建完成后，通过添加 "http访问策略" 来配置云原生组件的访问路由。

![部署组件02](/static_image/部署组件02.png)

接下来通过 PostMan 等接口调试工具，访问 *http://xxx.com/api/v1/demo?key=value* (xxx替换成具体域名)，即可验证部署是否成功。（[源码地址](https://github.com/hekaiyou/demo_component/tree/v1)）

### 部署存储组件

在 Rainbond 应用中选择 *从源镜像开始* 构建组件，通过组件的的镜像地址构建存储 (数据库) 组件，在当前解决方案中，使用的是 **MongoDB** 数据库，因此将 `mongo` 作为镜像地址。

![接入数据库01](/static_image/接入数据库01.png)

存储 (数据库) 组件构建完成后，需要开通 *对内服务* 并同时将别名改成 **MONGODB**，这样存储组件才能被其他组件的容器依赖和访问。

![接入数据库02](/static_image/接入数据库02.png)

通过上面的步骤，存储组件会自动创建两个依赖环境变量。

![接入数据库03](/static_image/接入数据库03.png)

在开发调试时，我们需要在本地设置这个 MongoDB 的环境变量，以 Linux 为例。

```shell script
$ set MONGODB_HOST=127.0.0.1
$ set MONGODB_PORT=27017
```

如果是 Windows 环境，打开 "高级系统设置" 里的环境变量，直接可视化编辑即可。

### 数据库读写

作为快速开始的部分，这里只展示最简单的增删改查操作。（[源码地址](https://github.com/hekaiyou/demo_component/tree/v2)）首先，我们接着上面的组件项目，在开头添加两行代码。

```python
from flask import Flask, request
from rainbond_python.parameter import Parameter
from rainbond_python.error_handler import error_handler
from rainbond_python.db_connect import DBConnect  # 添加的代码

app = Flask(__name__)
error_handler(app)

db_books = DBConnect(db='demo', collection='books')  # 添加的代码
```

上面的 `DBConnect` 类是处理 MongoDB 读写行为的通用类，通过在初始化时，指定 `db` 和 `collection` 参数，我们可以连接到 MongoDB 的指定库、指定集合中。

#### 添加数据

修改组件项目的 **POST** 部分代码。

```python
    elif parameter.method == 'POST':
        param = parameter.verification(
            checking=parameter.param_json,
            verify={'title': str, 'author': str}
        )
        new_id = db_books.write_one_docu(docu=param)
        return {'new_id': new_id}
```

现在，我们往 `books` 集合中添加一本图书文档。

![数据库读写01](/static_image/数据库读写01.png)

上面 `Parameter` 类的 `verification()` 是一个非常实用的方法，它可以判断请求内容是否满足需求，我们可以放心使用通过 `verification()` 方法检查后的数据。而 `DBConnect` 类的 `write_one_docu()` 方法则用于写入单条文档，它接收一个字典，而恰好 `verification()` 方法返回的就是一个字典，所以可以直接作为数据写入。

#### 查询数据

修改组件项目的 **GET** 部分代码。

```python
    if parameter.method == 'GET':
        find_data = db_books.find_paging(parameter)
        return find_data
```

现在，我们查询 `books` 集合中的所有图书文档。

![数据库读写02](/static_image/数据库读写02.png)

上面 `DBConnect` 类的 `find_paging()` 同样是一个特别实用的方法，如上面所见，你只需要把请求内容交给它，它会直接返回查询结果给你。

你还可以试试多写入几个文档，然后请求 `http://127.0.0.1:5000/api/v1/demo?author=李杰` 接口，看看会有什么神奇的效果？

#### 更新数据

修改组件项目的 **PUT** 部分代码。

```python
    elif parameter.method == 'PUT':
        param = parameter.verification(
            checking=parameter.param_json,
            verify={'id': str, 'title': str, 'author': str}
        )
        update_result = db_books.update_docu(
            find_docu={'id': param['id']},
            modify_docu={'title': param['title'], 'author': param['author']}
        )
        return update_result
```

现在，我们更新指定 `id` 的 `books` 集合中的图书文档。

![数据库读写03](/static_image/数据库读写03.png)

上面 `DBConnect` 类的 `update_docu()` 方法用于更新文档，它会返回更新结果。

#### 删除数据

修改组件项目的 **DELETE** 部分代码。

```python
    elif parameter.method == 'DELETE':
        param = parameter.verification(
            checking=parameter.param_json,
            verify={'id': str}
        )
        delete_result = db_books.delete_docu(find_docu=param)
        return delete_result
```

现在，我们删除指定 `id` 的 `books` 集合中的图书文档。

![数据库读写04](/static_image/数据库读写04.png)

上面 `DBConnect` 类的 `delete_docu()` 方法用于删除文档，它会返回删除结果。

### 建立组件依赖

完成一个简单的图书管理组件后，我们要将组件部署到 Rainbond 平台，在 Rainbond 应用中选择 *切换到编辑模式* 进入依赖关系编辑页面，将 *计算组件* 依赖到 *存储组件* 即 **Mongo DB** 组件。

![建立组件依赖01](/static_image/建立组件依赖01.png)

重新构建 *计算组件* 即 **Demo Component** 组件，完成构建并滚动更新后，通过日志可以看到组件服务已经在正常运行了。

![建立组件依赖02](/static_image/建立组件依赖02.png)

需要注意：在 Rainbond 平台更改组件依赖关系后，相关的组件需要进行滚动更新。

## 进阶

### 异常处理

通过 `error_handler()` 方法，可以将常用的 *4xx* 和 *5xx* 状态码的异常响应委托给 **rainbond-python** 处理，它会自动捕获这些异常并返回响应。

```python
......
from flask import Flask, request
from rainbond_python.error_handler import error_handler
......
app = Flask(__name__)
error_handler(app)
......
```

#### 跨域处理

默认情况下 `error_handler()` 方法通过 `flask_cors` 库一键处理了服务端跨域问题，如果需要考虑安全问题，可以通过 `error_handler(app, simple_cors=False)` 取消跨域支持，同时，还可以重写跨域逻辑。

```python
......
error_handler(app, simple_cors=False)
from flask_cors import CORS
CORS(app, resources={r'/.*': {'origins': 'http://127.0.0.1:8888'}})
......
```

#### 业务异常

使用 `handle_abnormal()` 方法可以主动抛出业务逻辑异常，简单示例如下。

```python
......
from rainbond_python.tools import handle_abnormal
......
@app.route('/api/v1/demo', methods=['GET'])
def api_demo():
    parameter = Parameter(request)

    if parameter.method == 'GET':
        handle_abnormal(message='异常信息~~~', status=400)
......
```

这样，当用户请求时，响应内容如下：

```json
{
    "code": 400,
    "message": "异常信息~~~",
    "server_time": 20210220143830000,
    "host_name": "Z0jli2o0d2ymott0ggs6m",
    "host_ip": "128.19.80.115"
}
```

还可以通过 `header` 参数字典设置响应头字典，通过 `other` 参数添加附加信息字典。

```python
handle_abnormal(message='2333~~~', status=400, other={'key1': 'value1', 'key2': {'a': 1}})
```

这样就可以将更详细的提示信息告知用户，响应内容如下：

```json
{
    "code": 400,
    "message": "2333~~~",
    "server_time": 20210220144625000,
    "host_name": "Z0jli2o0d2ymott0ggs6m",
    "host_ip": "128.19.80.115",
    "key1": "value1",
    "key2": {
        "a": 1
    }
}
```

当然，正常的业务逻辑也可以使用 `handle_abnormal()` 方法返回，但是考虑到业务逻辑的不确定性和复杂性，一般将作为异常逻辑的响应使用。

## 数据备份

mongo数据库的备份，是通过在rainbond平台mongo组件中安装插件的方式实现的，并且配合开源云存储服务，将备份数据上传至云端。

#### 插件安装步骤如下：

1.  ![数据库备份插件01](static_image/数据库备份插件01.png)
3.  ![数据库备份插件02](static_image/数据库备份插件02.png)
4.  ![数据库备份插件03](static_image/数据库备份插件03.png)
5.  ![数据库备份插件04](static_image/数据库备份插件04.png)
6.  ![数据库备份插件05](static_image/数据库备份插件05.png)

###### 插件参数说明
* 必须参数：

MONGODB_HOST ： 数据库地址

MONGODB_PORT ： 数据库端口

MONGODB_DB ： 需要备份的数据库名称

FILE_DIR ： 备份数据本地保存相对路径（同时也是上传备份数据的接口参数之一）

URL： 上传数据备份接口地址

* 定时任务参数（只支持以下参数）

DAY : 天循环

DAY_OF_WEEK: 周期循环

HOUR：小时循环

MINUTE：分钟循环

SECOND：秒循环

相似用法可参考 https://www.jianshu.com/p/4c5bc85fc3fd中2.1.3章节，第三点 crontab触发器用法

#### 开源云存储服务安装（可使用rainbond直接安装即可使用）
参考链接：https://www.laobuluo.com/2934.html

### Parameter

处理请求与响应参数的通用类。

```python
from rainbond_python.parameter import Parameter
```

#### 获取请求参数

通过 `Parameter` 类实例，可以获取以下信息：

- parameter.method: 请求类型
- parameter.headers: 请求头
- parameter.param_url: URL中传递的参数
- parameter.param_json: Json请求中的参数
- parameter.param_form: 表单请求中的参数

所有信息均为字典类型，通过 `json.dumps()` 可以直接作为响应返回：

```python
@app.route('/api/1.0/demo', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_demo():
    parameter = Parameter(request)
    if parameter.method == 'GET':
        return json.dumps(parameter.param_url, ensure_ascii=False), 200, []
    elif parameter.method == 'POST':
        return json.dumps(parameter.param_json, ensure_ascii=False), 200, []
    elif parameter.method == 'PUT':
        return json.dumps(parameter.param_json, ensure_ascii=False), 200, []
    elif parameter.method == 'DELETE':
        return json.dumps(parameter.param_json, ensure_ascii=False), 200, []
```

#### 校验参数内容

通过 `Parameter` 类的 `verification()` 方法，可以判断参数字典是否符合要求：

```python
    elif parameter.method == 'POST':
        param = parameter.verification(checking=parameter.param_json, verify={'name': str, 'age': int})
```

其中 `checking` 参数是需要校验的参数字典，通常传递 `parameter.param_url`、`parameter.param_json` 或 `parameter.param_form`。第二个 `verify` 参数则是校验内容字典，需要指定 *参数名* 和 *参数类型* 作为字典项。如果请求中包含可选参数，可以将该参数的名称及其默认值输入到 `optional` 参数中，例如可以设置 *age* 参数为空时，默认填充为 *18* 岁：

```python
parameter.verification(checking=parameter.param_json, verify={'name': str, 'age': int}, optional={'age': 18})
```

如果判断失败，则直接返回异常响应，响应体中包含明确的提示信息。默认情况下，`str` 类型的 必选参数不能为空字符串，如果需要为空，可以通过 `null_value=True` 进行设置，或者将其作为可选参数处理。

#### 校验文件表单

如果需要接收表单提交的文件对象，可以使用 `verification_file()` 方法对请求中的表单文件字段进行校验：

```python
    elif parameter.method == 'POST':
        param = parameter.verification(checking=parameter.param_form, verify={'id': str})
        param_file = parameter.verification_file(verify_field=['updata'])
```

如上面的代码，如果请求中没有名为 *updata* 的表单文件字段，会直接返回异常信息。该方法与 `verification()` 方法可以同时使用。如果还需要判断上传文件的后缀名，可以通过 `verify_suffix` 参数进行配置：

```python
param_file = parameter.verification_file(verify_field=['updata'], verify_suffix=['jpg'])
# 二者效果相同，但是列表类型可以同时指定多个后缀名称
param_file = parameter.verification_file(verify_field=['updata'], verify_suffix=[['jpg']])
```

该方法会返回 `werkzeug.datastructures.ImmutableMultiDict` 对象，即通过 `request.files` 获取到的对象，接下来就可以：

- 通过 `param_file.get('xxxx')` 获取到文件对象
- 通过 `param_file.get('xxxx').filename` 获取具体文件名称
- 通过 `param_file.get('xxxx').save('/xxx/xxx.jpg')` 保存文件到本地

### DBConnect

处理 MongoDB 读写行为的通用类。

```python
from rainbond_python.db_connect import DBConnect
db = DBConnect(db='db_name', collection='collection_name')
```

#### 分页查询

支持 **GET** 和 **POST** 请求，使用非常简单，直接把 `Parameter` 类的实例传递给 `DBConnect` 类的 `find_paging()` 方法即可：

```python
@app.route('/api/1.0/demo', methods=['GET'])
def api_demo():
    parameter = Parameter(request)
    if parameter.method == 'GET':
        find_data = db.find_paging(parameter)
        return find_data, 200, []
```

内部组件或外部客户端通过 */api/v1/demo?$offset=0&$limit=15&name=sb* 即可访问，请求参数如下：

- $limit: 可选，指示页大小，从 `1` 开始计算，默认 `10` 条数据（单纯的数数，数几个就几个）
- $offset: 可选，指示记录起始位置，默认从 `0` 开始计算（代码逻辑，第几就是从数据库的第几条开始取文档）
- $orderby: 可选，排序规则（Eg: `key1 desc,key2 asc`），asc=升序、desc=降序
- $start_date: 可选，开始日期（区间查询），支持日期（2020-10-1）格式和时间戳（601481600）格式
- $end_date: 可选，结束日期（区间查询），同上，必须成对出现
- $date_type: 可选，区间查询的字段，默认为更新时间（`update_time`），可以设置成按创建时间（`creation_time`）查询
- <任意筛选字段>: 可选，任意筛选值

响应字段如下：

- total: 查询到的文档总数
- items: 文档列表
- dummy_remove: 假删除文档数（不参与查询）

由于技术原因，筛选字段目前不支持 `int` 型数据的模糊查询。同时 `$start_date` 和 `$end_date` 如果传递的是时间戳格式，能精确到秒。（更复杂的查询，可以将查询值提前处理成字典，这样可以实现一些非常规性的需求）

#### 写文档

##### 写入单个文档

```python
insert_dict = {'name': 'Xiao Ming', 'age': 23}
db.write_one_docu(docu=insert_dict)
```

如果写入失败，会直接返回异常响应，如果成功则会返回新数据的 `_id` 值。

##### 写入多个文档

```python
insert_dict_list = [{'name': 'Xiao Ming', 'age': 23},{'name': 'lao Yang', 'age': 35}]
db.write_many_docu(docu_list=insert_dict_list)
```

如果写入失败，会直接返回异常响应，如果成功则会返回新数据的 `_id`值的列表。

#### 文档是否存在

```python
examine_dict = {'name': 'Xiao Ming'}
if db.does_it_exist(docu=examine_dict):
    print('Docu already exists')
else:
    print('Docu does not exist')
```

#### 更新文档

同样的，如果更新失败，也会直接返回异常响应。

##### 更新单个匹配文档

```python
find_dict = {'name': 'Xiao Ming'}
modify_dict = {'name': 'Xiao Hong'}
db.update_docu(find_docu=find_dict, modify_docu=modify_dict)
```

##### 更新全部匹配文档

```python
find_dict = {'age': 23}
modify_dict = {'name': '23 year old'}
db.update_docu(find_docu=find_dict, modify_docu=modify_dict, many=True)
```

该方法会返回一个包含 `matched_count` 和 `modified_count` 即匹配/影响数据条数的字典。


#### 更新文档-指定字段自增

```python
find_dict = {'name': 'xiao yang'}
modify_dict = {'age': 1}
db.update_docu_inc(find_docu=find_dict, modify_docu=modify_dict)
```
表示age字段数字增加1，原先age=18，调用该方法后，age=19
该方法会返回一个包含 `matched_count` 和 `modified_count` 即匹配/影响数据条数的字典。

#### 删除文档

删除文档分为 **真删除** 和 **假删除** 两种方式，通过 `delete_docu()` 方法实现，该方法会返回一个包含 `deleted_count` 和 `false_delete` 的字典。。

##### 真删除文档

```python
db.delete_docu(find_docu={'id': '60053fa139842d28d7563c6c'})
```

##### 假删除文档

```python
db.delete_docu(find_docu={'id': '60053fa139842d28d7563c6c'}, false_delete=True)
```

假删除操作会在对应的文档中添加一个 `remove_time` 字段，里面记录这个文档被移除的时间。

##### 批量删除文档

```python
db.delete_docu(find_docu={'id': {'$in': ['111', '222']}}, many=True)
```

#### 查询文档

通过 `find_docu()` 标准查询方法时，无论查询单个还是多个，返回均是 `list` 类型数据，没有匹配数据时返回空列表。

##### 查询单个匹配文档

```python
find_dict = {'title': {'$regex': '标题'}}
find_data_list = db.find_docu(find_dict=find_dict, many=False)
print(find_data_list[0])
```

##### 查询全部匹配文档

```python
find_dict = {'title': {'$regex': '标题'}}
find_data_list = db.find_docu(find_dict=find_dict)
for find_data in find_data_list:
    print(find_data)
```

##### 根据id查找文档

```python
from rainbond_python.db_connect import DBConnect
db = DBConnect('unitest_rainbond_python', 'test_db_connect')
id = db.write_one_docu({'name': 'LaoXu'})
docu = db.find_docu_by_id(str(id))

# 当id不存在时，默认会使用abort抛出异常
fail_docu = db.find_docu_by_id('6008daa19223551b00548ded')
# 可以将raise_err=False时，id不存在会返回None
fail_docu = db.find_docu_by_id('6008daa19223551b00548ded',raise_err=False)
```

该方法返回记录字典，且把'_id'转换为了str类型

##### 根据id列表查找文档

```python
from rainbond_python.db_connect import DBConnect
db = DBConnect('unitest_rainbond_python', 'test_db_connect')
docu_list = db.find_docu_by_id_list(['6008daa19223551b00548ded','6008daa29223551b00548dee'])
```

该方法返回记录字典列表，且把'_id'转换为了str类型。当所有id不存在时，返回[]

#### 根据字段去重查询文档

```python
num = find_docu_distinct('age')
``````
返回int类型数字，代表文档中age字段去重后的数量

### 文件下载

在网络上传输文件，目前主要有下载和流式传输两种方案，分别 `rainbond_python.download` 包的对应 `download_file()` 和 `download_flow()` 方法。

#### 普通下载

通常用于文档文件（压缩包/PDF/TXT等文档），这种方式必须等全部内容传输完毕后，才能在本地机器打开：

```python
......
from rainbond_python.download import download_file
......
    if parameter.method == 'GET':
        download_response = download_file(file_path='C:/Users/xxx/Desktop', file_name='新建文本文档.txt'])
        return download_response
......
```

#### 流式传输

通常用于多媒体文件（视频/音频/直播流等场景），文件信息由服务器向用户计算机连续实时地传送，不必等到整个文件全部下载完毕，通常经过几秒或十几秒的启动延时即可打开：

```python
......
from rainbond_python.download import download_flow
......
    if parameter.method == 'GET':
        download_response = download_flow(file_path='C:/Users/xxx/Desktop', file_name='微视频.mp4'])
        return download_response
......
```

#### 打包目录生成zip文件下载（在内存中打包）

通常用于将现有目录文件，打包成zip文件，提供用户下载。打包zip文件数据在内存中完成，完成后从内存中读取二进制数据，并且回收内存。
参数save_zip表示本地是否存储打包zip文件，默认值为 False，为True时,打包文件保存在打包目录同级

```python
from rainbond_python.download import download_directory

......
    if parameter.method == 'GET':
        download_response = download_directory(dir_path='C:/Users/xxx/project', zip_name='project.zip'],save_zip=False)
        return download_response
......
```

### RedisConnect

处理 Redis 读写行为的通用类。

```python
from rainbond_python.redis_connect import RedisConnect
redis_connect = RedisConnect(db=0)
```

### 权限认证

认证中心组件之前，需要将组件依赖于 **认证中心**、**Redis** 和 **MongoDB** 组件，然后在业务代码中编写如下代码，完成接入：

```python
......
from flask import Flask, request, session
from rainbond_python.verify_token import VerifyToken, set_token_session
......
# 注册权限信息到认证中心组件
per_defaults = [
    {'session_key': 'auth_xxxx', 'center_name': '组件名称', 'permission_name': '自定义权限', 'status': [0, 1, 2]},
]
token = VerifyToken(per_defaults=per_defaults)
set_token_session(app, verify=token, per_defaults=per_defaults)
......
@app.route('/api/v1/demo', methods=['GET'])
def api_v1_demo():
    # 获取用户权限：0-1-2-4-8-16-32-64 (无权限-查看-新增-编辑-删除-下载-……)
    # Eg: [0, 1, 2]
    permission_list = session['auth_reports']['permission_list']

    if parameter.method == 'GET' and (1 in permission_list):  # 用户有查询权限
        # 通过认证并符合权限后，可以执行业务逻辑
        psss
......
```

注册权限信息到认证中心组件的时候，`center_name` 和 `permission_name` 建议都以中文命名，因为前端管理页面会直接读取这两个字段。`session_key` 是写到会话中，建议使用英文命名。然后根据上面的注册内容，我们可以从会话中获取用户认证信息：

- session['auth_xxxx']['permission_list']: 0-1-2-4-8-16-32-64 (无权限-查看-新增-编辑-删除-下载-……)
- session['auth_xxxx']['is_all_data']: 前用户是否能查看全部数据
- session['real_name']: 账户真实姓名
- session['user_name']: 账户名称
- session['token_id']: 账户ID

如果需要指定某些路由不参与认证，可以通过 `set_token_session` 方法的 `whitelist` 参数设置白名单，例如 `whitelist=['/api/v1/demo']` 则表示该路由可以随意被请求。

### 通用方法

#### handle_date()

将 *2020-10-1* 或 *601481600* 即日期格式或时间戳格式的字符串，处理成 Python 的 `datetime.datetime` 数据：

```python
from rainbond_python.tools import handle_date
print(handle_date(date='2020-10-1'))
print(handle_date(date='2020-10-31', date_type='end'))
```

通过 `date_type` 可以设置是日期的开始（`start`）还是一天的结束（`end`）时间。

#### handle_db_dict()

将 MongoDB 字典数据中的 `_id` 转换为 `str` 类型、时间转换成时间戳：

```python
query_dict = self.mongo_collection.find_one({'title': {'$regex': '标题1'}})
handle_db_dict(query_dict)
```

#### handle_db_to_list()

将 MongoDB 的列表中的 `_id` 转换为 `str` 类型，并转换为字典列表（原db的id是ObjectId类型，转为json会报错）：

```python
from rainbond_python.tools import handle_db_to_list
from rainbond_python.db_connect import DBConnect

def test_handle_db_to_list():
    db = DBConnect('unitest_rainbond_python', 'test_parameter')
    old_list = db.mongo_collection.find({})
    new_list = handle_db_to_list(old_list)
    print('new_list is a list of dict',new_list)
```

#### handle_time_difference()

计算前端传递的两个时间戳之间，相差多少秒，返回 `float` 类型，解决前后端时间戳（前端的毫秒是整数位、Python的毫秒是小数位）差异问题：

```python
from rainbond_python.tools import handle_time_difference
handle_time_difference(start_timestamp=1614051008, end_timestamp=1614051008)
```

## 开发与测试

### 调试开发

基础调试代码的 `demo.py` 即 *rainbond -c demo-component* 命令创建项目中的 `app.py` 文件，是一个可以快速开始的基础代码项目。

在本地调试时，在 **demos** 目录下创建 `dev_xxxxx.py`，并复制 `demo.py` 文件里的代码，并在里面调试 *rainbond_python* 目录下的代码。（本地创建的 dev_*.py 文件会被忽略，不会被提交），同时要在开头处添加下面代码，以调用基础包中的代码：

```python
......
import sys
sys.path.append('..')
from rainbond_python.parameter import Parameter
from rainbond_python.error_handler import error_handler
from rainbond_python.db_connect import DBConnect
......
```

### 单元测试

单元测试在 /tests/* 目录下

* 执行单元测试
```shell script
$ pytest
```

## 参考

- [Restful API](https://www.runoob.com/w3cnote/restful-architecture.html) : 具体的组件API开发标准
- [12 Factor](https://12factor.net/zh_cn/) : 符合十二要素的才是云原生应用
- [RainBond](https://www.rainbond.com/docs/) : 一个开源的云原生平台
