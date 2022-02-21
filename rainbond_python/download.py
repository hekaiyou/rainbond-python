import os
import zipfile
from io import BytesIO
from .tools import handle_abnormal
from flask import Response, send_from_directory, make_response
from urllib.parse import quote


def download_file(file_path: str, file_name: str):
    if not os.path.exists(os.path.join(file_path, file_name)):
        handle_abnormal(
            message='文件(普通下载)路径不存在({0})'.format(
                os.path.join(file_path, file_name)),
            status=400,
            other={'file_path': file_path, 'file_name': file_name}
        )
    response = make_response(send_from_directory(
        file_path,  # 本地目录的path
        file_name,  # 文件名(带扩展名)
        as_attachment=True
    ))
    # 确保文件名称包含中文，逗号等各种符号时均能正常响应
    response.headers['Content-Disposition'] = "attachment; filename={0}; filename*=utf-8''{0}".format(
        quote(file_name))

    return response


def download_flow(file_path: str, file_name: str):
    complete_path = os.path.join(file_path, file_name)
    if not os.path.exists(complete_path):
        handle_abnormal(
            message='文件(流传输)路径不存在',
            status=400,
            other={'complete_path': complete_path}
        )

    def send_file():
        # 流式读取文件
        with open(complete_path, 'rb') as target_file:
            while 1:
                data = target_file.read(20 * 1024 * 1024)  # 每次读取20M
                if not data:
                    break
                yield data

    # 浏览器不识别的也会自动下载
    response = Response(send_file(), content_type='application/octet-stream')
    # 确保文件名称包含中文，逗号等各种符号时均能正常响应
    response.headers['Content-Disposition'] = "attachment; filename={0}; filename*=utf-8''{0}".format(
        quote(file_name))
    return response


def download_directory(dir_path: str, zip_name: str, save_zip=False):
    """ 将目录打包zip 返回数据"""
    if not os.path.exists(dir_path):
        handle_abnormal(
            message='目录路径不存在',
            status=400,
            other={'dir_path': dir_path}
        )
    # 创建一个内存对象，用于保存二进制文件
    memory_zip = BytesIO()
    # 在内存中打开一个压缩文件
    with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 将数据存储到内存的zip文件中
        for r, m, f in os.walk(dir_path):
            fpath = r.replace(dir_path, '')
            for _f in f:
                zf.write(os.path.join(r, _f), os.path.join(fpath, _f))
        for zfile in zf.filelist:
            zfile.create_system = 0
    # 读文件前，要将位置置位初始，从头开始读取文件
    memory_zip.seek(0)
    # 将内存中的数据读取出来
    data = memory_zip.read()
    # 关闭内存
    memory_zip.close()
    # 需要本地保存zip文件
    if save_zip:
        parent_path = os.path.dirname(dir_path)
        save_path = os.path.join(parent_path, zip_name)
        with open(save_path, 'wb') as z:
            z.write(data)
    # 浏览器不识别的也会自动下载
    response = Response(data, content_type='application/zip')
    # 确保文件名称包含中文，逗号等各种符号时均能正常响应
    response.headers['Content-Disposition'] = "attachment; filename={0}; filename*=utf-8''{0}".format(
        quote(zip_name))
    return response
