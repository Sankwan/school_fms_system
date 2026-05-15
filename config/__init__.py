# Use PyMySQL as MySQLdb (works on Render; no mysqlclient compile step)
import pymysql

pymysql.install_as_MySQLdb()
