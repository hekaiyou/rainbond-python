import pytest
from rainbond_python.db_connect import DBConnect
from werkzeug.exceptions import HTTPException


def test_find_docu_by_id():
    db = DBConnect('unitest_rainbond_python', 'test_db_connect')
    with pytest.raises(HTTPException):
        db.find_docu_by_id(1)
    with pytest.raises(HTTPException):
        db.find_docu_by_id([])
    with pytest.raises(HTTPException):
        db.find_docu_by_id('123123')
    with pytest.raises(HTTPException):
        db.find_docu_by_id('123123', raise_err=False)
    fail_docu = db.find_docu_by_id('6008daa19223551b00548ded', raise_err=False)
    assert fail_docu == {}
    with pytest.raises(HTTPException):
        db.find_docu_by_id('6008daa19223551b00548ded')

    id = db.write_one_docu({'name': 'LaoXu'})
    docu = db.find_docu_by_id(str(id))
    assert docu is not None
    assert isinstance(docu, dict)
    assert isinstance(docu['id'], str)


def test_find_docu_by_id_list():
    db = DBConnect('unitest_rainbond_python', 'test_db_connect')
    with pytest.raises(HTTPException):
        db.find_docu_by_id_list(1)
    with pytest.raises(HTTPException):
        db.find_docu_by_id_list({})
    db.write_one_docu({'name': 'LaoXu'})
    test_list = db.mongo_collection.find({})
    id_list = []
    for test in test_list:
        id_list.append(str(test['_id']))
    docu_list = db.find_docu_by_id_list(id_list)
    assert len(id_list) == len(docu_list)
    assert len(docu_list) > 0
    assert isinstance(docu_list[0], dict)
    assert isinstance(docu_list[0]['id'], str)
