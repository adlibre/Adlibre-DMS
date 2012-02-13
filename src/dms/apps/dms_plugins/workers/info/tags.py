from taggit.models import Tag
from taggit.utils import parse_tags

from dms_plugins.models import Document
from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint, BeforeUpdatePluginPoint
from dms_plugins.workers import Plugin, PluginError

class TagsPlugin(Plugin, BeforeRetrievalPluginPoint):
    title = "Tags Retrieval"
    description = "Populates document tags"
    plugin_type = "info"

    def work(self, request, document, **kwargs):
        tags = []
        try:
            doc_model = Document.objects.get(name = document.get_filename())
            tags = doc_model.get_tag_list()
        except Document.DoesNotExist:
            pass
        document.set_tags(tags)
        return document

    def get_all_tags(self, doccode = None):
        tags = Tag.objects.all()
        if doccode:
            tags = tags.filter(taggit_taggeditem_items__document__doccode = doccode.get_id()).distinct()
        return tags

    def get_doc_models(self, doccode = None, tags = []):
        doc_models = Document.objects.all()
        if doccode:
            doc_models = doc_models.filter(doccode = doccode.get_id())
        if tags:
            doc_models = doc_models.filter(tags__name__in = tags)
        return doc_models

class TagsUpdatePlugin(Plugin, BeforeUpdatePluginPoint):
    title = "Tags Update"
    description = "Saves document tags in the database"
    plugin_type = "info"

    def work(self, request, document, **kwargs):
        tag_string = document.get_tag_string()
        tag_string = tag_string.strip()
        remove_tag_string = document.get_remove_tag_string()
        remove_tag_string = remove_tag_string.strip()
        doc_model, created = Document.objects.get_or_create(name = document.get_filename(),
                                                                doccode = document.get_docrule().get_id())
        if tag_string or remove_tag_string:
            if tag_string:
                tags = parse_tags(tag_string)
                doc_model.tags.add(*tags)
            else:
                doc_model.tags.remove(remove_tag_string)
            doc_model = Document.objects.get(pk = doc_model.pk)
        document.set_tags(doc_model.get_tag_list())
        return document

