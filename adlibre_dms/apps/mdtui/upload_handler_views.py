import logging
from django.utils import simplejson
from django.http import HttpResponseServerError, HttpResponse

log = logging.getLogger('dms.mdtui.upload_handler_views')

def upload_progress(request):
    """
    Return JSON object with information about the progress of an upload.
    """
    log.debug('Touch to upload_progress view.')
    progress_id = ''
    if 'X-Progress-ID' in request.GET:
        progress_id = request.GET['X-Progress-ID']
    elif 'X-Progress-ID' in request.META:
        progress_id = request.META['X-Progress-ID']
    if progress_id:
        cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
        log.debug("request.session: %s" % [(key, value) for key,value  in request.session.iteritems()])
        try:
            data = request.session[cache_key]
            return HttpResponse(simplejson.dumps(data))
        except KeyError:
            return HttpResponseServerError('No such upload in this session.')
    else:
        return HttpResponseServerError('Server Error: You must provide X-Progress-ID header or query param.')