from newplugins.transfer import TransferPluginPoint


class TestPlugin(TransferPluginPoint):
    title = 'Test Plugin'
    has_configuration = False
    methods = ( 'RETRIEVAL','STORAGE' ) # acts on the following: retrieval, storage

    @staticmethod
    def work(file_obj, method):

        import tempfile

        file_obj.seek(0)
        content = file_obj.read()
        tmp_file_obj = tempfile.TemporaryFile()

        tmp_file_obj.write('Test Plugin Says Hello: ' + content)

        return tmp_file_obj