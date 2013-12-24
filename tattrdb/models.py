from sqlalchemy import create_engine
from sqlalchemy import (
    Table, Column, Integer, String, Text, Boolean,
    ForeignKey, Enum, DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker


Session = sessionmaker()
Model = declarative_base()


def connect(uri):
    engine = create_engine(uri)
    Session.configure(bind=engine)
    return Session()


def _sync(connection):
    """ This will build the database for whatever connection you pass."""
    Model.metadata.create_all(connection.bind)


host_tags = Table("host_tags", Model.metadata,
    Column("host_id", Integer, ForeignKey("hosts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True)
)

class Tag(Model):
    __tablename__ = 'tags'

    id = Column(Integer(), primary_key=True, nullable=False)
    tagname = Column(String(length=255), unique=True)

    def as_dict(self):
        return {
            "id": self.id,
            "tagname": self.tagname,
            "hosts": [host.hostname for host in self.hosts],
        }


class HostAttributes(Model):
    __tablename__ = "host_attributes"

    host_id = Column(Integer, ForeignKey("hosts.id"), primary_key=True)
    attribute_id = Column(Integer, ForeignKey("attributes.id"), primary_key=True)

    value = Column(String(length=255), nullable=False)

    attribute = relationship("Attribute", lazy="joined", backref="host_assocs")


class Attribute(Model):
    __tablename__ = 'attributes'

    id = Column(Integer(), primary_key=True, nullable=False)
    attrname = Column(String(length=255), unique=True)

    hosts = relationship("Host", secondary="host_attributes", lazy="joined", backref="real_attributes")

    def as_dict(self):
        values = {}

        for host_assoc in self.host_assocs:
            if host_assoc.value not in values:
                values[host_assoc.value] = []
            values[host_assoc.value].append(host_assoc.host.hostname)

        return {
            "id": self.id,
            "attrname": self.attrname,
            "values": values,
        }


class Host(Model):
    __tablename__ = 'hosts'

    id = Column(Integer(), primary_key=True, nullable=False)
    hostname = Column(String(length=255), unique=True)

    tags = relationship(
        "Tag", secondary=host_tags, lazy="joined", backref="hosts")
    attributes = relationship("HostAttributes", lazy="joined", backref="host")

    def as_dict(self):
        return {
            "id": self.id,
            "hostname": self.hostname,
            "tags": [tag.tagname for tag in self.tags],
            "attributes": {attr.attribute.attrname: attr.value for attr in self.attributes}
        }


