"""
link.py
Writes to MongoDB Collection: links
"""

import regex as re
from bson.objectid import ObjectId

from sefaria.system.exceptions import DuplicateRecordError, InputError
from sefaria.system.database import db
from . import abstract as abst
from . import text

import logging
logger = logging.getLogger(__name__)


class Link(abst.AbstractMongoRecord):
    """
    A link between two texts (or more specifically, two references)
    """
    collection = 'links'
    history_noun = 'link'

    required_attrs = [
        "type",           # string of connection type
        "refs"            # list of refs connected
    ]
    optional_attrs = [
        "anchorText",     # string of dibbur hamatchil (largely depcrated) 
        "auto",           # bool whether generated by automatic process
        "generated_by",   # string in ("add_commentary_links", "add_links_from_test", "mishnah_map")
        "source_text_oid" # oid of text from which link was generated
    ]

    def _normalize(self):
        self.auto = getattr(self, 'auto', False)
        self.generated_by = getattr(self, "generated_by", None)
        self.source_text_oid = getattr(self, "source_text_oid", None)
        self.refs = [text.Ref(self.refs[0]).normal(), text.Ref(self.refs[1]).normal()]

        if getattr(self, "_id", None):
            self._id = ObjectId(self._id)

    def _validate(self):
        assert super(Link, self)._validate()

        if False in self.refs:
            return False

        return True

    def _pre_save(self):
        if getattr(self, "_id", None) is None:
            # Don't bother saving a connection that already exists, or that has a more precise link already
            samelink = Link().load({"refs": self.refs})

            if samelink:
                if not self.auto and self.type and not samelink.type:
                    samelink.type = self.type
                    samelink.save()
                    raise DuplicateRecordError(u"Updated existing link with new type: {}".format(self.type))

                elif self.auto and not samelink.auto:
                    samelink.auto = self.auto
                    samelink.generated_by = self.generated_by
                    samelink.source_text_oid = self.source_text_oid
                    samelink.save()
                    raise DuplicateRecordError(u"Updated existing link with auto generation data {} - {}".format(self.refs[0], self.refs[1]))

                else:
                    raise DuplicateRecordError(u"Link already exists {} - {}. Try editing instead.".format(self.refs[0], self.refs[1]))

            else:
                preciselink = Link().load(
                    {'$and':
                        [
                            {'refs': self.refs[0]},
                            {'refs':
                                {'$regex': text.Ref(self.refs[1]).regex()}
                            }
                        ]
                    }
                )

                if preciselink:
                    # logger.debug("save_link: More specific link exists: " + link["refs"][1] + " and " + preciselink["refs"][1])
                    raise DuplicateRecordError(u"A more precise link already exists: {}".format(preciselink.refs[1]))
                # else: # this is a good new link


class LinkSet(abst.AbstractMongoSet):
    recordClass = Link

    def __init__(self, query_or_ref={}, page=0, limit=0):
        '''
        LinkSet can be initialized with a query dictionary, as any other MongoSet.
        It can also be initialized with a :py:class: `sefaria.text.Ref` object, and will use the :py:meth: `sefaria.text.Ref.regex()` method to return the set of Links that refer to that Ref or below.
        :param query_or_ref: A query dict, or a :py:class: `sefaria.text.Ref` object
        '''
        try:
            super(LinkSet, self).__init__({"refs": {"$regex": query_or_ref.regex()}}, page, limit)
        except AttributeError:
            super(LinkSet, self).__init__(query_or_ref, page, limit)

    def filter(self, sources):
        """
        Filter LinkSet according to 'sources' which may be either
        - a string, naming a text to include
        - an array of strings, naming multiple texts to include

        ! Returns a list of Links, not a LinkSet
        """
        if isinstance(sources, basestring):
            return self.filter([sources])

        # Expand Categories
        categories  = text.library.get_text_categories()
        expanded_sources = []
        for source in sources:
            expanded_sources += [source] if source not in categories else text.library.get_indexes_in_category(source, include_commentary=False)

        regexes = [text.Ref(source).regex() for source in expanded_sources]
        filtered = []
        for source in self:
            if any([re.match(regex, source.refs[0]) for regex in regexes] + [re.match(regex, source.refs[1]) for regex in regexes]):
                filtered.append(source)

        return filtered

    def refs_from(self, from_ref, as_tuple=False):
        """
        Get a collection of Refs that are opposite the given Ref, or a more specific Ref, in this link set.
        Note that if from_ref is more specific than the criterion that created the linkSet,
        then the results of this function will implicitly be filtered according to from_ref.
        :param from_ref: A Ref object
        :param as_tuple: If true, return a collection of tuples (Ref,Ref), where the first Ref is the given from_ref,
        or one more specific, and the second Ref is the opposing Ref in the link.
        :return:
        """
        reg = re.compile(from_ref.regex())
        refs = []
        for link in self:
            if reg.match(link.refs[1]):
                from_tref = link.refs[1]
                opposite_tref = link.refs[0]
            elif reg.match(link.refs[0]):
                from_tref = link.refs[0]
                opposite_tref = link.refs[1]
            else:
                opposite_tref = False

            if opposite_tref:
                try:
                    if as_tuple:
                        refs.append((text.Ref(from_tref), text.Ref(opposite_tref)))
                    else:
                        refs.append(text.Ref(opposite_tref))
                except:
                    pass
        return refs

    def summary(self, relative_ref):
        """
        Returns a summary of the counts and categories in this link set,
        relative to 'relative_ref'.
        """
        results = {}
        for link in self:
            ref = link.refs[0] if link.refs[1] == relative_ref.normal() else link.refs[1]
            try:
                oref = text.Ref(ref)
            except:
                continue
            cat  = oref.index.categories[0]
            if (cat not in results):
                results[cat] = {"count": 0, "books": {}}
            results[cat]["count"] += 1
            if (oref.book not in results[cat]["books"]):
                results[cat]["books"][oref.book] = 0
            results[cat]["books"][oref.book] += 1

        return [{"name": key, "count": results[key]["count"], "books": results[key]["books"] } for key in results.keys()]


