from sqlalchemy import event, exc
from sqlalchemy.pool import Pool
from sqlalchemy.sql.expression import ClauseElement

#logger = logging.getLogger('dbutils')

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance

@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # optional - dispose the whole pool
        # instead of invalidating one at a time
        # connection_proxy._pool.dispose()

        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
#        logger.error('Connection died, reconnect attempt')
        raise exc.DisconnectionError()

    cursor.close()

#engine = create_engine('mysql://bfc1ffabdb36c3:65da212b@us-cdbr-east-02.cleardb.com/heroku_1cec684f35035ce?charset=utf8', echo=True, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)
#Base = declarative_base(bind=engine)
#Base.metadata.create_all(engine)
#sm = sessionmaker(bind=engine, autoflush=True, autocommit=False, expire_on_commit=False)
#Session = scoped_session(sm)

#engine = create_engine('sqlite:///db3.sqlite', echo=True)
#logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)
#logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARN)
#logging.getLogger('sqlalchemy.pool').setLevel(logging.WARN)
#logging.getLogger('sqlalchemy.orm').setLevel(logging.WARN)

