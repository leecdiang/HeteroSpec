"""Stable failed-evidence diagnostics across Windows extraction roots."""
import json
from pathlib import PurePosixPath, PureWindowsPath


def diagnostic(error, root):
    root=str(root)
    if isinstance(error,OSError):
        cls=PureWindowsPath if '\\' in root or PureWindowsPath(root).drive else PurePosixPath
        def filename(value):
            if value is None:return None
            p=cls(str(value))
            try:return '$EVIDENCE_ROOT/'+p.relative_to(cls(root)).as_posix()
            except ValueError:return p.as_posix()
        return json.dumps(dict(type=type(error).__name__,errno=error.errno,
            message=error.strerror,filename=filename(error.filename),
            filename2=filename(error.filename2)),sort_keys=True)
    return str(error).replace(root,'$EVIDENCE_ROOT')