def process_index_title_change_in_links(indx, **kwargs):
    if indx.is_commentary():
        pattern = r'^{} on '.format(re.escape(kwargs["old"]))
    else:
        commentators = text.IndexSet({"categories.0": "Commentary"}).distinct("title")
        pattern = ur"(^{} \d)|(^({}) on {} \d)".format(re.escape(kwargs["old"]), "|".join(commentators), re.escape(kwargs["old"]))
        #pattern = r'(^{} \d)|( on {} \d)'.format(re.escape(kwargs["old"]), re.escape(kwargs["old"]))
    links = LinkSet({"refs": {"$regex": pattern}})
    for l in links:
        l.refs = [r.replace(kwargs["old"], kwargs["new"], 1) if re.search(pattern, r) else r for r in l.refs]
        try:
            l.save()
        except InputError: #todo: this belongs in a better place - perhaps in abstract
            logger.warning("Deleting link that failed to save: {} {}".format(l.refs[0], l.refs[1]))
            l.delete()


def process_index_delete_in_links(indx, **kwargs):
    if indx.is_commentary():
        pattern = ur'^{} on '.format(re.escape(indx.title))
    else:
        commentators = text.IndexSet({"categories.0": "Commentary"}).distinct("title")
        pattern = ur"(^{} \d)|^({}) on {} \d".format(re.escape(indx.title), "|".join(commentators), re.escape(indx.title))
    LinkSet({"refs": {"$regex": pattern}}).delete()


#get_link_counts() and get_book_link_collection() are used in Link Explorer.
#They have some client formatting code in them; it may make sense to move them up to sefaria.client or sefaria.helper
link_counts = {}
def get_link_counts(cat1, cat2):
    global link_counts
    key = cat1 + "-" + cat2
    if link_counts.get(key):
        return link_counts[key]

    queries = []
    for c in [cat1, cat2]:
        queries.append({"$and": [{"categories": c}, {"categories": {"$ne": "Commentary"}}, {"categories": {"$ne": "Commentary2"}}, {"categories": {"$ne": "Targum"}}]})

    titles = []
    for q in queries:
        ts = db.index.find(q).distinct("title")
        if len(ts) == 0:
            return {"error": "No results for {}".format(q)}
        titles.append(ts)

    result = []
    for title1 in titles[0]:
        for title2 in titles[1]:
            re1 = r"^{} \d".format(title1)
            re2 = r"^{} \d".format(title2)
            links = LinkSet({"$and": [{"refs": {"$regex": re1}}, {"refs": {"$regex": re2}}]})  # db.links.find({"$and": [{"refs": {"$regex": re1}}, {"refs": {"$regex": re2}}]})
            if links.count():
                result.append({"book1": title1.replace(" ","-"), "book2": title2.replace(" ", "-"), "count": links.count()})

    link_counts[key] = result
    return result


def get_book_category_linkset(book, cat):
    """
    Return LinkSet of links between the given book and category.
    :param book: String
    :param cat: String
    :return:
    """
    query = {"$and": [{"categories": cat}, {"categories": {"$ne": "Commentary"}}, {"categories": {"$ne": "Commentary2"}}, {"categories": {"$ne": "Targum"}}]}

    titles = text.IndexSet(query).distinct("title")
    if len(titles) == 0:
        return {"error": "No results for {}".format(query)}

    book_re = r'^{} \d'.format(book)
    cat_re = r'^({}) \d'.format('|'.join(titles))

    return LinkSet({"$and": [{"refs": {"$regex": book_re}}, {"refs": {"$regex": cat_re}}]})


def get_book_link_collection(book, cat):
    """
    Format results of get_book_category_linkset for front end use by the Explorer.
    :param book: String
    :param cat: String
    :return:
    """
    links = get_book_category_linkset(book, cat)

    link_re = r'^(?P<title>.+) (?P<loc>\d.*)$'
    ret = []

    for link in links:
        l1 = re.match(link_re, link.refs[0])
        l2 = re.match(link_re, link.refs[1])
        ret.append({
            "r1": {"title": l1.group("title").replace(" ", "-"), "loc": l1.group("loc")},
            "r2": {"title": l2.group("title").replace(" ", "-"), "loc": l2.group("loc")}
        })
    return ret