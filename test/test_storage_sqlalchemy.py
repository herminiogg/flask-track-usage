# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 21:31:41 2014

@author: Goutham
"""

try:
    import sqlalchemy as sql
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    
import datetime
import unittest
from flask import Blueprint
from . import FlaskTrackUsageTestCase
from flask_track_usage import TrackUsage
from flask_track_usage.storage.sql import SQLStorage
    
@unittest.skipUnless(HAS_SQLALCHEMY, "Requires SQLAlchemy")
class TestSQLiteStorage(FlaskTrackUsageTestCase):
    
    def setUp(self):
        """
        Set up an app to test with.
        """
        self.given_table_name = 'my_usage'
        FlaskTrackUsageTestCase.setUp(self)
        self.blueprint = Blueprint('blueprint', __name__)
        @self.blueprint.route('/blueprint')
        def blueprint():
            return "blueprint"
        self.app.register_blueprint(self.blueprint)
        
        self.storage = SQLStorage(
            conn_str="sqlite://",
            table_name=self.given_table_name
        )
    
        self.track_usage = TrackUsage(self.app, self.storage)
        self.track_usage.include_blueprint(self.blueprint)
        
    def test_sqlite_table_name(self):
        '''
        Test table name is created correctly for SQLite
        '''
        meta = sql.MetaData()
        meta.reflect(bind=self.storage._eng)
        assert self.given_table_name == meta.tables.keys()[0]

    def test_sqlite_storage_data_basic(self):
        """
        Test that data is stored in SQLite and retrieved correctly.
        """
        self.client.get('/')
        con = self.storage._eng.connect()
        s = sql.select([self.storage.track_table])
        result = con.execute(s).fetchone()
        assert result[0] == 1 # first row
        assert result[1] == u'http://localhost/'
        assert result[2] is None
        assert result[3] is None
        assert result[4] is None
        assert result[5] is None
        assert result[6] is None
        assert result[8] == 200
        assert result[9] is None
        assert result[10] == False
        assert result[11] is None
        assert result[12] == '/'
        assert result[13].__class__ is float
        assert type(result[14]) is datetime.datetime
        
    def test_sqlite_storage_data_blueprint(self):
        """
        Test that data is stored in SQLite and retrieved correctly for blueprint.
        """
        self.client.get('/blueprint')
        con = self.storage._eng.connect()
        s = sql.select([self.storage.track_table])
        result = con.execute(s).fetchone()
        assert result[0] == 1 # first row
        assert result[1] == u'http://localhost/blueprint'
        assert result[2] is None
        assert result[3] is None
        assert result[4] is None
        assert result[5] is None
        assert result[6] == 'blueprint'
        assert result[8] == 200
        assert result[9] is None
        assert result[10] == False
        assert result[11] is None
        assert result[12] == '/blueprint'
        assert result[13].__class__ is float
        assert type(result[14]) is datetime.datetime
        
    def test_sqlite_storage_get_usage(self):
        """
        Verify we can get usage information in expected ways using SQLStorages.
        """
        # First check no blueprint case get_usage is correct
        self.client.get('/')
        result = self.storage.get_usage()[0]
        assert result[0] == 1 # first row
        assert result[1] == u'http://localhost/'
        assert result[2] is None
        assert result[3] is None
        assert result[4] is None
        assert result[5] is None
        assert result[6] is None
        assert result[8] == 200
        assert result[9] is None
        assert result[10] == False
        assert result[11] is None
        assert result[12] == '/'
        assert result[13].__class__ is float
        assert type(result[14]) is datetime.datetime
        
        # Next check with blueprint the get_usage is correct
        self.client.get('/blueprint')
        rows = self.storage.get_usage()
        result = rows[1] if rows[0][6] is None else rows[0]
        assert result[0] == 2 # first row
        assert result[1] == u'http://localhost/blueprint'
        assert result[2] is None
        assert result[3] is None
        assert result[4] is None
        assert result[5] is None
        assert result[6] == 'blueprint'
        assert result[8] == 200
        assert result[9] is None
        assert result[10] == False
        assert result[11] is None
        assert result[12] == '/blueprint'
        assert result[13].__class__ is float
        assert type(result[14]) is datetime.datetime
        
        # third get
        self.client.get('/')

        # Limit tests
        assert len(self.storage.get_usage()) == 3
        assert len(self.storage.get_usage(limit=2)) == 2
        assert len(self.storage.get_usage(limit=1)) == 1
        
        # timing tests
        now = datetime.datetime.utcnow()
        assert len(self.storage.get_usage(start_date=now)) == 0
        assert len(self.storage.get_usage(end_date=now)) == 3
        assert len(self.storage.get_usage(end_date=now, limit=2)) == 2
        
        # test pagination        
        for i in range(100):
            self.client.get('/')
        limit = 10
        for page in range(1,11):
            result = self.storage.get_usage(limit=limit,page=page)
            for i in range(limit):
                assert (page-1)*limit+i+1 == result[i][0]
        
        