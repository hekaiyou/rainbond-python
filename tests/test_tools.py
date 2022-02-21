import pytest
from bson.objectid import ObjectId
from rainbond_python.tools import handle_db_id, handle_db_to_list
from rainbond_python.db_connect import DBConnect
from werkzeug.exceptions import HTTPException


def test_db_id():
    with pytest.raises(HTTPException):
        handle_db_id('')
    with pytest.raises(HTTPException):
        handle_db_id([])
    with pytest.raises(HTTPException):
        handle_db_id('123')
    id_data1 = handle_db_id({'_id': '600535c49495e1c2bec76356'})
    id_data2 = handle_db_id({'id': '600535c49495e1c2bec76356'})
    id_data3 = handle_db_id({'_id': '600535c49495e1c2bec76356', 'id': '12345'})
    data = handle_db_id({'name': 'xiaoyang', 'age': 8})
    assert id_data1['_id'] == ObjectId('600535c49495e1c2bec76356')
    assert id_data2['_id'] == ObjectId('600535c49495e1c2bec76356')
    assert id_data3['_id'] == ObjectId('600535c49495e1c2bec76356')
    assert data == {'name': 'XiaoYang', 'age': 8}


def test_handle_db_to_list():
    with pytest.raises(HTTPException):
        handle_db_to_list('')
    with pytest.raises(HTTPException):
        handle_db_to_list([])
    db = DBConnect('unitest_rainbond_python', 'test_parameter')
    db.write_one_docu({'name': 'LaoXu', 'age': 28})
    db.write_one_docu({'name': 'LaoHe', 'age': 18})
    old_list = db.mongo_collection.find({})
    new_list = handle_db_to_list(old_list)
    assert isinstance(new_list, list)
    assert len(new_list) > 0
    assert isinstance(new_list[0]['id'], str)
