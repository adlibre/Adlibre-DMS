import os

from django.http import HttpResponse
from django.views.generic.simple import direct_to_template
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, loader

from browser.forms import UploadForm

from base.dms import DmsBase, DmsRule, DmsDocument, DmsException


def handlerError(request, httpcode, message):
    t = loader.get_template(str(httpcode)+'_custom.html')
    context = RequestContext(
        request, {'request_path': request.path,
                  'message': message, }
        )
    response = HttpResponse(t.render(context))
    response.status_code = httpcode
    return response

# TODO : These should all have pagination
# TODO : These should use the WS API to browse the repository to reduce code duplication and to have pure separation.


# FIXME: Need to fix the @staff_required decorator to redirect to standard login form
# I don't think we want to necessarily use the django admin login.
@login_required
def upload(request, template_name='browser/upload.html', extra_context={}):
    """
    Upload file processing. Uploaded file will be check against available rules to
    determine storage, validator, and security plugins.
    """

    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            document = os.path.splitext(form.files['file'].name)[0]

            try:
                d = DmsDocument(document)
            except DmsException, (e):
                return handlerError(request, e.code, e.parameter)

            file_content = form.files['file']
            d.set_file(request, file_content, new_revision=True, append_content=False) # TODO: Add Exception check.
            messages.success(request, 'File has been uploaded.')

    extra_context['form'] = form
    return direct_to_template(request,
                              template_name,
                              extra_context=extra_context)


def get_file(request, document, hashcode=None, extension=None):

    revision = request.GET.get("r", None)
    request_extension = extension

    try:
        d = DmsDocument(document, revision)
    except DmsException, (e):
        return handlerError(request, e.code, e.parameter)

    try:
        content, filename, mimetype = d.get_file(request, hashcode, request_extension)
    except DmsException, (e):
        return handlerError(request, e.code, e.parameter)
    except Exception, (e):
        return handlerError(request, 500, e) # Generic Exception. All others should be caught above by DmsException
    else:
        response = HttpResponse(content, mimetype=mimetype)
        response["Content-Length"] = len(content)
        response['Content-Disposition'] = 'filename=%s' % filename
        return response


@staff_member_required
def revision_document(request, document):

    try:
        d = DmsDocument(document)
    except DmsException, (e):
        return handlerError(request, e.code, e.parameter)

    extra_context = {
        'fileinfo_db': d.get_meta_data(request),
        'document': document,
    }

    if d.get_hash():
        extra_context['hash'] = d.get_hash

    return direct_to_template(request, 'browser/revision.html',
        extra_context=extra_context)


@staff_member_required
def files_index(request):

    try:
        dms = DmsBase()
    except DmsException, (e):
        return handlerError(request, e.code, e.parameter)

    try:
        rules = dms.get_rules()
    except:
        return handlerError(request, 500, "No rules found")
    else:
        extra_context = {
            'rules': rules,
            }
    
        return direct_to_template(request, 'browser/files_index.html',
            extra_context=extra_context)


@staff_member_required
def files_document(request, id_rule):

    try:
        dms = DmsRule(id_rule)
    except DmsException, (e):
        return handlerError(request, e.code, e.parameter)

    rule_context = {
        'id': dms.rule.id,
        'name': dms.rule.get_doccode().name,
        }
    extra_context = {
        'document_list': dms.get_file_list(),
        'rule': rule_context,
        }

    return direct_to_template(request, 'browser/files.html',
        extra_context=extra_context)
