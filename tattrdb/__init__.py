
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import models
from .models import connect
from .version import __version__

__author__ = "Gary M. Josack <gary@byoteki.com>"



class TattrException(Exception):
    """Base level exception for the Tattr library."""


class Tattr(object):
    """Basic class used to return Collections."""

    def __init__(self, uri):
        self.db = connect(uri)

        self.hosts = self.add_collection(Hosts)
        self.attrs = self.add_collection(Attributes)
        self.tags = self.add_collection(Tags)

    def add_collection(self, collection):
        inst = collection()
        inst.db = self.db
        return inst


class Collection(object):
    """Represents different tattr collections. """

    model = None

    def __init__(self):

        if self.model is None:
            raise TattrException("Collection class is abstract only.")

        self.db = None


    def list(self):
        return list(self.db.query(self.model))

    def __iter__(self):
        for entity in self.list():
            yield entity



class Hosts(Collection):
    model = models.Host

    def __init__(self):
        Collection.__init__(self)
        self._filters = set()

    def add(self, name):
        try:
            self.db.add(self.model(hostname=name))
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise TattrException("Hostname (%s) already exists." % name)

    def rm(self, name):
        try:
            host = self.db.query(self.model).filter_by(hostname=name).one()
        except NoResultFound:
            raise TattrException("Hostname (%s) doesn't exist." % name)
        self.db.delete(host)
        self.db.commit()

    def rename(self, old_name, new_name):
        try:
            host = self.db.query(self.model).filter_by(hostname=old_name).one()
        except NoResultFound:
            raise TattrException("Hostname (%s) doesn't exist." % old_name)

        try:
            host.hostname = new_name
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise TattrException("Hostname (%s) already exists." % new_name)

    def get(self, name):
        try:
            host = self.db.query(self.model).filter_by(hostname=name).one()
        except NoResultFound:
            raise TattrException("Hostname (%s) doesn't exist." % name)
        return host.as_dict()

    def query(self, query):
        pass

    def set_tag(self, hostname, tagname):
        try:
            host = self.db.query(self.model).filter_by(hostname=hostname).one()
        except NoResultFound:
            raise TattrException("Hostname (%s) doesn't exist." % hostname)
        try:
            tag = self.db.query(models.Tag).filter_by(tagname=tagname).one()
        except NoResultFound:
            raise TattrException("Tag (%s) doesn't exist." % tagname)

        host.tags.append(tag)
        self.db.commit()

    def unset_tag(self, hostname, tagname):
        try:
            host = self.db.query(self.model).filter_by(hostname=hostname).one()
        except NoResultFound:
            raise TattrException("Hostname (%s) doesn't exist." % hostname)
        try:
            tag = self.db.query(models.Tag).filter_by(tagname=tagname).one()
        except NoResultFound:
            raise TattrException("Tag (%s) doesn't exist." % tagname)

        try:
            host.tags.remove(tag)
            self.db.commit()
        except ValueError:
            pass  # If the item isn't in the list, just silently ignore.

    def set_attribute(self, hostname, attrname, value):
        try:
            host = self.db.query(self.model).filter_by(hostname=hostname).one()
        except NoResultFound:
            raise TattrException("Hostname (%s) doesn't exist." % hostname)
        try:
            attr = self.db.query(models.Attribute).filter_by(attrname=attrname).one()
        except NoResultFound:
            raise TattrException("Attribute (%s) doesn't exist." % attrname)

    def unset_attribute(self, hostname, attrname):
        try:
            host = self.db.query(self.model).filter_by(hostname=hostname).one()
        except NoResultFound:
            raise TattrException("Hostname (%s) doesn't exist." % hostname)
        try:
            attr = self.db.query(models.Attribute).filter_by(attrname=attrname).one()
        except NoResultFound:
            raise TattrException("Attribute (%s) doesn't exist." % attrname)

    def filter(self, property_type, name, value):
        self._filters.add((property_type, name, value))
        return self


class Tags(Collection):
    model = models.Tag
    def add(self, name):
        try:
            self.db.add(self.model(tagname=name))
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise TattrException("Tag (%s) already exists." % name)

    def rm(self, name, force=False):
        try:
            tag = self.db.query(self.model).filter_by(tagname=name).one()
        except NoResultFound:
            raise TattrException("Attribute (%s) doesn't exist." % name)
        if tag.hosts and not force:
            raise TattrException("Tried to remove tag in use by %s hosts without force." % len(tag.hosts))
        self.db.delete(tag)
        self.db.commit()


class Attributes(Collection):
    model = models.Attribute

    def add(self, name):
        try:
            self.db.add(self.model(attrname=name))
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise TattrException("Attribute (%s) already exists." % name)

    def rm(self, name, force=False):
        try:
            attr = self.db.query(self.model).filter_by(attrname=name).one()
        except NoResultFound:
            raise TattrException("Attribute (%s) doesn't exist." % name)
        if attr.hosts and not force:
            raise TattrException("Tried to remove attribute in use by %s hosts without force." % len(attr.hosts))
        self.db.delete(attr)
        self.db.commit()

