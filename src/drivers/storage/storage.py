import os
import os.path
import shutil
from fastapi.responses import FileResponse
from drivers.storage.utils import secure_filename
from drivers.storage.errors import FileExists

class StorageDriver:
    def __init__(self, UPLOAD_DIR):
        self.name = "LOCAL DRIVER"
        self.upload_dir = UPLOAD_DIR
        
    def Exists(self, filename):
        """Checks if a file exists.

        Overridden by backends.
        """
        filename = secure_filename(filename)
        return os.path.exists(os.path.join(self.upload_dir, filename))

    async def WriteFile(self, filename, file, overwrite=False):
        """Write content to a file.

        :param str filename: The storage root-relative filename
        :param file: The file-like object to write in the file
        :param bool overwrite: Whether to allow overwrite or not
        :raises FileExists: If the file exists and `overwrite` is `False`

        Overridden by backends.
        """
        if not overwrite and self.Exists(filename):
            raise FileExists()
        filename = secure_filename(filename)
        fpath = os.path.join(self.upload_dir, filename)
        with open(fpath, "wb") as f:
            shutil.copyfileobj(file.file, f)

    def ReadFile(self, filename, db_name=None):
        """Reads a file from the local storage.

        Overridden by backends
        """
        filename = secure_filename(filename)
        fpath = os.path.join(self.upload_dir, filename)
        if not self.Exists(filename):
            raise FileNotFoundError(filename)
        res = FileResponse(fpath, filename=db_name)
        return res

    def DeleteFile(self, filename):
        """Deletes a given file in the local storage.

        Overridden by backends.
        """
        filename = secure_filename(filename)
        path = os.path.join(self.upload_dir, filename)
        if not self.Exists(filename):
            raise FileNotFoundError(path)
        os.remove(path)

    def ListFiles(self):
        """Lists all the files in the local storage.

        Overridden by backends.
        """
        return os.listdir(self.upload_dir)