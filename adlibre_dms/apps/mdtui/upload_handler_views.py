import logging
import json
from django.core.cache import get_cache
from django.http import HttpResponseServerError, HttpResponse

log = logging.getLogger('dms.mdtui.upload_handler_views')


def upload_progress(request):
    """Return JSON object with information about the progress of an upload."""
    log.debug('Touch to upload_progress view.')
    cache = get_cache('default')
    progress_id = ''
    if 'X-Progress-ID' in request.GET:
        progress_id = request.GET['X-Progress-ID']
    elif 'X-Progress-ID' in request.META:
        progress_id = request.META['X-Progress-ID']
    if progress_id:
        cache_key = "%s" % progress_id
        data = cache.get(cache_key)
        log.debug("responded with cache_key: %s, data: %s" % (cache_key, data))
        return HttpResponse(json.dumps(data))
    else:
        return HttpResponseServerError('Server Error: You must provide X-Progress-ID header' )