
import inspect

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import models
from .models import connect
from .version import __version__

__author__ = "Gary M. Josack <gary@byoteki.com>"



class Error(Exception):
    """Base level exception for the Tattr library."""


class Tattr(object):
    """Basic class used to return Collections."""

    def __init__(self, uri):
        self.db = connect(uri)

        self.hosts = Hosts
        self.attrs = Attributes
        self.tags = Tags

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if inspect.isclass(attr) and issubclass(attr, Collection):
            inst = attr()
            inst.db = self.db
            return inst
        return attr

    def query(self, args):

        def ghn(hosts):
            """ Get Hostname. """
            return set(host["hostname"] for host in hosts)

        if not args:
            return ghn(self.hosts)

        if args[0][0] in "-+":
            hosts = ghn(self.hosts)
        else:
            hosts = ghn(self.hosts.filter_tag(args.pop(0)))

        for tag in args:
            if tag.startswith("+"):
                hosts.update(ghn(self.hosts.filter_tag(tag[1:])))
            elif tag.startswith("-"):
                hosts.difference_update(ghn(self.hosts.filter_tag(tag[1:])))
            else:
                hosts.intersection_update(ghn(self.hosts.filter_tag(tag)))

        return hosts


class Collection(object):
    """Represents different tattr collections. """

    model = None

    def __init__(self):
        if self.model is None:
            raise Error("Collection class is abstract only.")

        self.db = None


    def list(self):
        return list(self)

    def __iter__(self):
        for entity in self.db.query(self.model):
            yield entity.as_dict()


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
            raise Error("Hostname (%s) already exists." % name)

    def rm(self, name):
        try:
            host = self.db.query(self.model).filter_by(hostname=name).one()
        except NoResultFound:
            raise Error("Hostname (%s) doesn't exist." % name)
        self.db.delete(host)
        self.db.commit()

    def rename(self, old_name, new_name):
        try:
            host = self.db.query(self.model).filter_by(hostname=old_name).one()
        except NoResultFound:
            raise Error("Hostname (%s) doesn't exist." % old_name)

        try:
            host.hostname = new_name
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise Error("Hostname (%s) already exists." % new_name)

    def get(self, name):
        try:
            host = self.db.query(self.model).filter_by(hostname=name).one()
        except NoResultFound:
            raise Error("Hostname (%s) doesn't exist." % name)
        return host.as_dict()

    def set_tag(self, hostname, tagname):
        try:
            host = self.db.query(self.model).filter_by(hostname=hostname).one()
        except NoResultFound:
            raise Error("Hostname (%s) doesn't exist." % hostname)
        try:
            tag = self.db.query(models.Tag).filter_by(tagname=tagname).one()
        except NoResultFound:
            raise Error("Tag (%s) doesn't exist." % tagname)

        host.tags.append(tag)
        self.db.commit()

    def unset_tag(self, hostname, tagname):
        try:
            host = self.db.query(self.model).filter_by(hostname=hostname).one()
        except NoResultFound:
            raise Error("Hostname (%s) doesn't exist." % hostname)
        try:
            tag = self.db.query(models.Tag).filter_by(tagname=tagname).one()
        except NoResultFound:
            raise Error("Tag (%s) doesn't exist." % tagname)

        try:
            host.tags.remove(tag)
            self.db.commit()
        except ValueError:
            pass  # If the item isn't in the list, just silently ignore.

    def set_attribute(self, hostname, attrname, value):
        try:
            host = self.db.query(self.model).filter_by(hostname=hostname).one()
        except NoResultFound:
            raise Error("Hostname (%s) doesn't exist." % hostname)

        try:
            attr = self.db.query(models.Attribute).filter_by(attrname=attrname).one()
        except NoResultFound:
            raise Error("Attribute (%s) doesn't exist." % attrname)

        try:
            assoc = (self.db.query(models.HostAttributes)
                .filter_by(host_id=host.id)
                .filter_by(attribute_id=attr.id)
                .one()
            )
        except NoResultFound:
            assoc = models.HostAttributes(host_id=host.id, attribute_id=attr.id)

        assoc.value = value
        host.attributes.append(assoc)
        self.db.commit()


    def unset_attribute(self, hostname, attrname):
        try:
            host = self.db.query(self.model).filter_by(hostname=hostname).one()
        except NoResultFound:
            raise Error("Hostname (%s) doesn't exist." % hostname)

        try:
            attr = self.db.query(models.Attribute).filter_by(attrname=attrname).one()
        except NoResultFound:
            raise Error("Attribute (%s) doesn't exist." % attrname)

        try:
            assoc = (self.db.query(models.HostAttributes)
                .filter_by(host_id=host.id)
                .filter_by(attribute_id=attr.id)
            ).one()
        except NoResultFound:
            return

        host.attributes.remove(assoc)
        self.db.delete(assoc)
        self.db.commit()


    def filter(self, property_type, name, value):
        self._filters.add((property_type, name, value))
        return self

    def filter_tag(self, tag):
        return self.filter("tag", tag, None)

    def filter_attr(self, attr, value=None):
        return self.filter("attr", attr, value)

    def __iter__(self):
        query = self.db.query(self.model)

        for prop_type, name, value in self._filters:
            if prop_type == "tag":
                query = query.filter(models.Host.tags.any(tagname=name))
            elif prop_type == "attr":
                query = query.filter(models.Host.real_attributes.any(attrname=name))
                if value:
                    query = query.filter(models.Host.attributes.any(value=value))

        for entity in query:
            yield entity.as_dict()


class Tags(Collection):
    model = models.Tag

    def add(self, name):
        try:
            self.db.add(self.model(tagname=name))
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise Error("Tag (%s) already exists." % name)

    def rm(self, name, force=False):
        try:
            tag = self.db.query(self.model).filter_by(tagname=name).one()
        except NoResultFound:
            raise Error("Attribute (%s) doesn't exist." % name)
        if tag.hosts and not force:
            raise Error("Tried to remove tag in use by %s hosts without force." % len(tag.hosts))
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
            raise Error("Attribute (%s) already exists." % name)

    def rm(self, name, force=False):
        try:
            attr = self.db.query(self.model).filter_by(attrname=name).one()
        except NoResultFound:
            raise Error("Attribute (%s) doesn't exist." % name)
        if attr.hosts and not force:
            raise Error("Tried to remove attribute in use by %s hosts without force." % len(attr.hosts))

        for assoc in attr.host_assocs:
            self.db.delete(assoc)
        self.db.delete(attr)
        self.db.commit()
