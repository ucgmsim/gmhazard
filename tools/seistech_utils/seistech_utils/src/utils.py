from pathlib import Path
from typing import Tuple, Union, Sequence, List

def get_package_version(package_name: str) -> Tuple[str, str]:
    try:
        # Available for python version >= 3.8
        from importlib.metadata import version
    except ImportError:
        try:
            # Third party package
            # https://pypi.org/project/importlib-metadata/
            from importlib_metadata import version
        except ImportError:
            print(f"Please install the importlib-metadata package "
                  f"or switch to a python version >= 3.8")

    version_number = version(package_name)
    return version_number, f"v{version_number.replace('.', 'p')}"


def to_path(
    input: Union[str, Sequence[str], Sequence[Path]] = None
) -> Union[Path, List[Path]]:
    """Converts strings to Path objects"""
    if isinstance(input, str):
        return Path(input)
    elif isinstance(input, list):
        return [
            Path(cur_input) if isinstance(cur_input, str) else cur_input
            for cur_input in input
        ]


def change_file_ext(file_ffp: str, new_ext: str, excl_dot: bool = False):
    """Returns the full file path of the given file with the
    extension changed to new_ext

    If excl_dot is set, then a . is not added automatically
    """
    return os.path.join(
        os.path.dirname(file_ffp),
        os.path.splitext(os.path.basename(file_ffp))[0]
        + (f".{new_ext}" if not excl_dot else new_ext),
    )
