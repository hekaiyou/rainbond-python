import json
from flask import abort, Response
from .tools import handle_abnormal


class Parameter():
    def __init__(self, request):
        self.request = request
        self.ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        self.method = request.method  # 请求方法
        self.headers = dict(request.headers)  # 请求头
        # GET方法的取参
        self.param_url = request.args.to_dict()
        # 非GET方法取值
        try:
            self.param_json = json.loads(
                request.get_data(as_text=True)
            )
        except json.decoder.JSONDecodeError:
            self.param_json = {}
        # 表单提交取值
        self.param_form = dict(request.form)

    def get_content(self) -> dict:
        return {
            'method': self.method,
            'headers': self.headers,
            'param_url': self.param_url,
            'param_json': self.param_json,
            'param_form': self.param_form
        }

    def verification(self, checking: dict, verify: dict, optional: dict = {}, null_value: bool = False, allow_extra: bool = False) -> dict:
        if type(checking) != dict:
            handle_abnormal(message='请求格式不规范', status=400)
        for opt_k, opt_v in optional.items():
            # 没有选填参数时，填充预设的默认值
            if not checking.__contains__(opt_k):
                checking[opt_k] = opt_v
        if not set(verify.keys()).issubset(set(checking.keys())):
            json_data = {'All Parameters': {}, 'Optional': optional}
            for k, v in verify.items():
                json_data['All Parameters'][k] = str(v)
            handle_abnormal(
                message='请求参数不完整',
                status=400,
                other={'prompt': json_data}
            )
        redundant_dict = {}  # 未预先定义的额外参数字典
        for _k, _v in checking.items():
            try:
                str_data = None
                if type(_v) != verify[_k]:
                    if verify[_k] == float:
                        # 特殊处理字符串形式 float 类型判断
                        try:
                            checking[_k] = float(_v)
                        except ValueError as err:
                            str_data = f'参数 {_k} 应该符合 {verify[_k]} 格式'
                    elif verify[_k] == int:
                        # 特殊处理字符串形式 int 类型判断
                        try:
                            checking[_k] = int(_v)
                        except ValueError as err:
                            str_data = f'参数 {_k} 应该符合 {verify[_k]} 格式'
                    elif verify[_k] == list:
                        # 特殊处理字符串形式 list 类型判断
                        try:
                            checking[_k] = json.loads(_v)
                        except ValueError as err:
                            str_data = f'参数 {_k} 应该符合 {verify[_k]} 格式'
                    else:
                        str_data = f'参数 {_k} 应该是 {verify[_k]} 类型'
                if not null_value and verify[_k] == str and not optional.__contains__(_k) and not str_data:
                    # 字符串不允许为空 AND 要求为字符串 AND 不是可选参数 AND 前面没有其他错误
                    if not _v.strip():
                        str_data = f'参数 {_k} 不能是空字符串'
                if str_data:
                    handle_abnormal(
                        message='请求参数类型校验失败',
                        status=400,
                        other={'prompt': str_data}
                    )
            except KeyError as err:
                if allow_extra:
                    redundant_dict[_k] = _v  # 收集多余的参数
                else:
                    handle_abnormal(
                        message='有多余的请求参数',
                        status=400,
                        other={'prompt': str(err)}
                    )
        if allow_extra:  # 默认不需要收集和返回额外参数
            checking['redundant_dict'] = redundant_dict
        return checking

    def verification_file(self, verify_field: list, verify_suffix: list = []):
        files = self.request.files
        for field in verify_field:
            if not files.get(field, None):
                handle_abnormal(
                    message='表单文件参数不完整',
                    status=400,
                    other={'prompt': verify_field}
                )
        if verify_suffix:
            if len(verify_suffix) != len(verify_field):
                handle_abnormal(
                    message='参数 verify_field 与 verify_suffix 的长度不一致',
                    status=500,
                )
            for i in range(len(verify_suffix)):
                file_name = files[verify_field[i]].filename
                if type(verify_suffix[i]) == list:
                    if file_name.split('.')[-1] not in verify_suffix[i]:
                        handle_abnormal(
                            message='文件字段 {0} 仅支持 {1} 后缀'.format(
                                verify_field[i], verify_suffix[i]),
                            status=400,
                        )
                else:
                    if file_name.split('.')[-1] != verify_suffix[i]:
                        handle_abnormal(
                            message='文件字段 {0} 仅支持 {1} 后缀'.format(
                                verify_field[i], verify_suffix[i]),
                            status=400,
                        )
        return files
